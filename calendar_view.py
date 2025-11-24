import calendar
import tkinter as tk
from datetime import datetime, timedelta

import customtkinter as ctk
import pandas as pd


class CalendarView(ctk.CTkToplevel):
    def __init__(self, parent, dm):
        super().__init__(parent)
        self.dm = dm

        self.title("생산 일정 달력 (4주)")
        self.geometry("1200x800")
        self.attributes("-topmost", True)

        # [변경] 기준 날짜 (초기값: 오늘)
        self.base_date = datetime.now()

        # [Drag & Drop 상태 변수]
        self.drag_data = {
            "item": None,      # 드래그 중인 위젯
            "req_no": None,    # 드래그 중인 데이터의 번호
            "text": None,      # 드래그 텍스트
            "window": None,    # 잔상 윈도우
            "origin_date": None # 원래 날짜
        }
        
        # [이벤트 바인딩] 창 닫기 버튼(X) 클릭 시 처리
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.update_calendar()

    def create_widgets(self):
        # 헤더 프레임 (네비게이션)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=10, padx=10, fill="x")

        # [변경] 버튼 텍스트 및 커맨드 (4주 단위 이동)
        self.btn_prev = ctk.CTkButton(header_frame, text="< 이전 4주 (여기에 드롭)", command=self.prev_weeks, hover_color="#D32F2F")
        self.btn_prev.pack(side="left")
        
        self.period_label = ctk.CTkLabel(header_frame, text="", font=("Malgun Gothic", 16, "bold"))
        self.period_label.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(header_frame, text="다음 4주 (여기에 드롭) >", command=self.next_weeks, hover_color="#1976D2")
        self.btn_next.pack(side="right")

        # 메인 달력 프레임
        self.calendar_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.calendar_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def update_calendar(self):
        # 기존 위젯 삭제
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # 1. 표시할 4주 날짜 범위 계산
        # 기준 날짜가 속한 주의 일요일 구하기 (Python: 월=0 ... 일=6)
        # 일요일을 시작으로 하려면: (weekday + 1) % 7 만큼 빼면 됨
        offset = (self.base_date.weekday() + 1) % 7
        start_date = self.base_date - timedelta(days=offset)
        
        # 4주치 날짜 리스트 생성 (28일)
        calendar_days = []
        for i in range(28):
            day_date = start_date + timedelta(days=i)
            calendar_days.append(day_date)

        end_date = calendar_days[-1]

        # 상단 라벨 업데이트 (기간 표시)
        start_str = start_date.strftime("%Y.%m.%d")
        end_str = end_date.strftime("%Y.%m.%d")
        self.period_label.configure(text=f"{start_str} ~ {end_str}")

        # 2. 요일 헤더 그리기
        days_header = ["일", "월", "화", "수", "목", "금", "토"]
        for i, day in enumerate(days_header):
            text_color = "white"
            if i == 0: text_color = "#FF6B6B" # 일요일
            elif i == 6: text_color = "#4D96FF" # 토요일
            
            ctk.CTkLabel(self.calendar_frame, text=day, font=("Malgun Gothic", 12, "bold"), text_color=text_color).grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="days")

        # 3. 데이터 로드 및 필터링
        df = self.dm.df
        events = {}
        if not df.empty and '출고예정일' in df.columns:
            # 문자열 날짜 비교를 위해 범위 설정
            s_date_str = start_date.strftime("%Y-%m-%d")
            e_date_str = end_date.strftime("%Y-%m-%d")
            
            # 범위 내 데이터 필터링
            mask = (df['출고예정일'] >= s_date_str) & (df['출고예정일'] <= e_date_str)
            df_filtered = df.loc[mask].copy()
            
            # 날짜별 그룹화
            if not df_filtered.empty:
                events = {date: group.to_dict('records') for date, group in df_filtered.groupby('출고예정일')}

        # 4. 달력 그리드 생성 (4행 7열)
        for i, current_day_date in enumerate(calendar_days):
            r = (i // 7) + 1 # 헤더가 0번 로우이므로 +1
            c = i % 7
            
            self.calendar_frame.grid_rowconfigure(r, weight=1, uniform="weeks")
            
            # 셀 프레임
            cell_frame = ctk.CTkFrame(self.calendar_frame, border_width=1, border_color="#444444", fg_color="transparent")
            cell_frame.grid(row=r, column=c, sticky="nsew")
            
            date_str = current_day_date.strftime("%Y-%m-%d")
            cell_frame.target_date = date_str # 드롭 타겟용 날짜 저장
            
            # 오늘 날짜 강조
            is_today = (date_str == datetime.now().strftime("%Y-%m-%d"))
            if is_today:
                cell_frame.configure(fg_color="#333333", border_color="#2CC985", border_width=2)

            # 내부 레이아웃
            cell_frame.grid_rowconfigure(1, weight=1)
            cell_frame.grid_columnconfigure(0, weight=1)
            
            # 날짜 숫자 표시
            day_num = current_day_date.day
            day_color = "white"
            if c == 0: day_color = "#FF6B6B" # 일
            elif c == 6: day_color = "#4D96FF" # 토
            
            # 월이 바뀌는 경우 날짜 옆에 (M월) 표시해주면 좋음
            display_text = str(day_num)
            if day_num == 1 or i == 0: # 1일이거나 달력의 시작일인 경우
                display_text = f"{current_day_date.month}/{current_day_date.day}"

            ctk.CTkLabel(cell_frame, text=display_text, font=("Malgun Gothic", 12), text_color=day_color).grid(row=0, column=0, sticky="nw", padx=5, pady=(3, 0))
            
            # 이벤트 표시
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

                    # 업체명 헤더
                    if current_comp_name != last_comp_name:
                        display_comp_name = current_comp_name
                        if len(display_comp_name) > 8: display_comp_name = display_comp_name[:8] + ".."
                        
                        header_label = ctk.CTkLabel(
                            event_scroll_frame,
                            text=f"• {display_comp_name}",
                            font=("Malgun Gothic", 11, "bold"),
                            text_color="#3B8ED0",
                            anchor="w",
                            height=15
                        )
                        header_label.pack(fill="x", pady=(2, 0), padx=2)
                        last_comp_name = current_comp_name

                    item_text = f"  - {model_name} ({qty})"
                    item_label = ctk.CTkLabel(
                        event_scroll_frame, 
                        text=item_text, 
                        justify="left", 
                        font=("Malgun Gothic", 10), 
                        anchor="w",
                        height=15,
                        fg_color="transparent"
                    )
                    item_label.pack(fill="x", pady=0, padx=2)
                    
                    # 이벤트 바인딩 (Drag & Drop)
                    item_label.bind("<Button-1>", lambda e, r=req_no, d=origin_date, t=item_text, w=item_label: self.start_drag(e, r, d, t, w))
                    item_label.bind("<B1-Motion>", self.do_drag)
                    item_label.bind("<ButtonRelease-1>", self.stop_drag)
                    
                    item_label.bind("<Enter>", lambda e, w=item_label: w.configure(text_color="#AAAAAA"))
                    item_label.bind("<Leave>", lambda e, w=item_label: w.configure(text_color="white"))

    # -------------------------------------------------------------------------
    # Drag & Drop Logic (수정: 버튼 드롭 시 4주 단위 이동)
    # -------------------------------------------------------------------------
    def start_drag(self, event, req_no, origin_date, text, widget):
        self.drag_data["item"] = widget
        self.drag_data["req_no"] = req_no
        self.drag_data["origin_date"] = origin_date
        self.drag_data["text"] = text
        
        self.drag_data["window"] = ctk.CTkToplevel(self)
        self.drag_data["window"].overrideredirect(True)
        self.drag_data["window"].attributes("-topmost", True)
        self.drag_data["window"].attributes("-alpha", 0.7)
        
        lbl = ctk.CTkLabel(self.drag_data["window"], text=text, fg_color="#333333", corner_radius=5, padx=5, pady=2)
        lbl.pack()
        
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+10}+{y+10}")

    def do_drag(self, event):
        if self.drag_data["window"]:
            x, y = self.winfo_pointerxy()
            self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def stop_drag(self, event):
        if self.drag_data["window"]:
            self.drag_data["window"].destroy()
            self.drag_data["window"] = None

        x, y = self.winfo_pointerxy()
        target_widget = self.winfo_containing(x, y)

        target_date = self.find_target_date(target_widget)
        is_next_btn = self._is_widget_or_child(target_widget, self.btn_next)
        is_prev_btn = self._is_widget_or_child(target_widget, self.btn_prev)

        new_date = None

        # 1. 특정 날짜 칸에 드롭한 경우
        if target_date:
            new_date = target_date
        
        # 2. '이전/다음 4주' 버튼에 드롭한 경우
        elif (is_next_btn or is_prev_btn) and self.drag_data["origin_date"]:
            try:
                origin_dt = datetime.strptime(self.drag_data["origin_date"], "%Y-%m-%d")
                
                # [수정] 4주(28일) 더하기/빼기
                if is_next_btn:
                    new_dt = origin_dt + timedelta(weeks=4)
                elif is_prev_btn:
                    new_dt = origin_dt - timedelta(weeks=4)
                
                new_date = new_dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"날짜 계산 오류: {e}")

        # 날짜 업데이트 실행
        if new_date and self.drag_data["req_no"]:
            if self.dm.update_expected_date(self.drag_data["req_no"], new_date):
                # 뷰 갱신: 버튼에 드롭했다면 해당 기간으로 이동, 아니면 현재 뷰 갱신
                if is_next_btn:
                    self.next_weeks()
                elif is_prev_btn:
                    self.prev_weeks()
                else:
                    self.update_calendar()

        self.drag_data = {"item": None, "req_no": None, "origin_date": None, "text": None, "window": None}

    def _is_widget_or_child(self, target, parent_btn):
        if target is None: return False
        if target == parent_btn: return True
        try:
            if target.master == parent_btn: return True
        except:
            pass
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

    # [변경] 4주 이동 함수
    def prev_weeks(self):
        self.base_date -= timedelta(weeks=4)
        self.update_calendar()

    def next_weeks(self):
        self.base_date += timedelta(weeks=4)
        self.update_calendar()

    def on_closing(self):
        self.dm.load_data()
        if hasattr(self.master, "refresh_ui"):
            self.master.refresh_ui()
        self.destroy()
