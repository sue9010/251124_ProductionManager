import calendar
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd


class CalendarView(ctk.CTkToplevel):
    def __init__(self, parent, dm, popup_manager):
        super().__init__(parent)
        self.dm = dm
        self.popup_manager = popup_manager

        # =================================================================
        # [설정] 레이아웃 크기 설정
        # =================================================================
        self.layout_config = {
            "window_width": 1650,      # 1. 전체 창 너비
            "window_height": 850,      # 2. 전체 창 높이
            "sidebar_width": 450,      # 3. 사이드바(오른쪽 목록) 너비
            # ※ 달력 너비는 (전체 창 - 사이드바) 남은 공간을 자동으로 꽉 채웁니다.
        }
        # =================================================================

        self.title("생산 일정 달력")
        self.geometry(f"{self.layout_config['window_width']}x{self.layout_config['window_height']}")
        self.attributes("-topmost", True)

        self.base_date = datetime.now()

        self.drag_data = {
            "item": None,
            "req_no": None,
            "text": None,
            "window": None,
            "origin_date": None
        }
        
        self.click_timer = None
        self.drag_started = False
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.update_view()

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=10, padx=10, fill="x", side="top")

        self.btn_prev = ctk.CTkButton(header_frame, text="< 이전 4주 (여기에 드롭)", command=self.prev_weeks, hover_color="#D32F2F")
        self.btn_prev.pack(side="left")
        
        self.period_label = ctk.CTkLabel(header_frame, text="", font=("Malgun Gothic", 16, "bold"))
        self.period_label.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(header_frame, text="다음 4주 (여기에 드롭) >", command=self.next_weeks, hover_color="#1976D2")
        self.btn_next.pack(side="right")

        ctk.CTkButton(header_frame, text="🔄 새로고침", width=80, fg_color="#555555", hover_color="#333333", 
                      command=self.refresh_data).pack(side="right", padx=(0, 10))

        content_container = ctk.CTkFrame(self, fg_color="transparent")
        # [수정됨] padx=0 -> padx=5 (너무 붙지 않게 전체적으로 5px 여백 추가)
        content_container.pack(expand=True, fill="both", padx=5, pady=(0, 10))

        content_container.grid_columnconfigure(0, weight=1)
        sidebar_w = self.layout_config["sidebar_width"]
        content_container.grid_columnconfigure(1, weight=0, minsize=sidebar_w)
        content_container.grid_rowconfigure(0, weight=1)

        self.calendar_frame = ctk.CTkFrame(content_container, fg_color="#2b2b2b")
        # [수정됨] padx=(10, 0) -> padx=(0, 5) 
        # 왼쪽은 컨테이너 패딩(5px)이 있으므로 0, 오른쪽(사이드바와 사이)은 5px 간격 둠
        self.calendar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.sidebar_frame = ctk.CTkFrame(content_container, width=sidebar_w, fg_color="#2b2b2b")
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        ctk.CTkLabel(self.sidebar_frame, text="🛑 Hold 목록", font=("Malgun Gothic", 14, "bold"), text_color="#E04F5F").pack(pady=(15, 5), padx=10, anchor="w")
        
        # [수정됨] padx=0 -> padx=5 (목록 상자 좌우에 5px 여백을 주어 답답함 해소)
        self.hold_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, height=300, fg_color="#333333", corner_radius=0)
        self.hold_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        ctk.CTkLabel(self.sidebar_frame, text="⏳ 생산 대기 목록", font=("Malgun Gothic", 14, "bold"), text_color="#D35400").pack(pady=(10, 5), padx=10, anchor="w")
        
        # [수정됨] padx=0 -> padx=5
        self.waiting_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, height=300, fg_color="#333333", corner_radius=0)
        self.waiting_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 15))

    def refresh_data(self):
        self.dm.load_data()
        self.update_view()

    def update_view(self):
        self.update_calendar()
        self.update_sidebar()

    def update_sidebar(self):
        for widget in self.hold_scroll.winfo_children(): widget.destroy()
        for widget in self.waiting_scroll.winfo_children(): widget.destroy()

        df = self.dm.df
        if df.empty: return

        status_series = df['Status'].fillna('').astype(str).str.strip()

        hold_df = df[status_series == 'Hold'].copy()
        self._fill_sidebar_list(self.hold_scroll, hold_df)

        waiting_df = df[status_series == '대기'].copy()
        self._fill_sidebar_list(self.waiting_scroll, waiting_df)

    def _fill_sidebar_list(self, parent_frame, target_df):
        if target_df.empty:
            ctk.CTkLabel(parent_frame, text="데이터 없음", text_color="#777777", font=("Malgun Gothic", 12)).pack(pady=10)
            return

        target_df = target_df.sort_values(by=['업체명', '출고요청일'])
        last_company = None

        for _, row in target_df.iterrows():
            req_no = row.get("번호")
            curr_company = str(row.get('업체명', '-'))
            req_date = str(row.get('출고요청일', '-'))
            model = str(row.get('모델명', '-'))
            qty = str(row.get('수량', '0'))
            
            if curr_company != last_company:
                if last_company is not None:
                    ctk.CTkFrame(parent_frame, height=1, fg_color="#555555").pack(fill="x", pady=5)

                comp_header = ctk.CTkLabel(
                    parent_frame, 
                    text=f"🏢 {curr_company}", 
                    font=("Malgun Gothic", 13, "bold"), 
                    text_color="#3B8ED0", 
                    anchor="w"
                )
                comp_header.pack(fill="x", pady=(5, 2), padx=2)
                last_company = curr_company

            date_short = req_date[5:] if len(req_date) >= 10 else req_date
            item_text = f"  - [No.{req_no}] {model} ({qty}개)"
            
            item_label = ctk.CTkLabel(
                parent_frame,
                text=item_text,
                font=("Malgun Gothic", 12),
                anchor="w",
                text_color="#DDDDDD"
            )
            item_label.pack(fill="x", padx=(5, 0), pady=1)

            # Event bindings
            item_label.bind("<Double-1>", lambda e, r=req_no: self.handle_sidebar_double_click(r))
            item_label.bind("<Button-1>", lambda e, r=req_no, t=item_text, w=item_label: self.start_drag(e, r, None, t, w))
            item_label.bind("<B1-Motion>", lambda e, r=req_no: self.do_drag(e, r))
            item_label.bind("<ButtonRelease-1>", lambda e, r=req_no: self.stop_drag(e, r))
            item_label.bind("<Enter>", lambda e, w=item_label: w.configure(text_color="#AAAAAA"))
            item_label.bind("<Leave>", lambda e, w=item_label: w.configure(text_color="white"))

    def update_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        offset = (self.base_date.weekday() + 1) % 7
        start_date = self.base_date - timedelta(days=offset)
        
        calendar_days = [start_date + timedelta(days=i) for i in range(28)]
        end_date = calendar_days[-1]

        self.period_label.configure(text=f"{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}")

        days_header = ["일", "월", "화", "수", "목", "금", "토"]
        for i, day in enumerate(days_header):
            text_color = "white"
            if i == 0: text_color = "#FF6B6B" 
            elif i == 6: text_color = "#4D96FF" 
            ctk.CTkLabel(self.calendar_frame, text=day, font=("Malgun Gothic", 12, "bold"), text_color=text_color).grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

        for i in range(7): self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="days")

        df = self.dm.df
        events = {}
        if not df.empty and '출고예정일' in df.columns:
            s_date_str = start_date.strftime("%Y-%m-%d")
            e_date_str = end_date.strftime("%Y-%m-%d")
            status_series = df['Status'].fillna('').astype(str).str.strip()
            mask = (df['출고예정일'] >= s_date_str) & (df['출고예정일'] <= e_date_str) & (~status_series.isin(['Hold', '대기', '완료']))
            df_filtered = df.loc[mask].copy()
            if not df_filtered.empty:
                events = {date: group.to_dict('records') for date, group in df_filtered.groupby('출고예정일')}

        for i, current_day_date in enumerate(calendar_days):
            r, c = (i // 7) + 1, i % 7
            self.calendar_frame.grid_rowconfigure(r, weight=1, uniform="weeks")
            
            cell_frame = ctk.CTkFrame(self.calendar_frame, border_width=1, border_color="#444444", fg_color="transparent")
            cell_frame.grid(row=r, column=c, sticky="nsew")
            
            date_str = current_day_date.strftime("%Y-%m-%d")
            cell_frame.target_date = date_str 
            
            if date_str == datetime.now().strftime("%Y-%m-%d"):
                cell_frame.configure(fg_color="#333333", border_color="#2CC985", border_width=2)

            cell_frame.grid_rowconfigure(1, weight=1)
            cell_frame.grid_columnconfigure(0, weight=1)
            
            day_num = current_day_date.day
            day_color = "white"
            if c == 0: day_color = "#FF6B6B" 
            elif c == 6: day_color = "#4D96FF" 
            
            display_text = str(day_num)
            if day_num == 1 or i == 0: display_text = f"{current_day_date.month}/{current_day_date.day}"
            ctk.CTkLabel(cell_frame, text=display_text, font=("Malgun Gothic", 12), text_color=day_color).grid(row=0, column=0, sticky="nw", padx=5, pady=(3, 0))
            
            if date_str in events:
                event_scroll_frame = ctk.CTkScrollableFrame(cell_frame, fg_color="transparent")
                event_scroll_frame.grid(row=1, column=0, sticky='nsew', padx=1, pady=(0, 2))
                
                day_events = sorted(events[date_str], key=lambda x: str(x['업체명']))
                last_comp_name = None 

                for event in day_events:
                    req_no = event.get("번호")
                    origin_date = event.get("출고예정일")
                    current_comp_name = str(event['업체명'])
                    model_name = str(event['모델명'])
                    qty = event['수량']

                    if current_comp_name != last_comp_name:
                        display_comp_name = current_comp_name[:8] + ".." if len(current_comp_name) > 8 else current_comp_name
                        header_label = ctk.CTkLabel(event_scroll_frame, text=f"• {display_comp_name}", font=("Malgun Gothic", 11, "bold"), text_color="#3B8ED0", anchor="w", height=15)
                        header_label.pack(fill="x", pady=(2, 0), padx=2)
                        last_comp_name = current_comp_name

                    item_text = f"  - {model_name} ({qty})"
                    item_label = ctk.CTkLabel(event_scroll_frame, text=item_text, justify="left", font=("Malgun Gothic", 10), anchor="w", height=15, fg_color="transparent")
                    item_label.pack(fill="x", pady=0, padx=2)
                    
                    item_label.bind("<Button-1>", lambda e, r=req_no, d=origin_date, t=item_text, w=item_label: self.start_drag(e, r, d, t, w))
                    item_label.bind("<B1-Motion>", lambda e, r=req_no: self.do_drag(e, r))
                    item_label.bind("<ButtonRelease-1>", lambda e, r=req_no: self.stop_drag(e, r))
                    
                    item_label.bind("<Enter>", lambda e, w=item_label: w.configure(text_color="#AAAAAA"))
                    item_label.bind("<Leave>", lambda e, w=item_label: w.configure(text_color="white"))

    def handle_click(self, req_no):
        status = self.dm.get_status_by_req_no(req_no)
        if status == '생산중':
            self.popup_manager.open_complete_popup(req_no)
        elif status == '완료':
            self.popup_manager.open_completed_view_popup(req_no)

    def handle_sidebar_double_click(self, req_no):
        """사이드바 아이템 더블클릭 시 일정 수립 팝업을 엽니다."""
        self.popup_manager.open_schedule_popup(req_no)

    def _start_drag_window(self, text):
        self.drag_started = True
        if self.drag_data["window"] is None:
            self.drag_data["window"] = ctk.CTkToplevel(self)
            self.drag_data["window"].overrideredirect(True)
            self.drag_data["window"].attributes("-topmost", True)
            self.drag_data["window"].attributes("-alpha", 0.7)
            lbl = ctk.CTkLabel(self.drag_data["window"], text=text, fg_color="#333333", corner_radius=5, padx=5, pady=2)
            lbl.pack()
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+10}+{y+10}")

    def start_drag(self, event, req_no, origin_date, text, widget):
        self.drag_data.update({"item": widget, "req_no": req_no, "origin_date": origin_date, "text": text})
        self.drag_started = False
        if self.click_timer: self.after_cancel(self.click_timer)
        self.click_timer = self.after(200, lambda: self._start_drag_window(text))

    def do_drag(self, event, req_no):
        if self.drag_started and self.drag_data["window"]:
            x, y = self.winfo_pointerxy()
            self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def stop_drag(self, event, req_no):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None

        if self.drag_started:
            if self.drag_data["window"]:
                self.drag_data["window"].destroy()
            
            x, y = self.winfo_pointerxy()
            target_widget = self.winfo_containing(x, y)

            # Check for drop targets
            target_date = self.find_target_date(target_widget)
            is_next_btn = self._is_widget_or_child(target_widget, self.btn_next)
            is_prev_btn = self._is_widget_or_child(target_widget, self.btn_prev)
            is_hold_list = self._is_in_hold_list(target_widget)
            is_waiting_list = self._is_in_waiting_list(target_widget)
            
            req_no = self.drag_data["req_no"]
            origin_date = self.drag_data["origin_date"]

            # Case 1: Drag from Sidebar to Calendar
            if origin_date is None:
                if target_date and req_no:
                    success, msg = self.dm.update_production_schedule(req_no, target_date)
                    if success: self.update_view()
                    else: messagebox.showerror("이동 실패", msg, parent=self)
            
            # Case 2: Drag from Calendar
            else:
                # 2a: Drop on Hold List
                if is_hold_list and req_no:
                    success, msg = self.dm.update_status_to_hold(req_no)
                    if success: self.update_view()
                    else: messagebox.showerror("Hold 이동 실패", msg, parent=self)
                
                # 2b: Drop on Waiting List
                elif is_waiting_list and req_no:
                    success, msg = self.dm.update_status_to_waiting(req_no) # reason is optional
                    if success: self.update_view()
                    else: messagebox.showerror("대기 이동 실패", msg, parent=self)

                # 2c: Drop on another Date or Buttons
                else:
                    new_date = None
                    if target_date:
                        new_date = target_date
                    elif (is_next_btn or is_prev_btn):
                        try:
                            origin_dt = datetime.strptime(origin_date, "%Y-%m-%d")
                            delta = timedelta(weeks=4)
                            new_dt = origin_dt + delta if is_next_btn else origin_dt - delta
                            new_date = new_dt.strftime("%Y-%m-%d")
                        except Exception as e: print(f"날짜 계산 오류: {e}")

                    if new_date and req_no:
                        success, msg = self.dm.update_expected_date(req_no, new_date)
                        if success:
                            if is_next_btn: self.next_weeks()
                            elif is_prev_btn: self.prev_weeks()
                            else: self.update_view()
                        else:
                            messagebox.showerror("이동 실패", msg, parent=self)
        else: # It's a click
            # Sidebar items have origin_date = None, so this prevents click action on them
            if self.drag_data.get("origin_date") is not None:
                self.handle_click(req_no)
            
        self.drag_data = {"item": None, "req_no": None, "origin_date": None, "text": None, "window": None}
        self.drag_started = False

    def _is_in_hold_list(self, widget):
        current = widget
        while current:
            if current == self.hold_scroll: return True
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return False

    def _is_in_waiting_list(self, widget):
        current = widget
        while current:
            if current == self.waiting_scroll: return True
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return False

    def _is_widget_or_child(self, target, parent_btn):
        if target is None: return False
        current = target
        while current:
            if current == parent_btn: return True
            try:
                current = current.master
            except:
                return False
        return False

    def find_target_date(self, widget):
        current = widget
        while current:
            if hasattr(current, "target_date"):
                return current.target_date
            try:
                current = current.master
                if current == self or current is None: break
            except:
                break
        return None



    def prev_weeks(self):
        self.base_date -= timedelta(weeks=4)
        self.update_view()

    def next_weeks(self):
        self.base_date += timedelta(weeks=4)
        self.update_view()

    def on_closing(self):
        self.dm.load_data()
        if hasattr(self.master, "refresh_ui"):
            self.master.refresh_ui()
        self.destroy()