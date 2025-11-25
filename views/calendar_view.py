import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from styles import COLORS, FONTS


class CalendarView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        # 팝업(Toplevel)이 아닌 프레임(Frame)으로 초기화
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.base_date = datetime.now()

        # 드래그 앤 드롭 관련 상태 변수
        self.drag_data = {
            "item": None,
            "req_no": None,
            "text": None,
            "window": None,
            "origin_date": None
        }
        
        self.click_timer = None
        self.drag_started = False

        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # ===================================================
        # 1. 상단 헤더 (이전/다음 버튼, 기간 표시)
        # ===================================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(0, 10), padx=10, fill="x", side="top")

        self.btn_prev = ctk.CTkButton(
            header_frame, text="< 이전 4주", 
            command=self.prev_weeks, 
            fg_color=COLORS["bg_medium"], hover_color=COLORS["danger_hover"],
            width=100, height=32
        )
        self.btn_prev.pack(side="left")
        
        self.period_label = ctk.CTkLabel(header_frame, text="", font=FONTS["title"], text_color=COLORS["text"])
        self.period_label.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(
            header_frame, text="다음 4주 >", 
            command=self.next_weeks, 
            fg_color=COLORS["bg_medium"], hover_color=COLORS["primary_hover"],
            width=100, height=32
        )
        self.btn_next.pack(side="right")

        ctk.CTkButton(
            header_frame, text="🔄 새로고침", width=80, height=32,
            fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
            command=self.refresh_data
        ).pack(side="right", padx=(0, 10))

        # ===================================================
        # 2. 메인 컨텐츠 (달력 영역 + 우측 사이드바)
        # ===================================================
        content_container = ctk.CTkFrame(self, fg_color="transparent")
        content_container.pack(expand=True, fill="both", padx=5, pady=(0, 10))

        # Grid 레이아웃: 달력(가변) : 사이드바(고정)
        content_container.grid_columnconfigure(0, weight=1) 
        content_container.grid_columnconfigure(1, weight=0, minsize=320) 
        content_container.grid_rowconfigure(0, weight=1)

        # [Left] 달력 프레임
        self.calendar_frame = ctk.CTkFrame(content_container, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.calendar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # [Right] 사이드바 프레임
        self.sidebar_frame = ctk.CTkFrame(content_container, width=320, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        # -- 사이드바 내용물 구성 --
        # 1) 작업 중지 목록
        ctk.CTkLabel(
            self.sidebar_frame, text="⛔ 작업 중지 목록", 
            font=FONTS["header"], text_color=COLORS["danger"]
        ).pack(pady=(15, 5), padx=15, anchor="w")
        
        self.hold_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, height=250, fg_color=COLORS["bg_medium"], corner_radius=6)
        self.hold_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 2) 생산 대기 목록
        ctk.CTkLabel(
            self.sidebar_frame, text="⏳ 생산 대기 목록", 
            font=FONTS["header"], text_color=COLORS["warning"]
        ).pack(pady=(10, 5), padx=15, anchor="w")
        
        self.waiting_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, height=250, fg_color=COLORS["bg_medium"], corner_radius=6)
        self.waiting_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

    def refresh_data(self):
        # 필요 시 부모나 DM을 통해 데이터 리로드 호출 가능
        # self.dm.load_data()
        self.update_view()

    def update_view(self):
        self.update_calendar()
        self.update_sidebar()

    # ===================================================
    # [Sidebar] 사이드바 목록 업데이트 로직
    # ===================================================
    def update_sidebar(self):
        for widget in self.hold_scroll.winfo_children(): widget.destroy()
        for widget in self.waiting_scroll.winfo_children(): widget.destroy()

        df = self.dm.df
        if df.empty: return

        status_series = df['Status'].fillna('').astype(str).str.strip()

        # Hold / 작업 중지 목록
        hold_df = df[status_series.isin(['Hold', '작업 중지', '중지'])].copy()
        self._fill_sidebar_list(self.hold_scroll, hold_df)

        # 대기 목록
        waiting_df = df[status_series == '대기'].copy()
        self._fill_sidebar_list(self.waiting_scroll, waiting_df)

    def _fill_sidebar_list(self, parent_frame, target_df):
        if target_df.empty:
            ctk.CTkLabel(parent_frame, text="데이터 없음", text_color=COLORS["text_dim"], font=FONTS["small"]).pack(pady=10)
            return

        target_df = target_df.sort_values(by=['업체명', '출고요청일'])
        last_company = None

        for _, row in target_df.iterrows():
            req_no = row.get("번호")
            curr_company = str(row.get('업체명', '-'))
            model = str(row.get('모델명', '-'))
            qty = str(row.get('수량', '0'))
            
            # 업체명 헤더 (중복 제거)
            if curr_company != last_company:
                if last_company is not None:
                    ctk.CTkFrame(parent_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=5)

                ctk.CTkLabel(
                    parent_frame, 
                    text=f"🏢 {curr_company}", 
                    font=("Malgun Gothic", 12, "bold"), 
                    text_color=COLORS["primary"], 
                    anchor="w"
                ).pack(fill="x", pady=(5, 2), padx=2)
                last_company = curr_company

            item_text = f"[{req_no}] {model} ({qty}개)"
            
            item_label = ctk.CTkLabel(
                parent_frame,
                text=item_text,
                font=FONTS["small"],
                anchor="w",
                text_color=COLORS["text"]
            )
            item_label.pack(fill="x", padx=(10, 0), pady=1)

            # 이벤트 바인딩 (드래그 앤 드롭 & 더블클릭)
            self._bind_item_events(item_label, req_no, None, item_text, is_header=False)

    # ===================================================
    # [Calendar] 달력 그리드 업데이트 로직
    # ===================================================
    def update_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # 4주 날짜 계산
        offset = (self.base_date.weekday() + 1) % 7
        start_date = self.base_date - timedelta(days=offset)
        calendar_days = [start_date + timedelta(days=i) for i in range(28)]
        end_date = calendar_days[-1]

        self.period_label.configure(text=f"{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}")

        # 요일 헤더 그리기
        days_header = ["일", "월", "화", "수", "목", "금", "토"]
        for i, day in enumerate(days_header):
            text_color = COLORS["text"]
            if i == 0: text_color = COLORS["danger"] 
            elif i == 6: text_color = COLORS["primary"] 
            ctk.CTkLabel(self.calendar_frame, text=day, font=FONTS["main_bold"], text_color=text_color).grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

        for i in range(7): self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="days")

        # 데이터 필터링 (기간 내 + 생산중인 항목)
        df = self.dm.df
        events = {}
        if not df.empty and '출고예정일' in df.columns:
            s_date_str = start_date.strftime("%Y-%m-%d")
            e_date_str = end_date.strftime("%Y-%m-%d")
            status_series = df['Status'].fillna('').astype(str).str.strip()
            # 달력에는 확정된(생산중인) 일정만 표시 (대기, 중지 제외)
            mask = (df['출고예정일'] >= s_date_str) & (df['출고예정일'] <= e_date_str) & (~status_series.isin(['Hold', '작업 중지', '중지', '대기', '완료']))
            df_filtered = df.loc[mask].copy()
            if not df_filtered.empty:
                events = {date: group.to_dict('records') for date, group in df_filtered.groupby('출고예정일')}

        # 날짜 셀 그리기
        for i, current_day_date in enumerate(calendar_days):
            r, c = (i // 7) + 1, i % 7
            self.calendar_frame.grid_rowconfigure(r, weight=1, uniform="weeks")
            
            cell_frame = ctk.CTkFrame(self.calendar_frame, border_width=1, border_color=COLORS["border"], fg_color="transparent")
            cell_frame.grid(row=r, column=c, sticky="nsew")
            
            date_str = current_day_date.strftime("%Y-%m-%d")
            cell_frame.target_date = date_str 
            
            # 오늘 날짜 강조
            if date_str == datetime.now().strftime("%Y-%m-%d"):
                cell_frame.configure(fg_color=COLORS["bg_medium"], border_color=COLORS["success"], border_width=2)

            cell_frame.grid_rowconfigure(1, weight=1)
            cell_frame.grid_columnconfigure(0, weight=1)
            
            day_num = current_day_date.day
            day_color = COLORS["text"]
            if c == 0: day_color = COLORS["danger"] 
            elif c == 6: day_color = COLORS["primary"] 
            
            display_text = str(day_num)
            if day_num == 1 or i == 0: display_text = f"{current_day_date.month}/{current_day_date.day}"
            
            # 날짜 숫자 라벨
            ctk.CTkLabel(cell_frame, text=display_text, font=FONTS["small"], text_color=day_color).grid(row=0, column=0, sticky="nw", padx=5, pady=(2, 0))
            
            # 이벤트 목록 표시
            if date_str in events:
                event_scroll_frame = ctk.CTkScrollableFrame(cell_frame, fg_color="transparent")
                event_scroll_frame.grid(row=1, column=0, sticky='nsew', padx=1, pady=(0, 2))
                event_scroll_frame._scrollbar.grid_forget() 
                
                day_records = events[date_str]
                
                # [수정] 요청 번호(req_no)로 그룹화
                grouped_events = {}
                for rec in day_records:
                    r_no = rec.get("번호")
                    if r_no not in grouped_events:
                        grouped_events[r_no] = []
                    grouped_events[r_no].append(rec)
                
                # 업체명 기준으로 정렬
                sorted_req_nos = sorted(grouped_events.keys(), key=lambda r: str(grouped_events[r][0]['업체명']))
                
                for r_no in sorted_req_nos:
                    group = grouped_events[r_no]
                    first_item = group[0]
                    comp_name = str(first_item['업체명'])
                    origin_date = first_item.get("출고예정일")
                    
                    # 1. 헤더: [업체명] (번호는 툴팁이나 드래그 시 표시)
                    header_text = f"• [{comp_name}]"
                    
                    header_label = ctk.CTkLabel(
                        event_scroll_frame, text=header_text, 
                        font=("Malgun Gothic", 10, "bold"), anchor="w", height=14,
                        text_color=COLORS["primary"], fg_color="transparent"
                    )
                    header_label.pack(fill="x", pady=(2, 0), padx=1)
                    
                    # 헤더 이벤트 바인딩
                    drag_text_header = f"[{r_no}] {comp_name} ({len(group)} items)"
                    self._bind_item_events(header_label, r_no, origin_date, drag_text_header, is_header=True)
                    
                    # 2. 아이템 목록: - 모델명 (수량)
                    for item in group:
                        model_name = str(item['모델명'])
                        qty = item['수량']
                        item_text = f"   - {model_name} ({qty})"
                        
                        item_label = ctk.CTkLabel(
                            event_scroll_frame, text=item_text, 
                            font=("Malgun Gothic", 9), anchor="w", height=12,
                            text_color=COLORS["text"], fg_color="transparent"
                        )
                        item_label.pack(fill="x", pady=0, padx=1)
                        
                        # 아이템 이벤트 바인딩
                        drag_text_item = f"[{r_no}] {comp_name} - {model_name}"
                        self._bind_item_events(item_label, r_no, origin_date, drag_text_item, is_header=False)

    def _bind_item_events(self, widget, req_no, origin_date, drag_text, is_header):
        """이벤트 바인딩 헬퍼 함수"""
        widget.bind("<Button-1>", lambda e, r=req_no, d=origin_date, t=drag_text, w=widget: self.start_drag(e, r, d, t, w))
        widget.bind("<B1-Motion>", lambda e, r=req_no: self.do_drag(e, r))
        widget.bind("<ButtonRelease-1>", lambda e, r=req_no: self.stop_drag(e, r))
        widget.bind("<Double-1>", lambda e, r=req_no: self.pm.open_complete_popup(r))
        
        # 호버 효과 설정
        default_color = COLORS["primary"] if is_header else COLORS["text"]
        hover_color = COLORS["primary_hover"] if is_header else COLORS["text_dim"]
        
        widget.bind("<Enter>", lambda e, w=widget, c=hover_color: w.configure(text_color=c))
        widget.bind("<Leave>", lambda e, w=widget, c=default_color: w.configure(text_color=c))

    # ===================================================
    # [Drag & Drop] 드래그 앤 드롭 로직
    # ===================================================
    def _start_drag_window(self, text):
        self.drag_started = True
        if self.drag_data["window"] is None:
            # 드래그 중 따라다니는 반투명 윈도우 생성
            self.drag_data["window"] = ctk.CTkToplevel(self)
            self.drag_data["window"].overrideredirect(True)
            self.drag_data["window"].attributes("-topmost", True)
            self.drag_data["window"].attributes("-alpha", 0.7)
            
            lbl = ctk.CTkLabel(
                self.drag_data["window"], text=text, 
                fg_color=COLORS["bg_dark"], text_color=COLORS["text"],
                corner_radius=5, padx=8, pady=4
            )
            lbl.pack()
            
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def start_drag(self, event, req_no, origin_date, text, widget):
        # 드래그 시작 준비 (클릭 후 일정 시간/거리 이동 시 시작)
        self.drag_data.update({
            "item": widget, 
            "req_no": req_no, 
            "origin_date": origin_date, 
            "text": text
        })
        self.drag_started = False
        
        if self.click_timer: self.after_cancel(self.click_timer)
        # 200ms 이상 누르고 있으면 드래그 시작으로 간주
        self.click_timer = self.after(200, lambda: self._start_drag_window(text))

    def do_drag(self, event, req_no):
        # 마우스 이동 시 윈도우 따라가기
        if self.drag_started and self.drag_data["window"]:
            x, y = self.winfo_pointerxy()
            self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def stop_drag(self, event, req_no):
        # 드래그 종료 (클릭 해제)
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None

        if self.drag_started:
            # 드래그 윈도우 제거
            if self.drag_data["window"]:
                self.drag_data["window"].destroy()
                self.drag_data["window"] = None
            
            # 드롭된 위치 확인
            x, y = self.winfo_pointerxy()
            target_widget = self.winfo_containing(x, y)

            # 타겟 식별
            target_date = self.find_target_date(target_widget)
            is_next_btn = self._is_widget_or_child(target_widget, self.btn_next)
            is_prev_btn = self._is_widget_or_child(target_widget, self.btn_prev)
            is_hold_list = self._is_in_hold_list(target_widget)
            is_waiting_list = self._is_in_waiting_list(target_widget)
            
            req_no = self.drag_data["req_no"]
            origin_date = self.drag_data["origin_date"]

            # [로직 1] 사이드바(미정) -> 달력(확정) 이동
            if origin_date is None: 
                if target_date and req_no:
                    success, msg = self.dm.update_production_schedule(req_no, target_date)
                    if success: self.update_view()
                    else: messagebox.showerror("이동 실패", msg)
            
            # [로직 2] 달력(확정) -> 어딘가로 이동
            else: 
                if is_hold_list and req_no:
                    # Hold로 이동
                    success, msg = self.dm.update_status_to_hold(req_no)
                    if success: self.update_view()
                
                elif is_waiting_list and req_no:
                    # 대기로 이동
                    success, msg = self.dm.update_status_to_waiting(req_no)
                    if success: self.update_view()
                
                else:
                    # 날짜 변경 또는 페이지 넘김
                    new_date = None
                    if target_date:
                        new_date = target_date
                    elif (is_next_btn or is_prev_btn):
                        try:
                            origin_dt = datetime.strptime(origin_date, "%Y-%m-%d")
                            delta = timedelta(weeks=4)
                            new_dt = origin_dt + delta if is_next_btn else origin_dt - delta
                            new_date = new_dt.strftime("%Y-%m-%d")
                        except: pass

                    if new_date and req_no and new_date != origin_date:
                        success, msg = self.dm.update_expected_date(req_no, new_date)
                        if success:
                            if is_next_btn: self.next_weeks()
                            elif is_prev_btn: self.prev_weeks()
                            else: self.update_view()
        else:
            # 단순 클릭인 경우 (드래그 안 함)
            # 기존에는 캘린더에서 클릭하면 팝업을 띄웠음
            if self.drag_data.get("origin_date") is not None:
                # (옵션) 클릭 시 동작이 필요하면 여기서 처리
                pass
            
        # 상태 초기화
        self.drag_data = {"item": None, "req_no": None, "origin_date": None, "text": None, "window": None}
        self.drag_started = False

    # ===================================================
    # [Helpers] 유틸리티 함수들
    # ===================================================
    def _is_in_hold_list(self, widget):
        current = widget
        while current:
            if current == self.hold_scroll: return True
            try: current = current.master
            except: break
        return False

    def _is_in_waiting_list(self, widget):
        current = widget
        while current:
            if current == self.waiting_scroll: return True
            try: current = current.master
            except: break
        return False

    def _is_widget_or_child(self, target, parent_btn):
        if target is None: return False
        current = target
        while current:
            if current == parent_btn: return True
            try: current = current.master
            except: return False
        return False

    def find_target_date(self, widget):
        current = widget
        while current:
            if hasattr(current, "target_date"):
                return current.target_date
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return None

    def prev_weeks(self):
        self.base_date -= timedelta(weeks=4)
        self.update_view()

    def next_weeks(self):
        self.base_date += timedelta(weeks=4)
        self.update_view()