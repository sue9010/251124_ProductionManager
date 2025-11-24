import calendar
import tkinter as tk
from datetime import datetime, timedelta

import customtkinter as ctk
import pandas as pd


class CalendarView(ctk.CTkToplevel):
    def __init__(self, parent, dm):
        super().__init__(parent)
        self.dm = dm

        self.title("월간 출고 예정 달력")
        self.geometry("1200x800")
        self.attributes("-topmost", True)

        # 현재 연도와 월
        self.year = datetime.now().year
        self.month = datetime.now().month

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

        self.btn_prev = ctk.CTkButton(header_frame, text="< 이전 달 (여기에 드롭)", command=self.prev_month, hover_color="#D32F2F")
        self.btn_prev.pack(side="left")
        
        self.month_label = ctk.CTkLabel(header_frame, text="", font=("Malgun Gothic", 16, "bold"))
        self.month_label.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(header_frame, text="다음 달 (여기에 드롭) >", command=self.next_month, hover_color="#1976D2")
        self.btn_next.pack(side="right")

        # 메인 달력 프레임
        self.calendar_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.calendar_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def update_calendar(self):
        # 기존 위젯 삭제
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_label.configure(text=f"{self.year}년 {self.month}월")

        # 요일 헤더
        days = ["일", "월", "화", "수", "목", "금", "토"]
        for i, day in enumerate(days):
            text_color = "white"
            if i == 0: text_color = "#FF6B6B"
            elif i == 6: text_color = "#4D96FF"
            
            ctk.CTkLabel(self.calendar_frame, text=day, font=("Malgun Gothic", 12, "bold"), text_color=text_color).grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="days")

        # 데이터 로드
        df = self.dm.df
        events = {}
        if not df.empty and '출고예정일' in df.columns:
            df_filtered = df[df['출고예정일'].str.startswith(f"{self.year}-{str(self.month).zfill(2)}", na=False)].copy()
            df_filtered['day'] = pd.to_datetime(df_filtered['출고예정일']).dt.day
            events = {day: group.to_dict('records') for day, group in df_filtered.groupby('day')}

        # 달력 날짜 생성
        cal = calendar.Calendar(firstweekday=6).monthdayscalendar(self.year, self.month)
        
        for r, week in enumerate(cal):
            self.calendar_frame.grid_rowconfigure(r + 1, weight=1, uniform="weeks")
            
            for c, day in enumerate(week):
                cell_frame = ctk.CTkFrame(self.calendar_frame, border_width=1, border_color="#444444", fg_color="transparent")
                cell_frame.grid(row=r + 1, column=c, sticky="nsew")

                # 타겟 날짜 정보
                if day != 0:
                    target_date_str = f"{self.year}-{str(self.month).zfill(2)}-{str(day).zfill(2)}"
                    cell_frame.target_date = target_date_str
                else:
                    cell_frame.target_date = None

                if day == 0: continue
                
                # Cell 내부 레이아웃
                cell_frame.grid_rowconfigure(1, weight=1)
                cell_frame.grid_columnconfigure(0, weight=1)
                
                day_color = "white"
                if c == 0: day_color = "#FF6B6B"
                elif c == 6: day_color = "#4D96FF"
                
                # [수정] 날짜 라벨 여백 최소화 (pady=(3, 0) : 위쪽 3, 아래쪽 0)
                ctk.CTkLabel(cell_frame, text=str(day), font=("Malgun Gothic", 12), text_color=day_color).grid(row=0, column=0, sticky="nw", padx=5, pady=(3, 0))
                
                # 이벤트 표시
                if day in events:
                    # [수정] 스크롤 프레임 여백 최소화 (pady=(0, 2) : 위쪽 0, 아래쪽 2)
                    event_scroll_frame = ctk.CTkScrollableFrame(cell_frame, fg_color="transparent")
                    event_scroll_frame.grid(row=1, column=0, sticky='nsew', padx=1, pady=(0, 2))
                    
                    day_events = sorted(events[day], key=lambda x: str(x['업체명']))
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
                            # 헤더 위쪽 여백도 최소화 (pady=(2,0))
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
                        
                        # 이벤트 바인딩
                        item_label.bind("<Button-1>", lambda e, r=req_no, d=origin_date, t=item_text, w=item_label: self.start_drag(e, r, d, t, w))
                        item_label.bind("<B1-Motion>", self.do_drag)
                        item_label.bind("<ButtonRelease-1>", self.stop_drag)
                        
                        item_label.bind("<Enter>", lambda e, w=item_label: w.configure(text_color="#AAAAAA"))
                        item_label.bind("<Leave>", lambda e, w=item_label: w.configure(text_color="white"))

    # -------------------------------------------------------------------------
    # Drag & Drop Logic (기존과 동일)
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

        if target_date:
            new_date = target_date
        elif (is_next_btn or is_prev_btn) and self.drag_data["origin_date"]:
            try:
                origin_dt = datetime.strptime(self.drag_data["origin_date"], "%Y-%m-%d")
                year = origin_dt.year
                month = origin_dt.month
                day = origin_dt.day

                if is_next_btn:
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                elif is_prev_btn:
                    month -= 1
                    if month < 1:
                        month = 12
                        year -= 1
                
                last_day_of_new_month = calendar.monthrange(year, month)[1]
                if day > last_day_of_new_month:
                    day = last_day_of_new_month
                
                new_date = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
            except Exception as e:
                print(f"날짜 계산 오류: {e}")

        if new_date and self.drag_data["req_no"]:
            if self.dm.update_expected_date(self.drag_data["req_no"], new_date):
                if is_next_btn:
                    self.next_month()
                elif is_prev_btn:
                    self.prev_month()
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

    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.update_calendar()

    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.update_calendar()

    # -------------------------------------------------------------------------
    # [추가] 창 닫기 이벤트 핸들러
    # -------------------------------------------------------------------------
    def on_closing(self):
        """창이 닫힐 때 데이터를 새로고침하고 메인 UI를 업데이트합니다."""
        # 1. 엑셀 파일에서 데이터 다시 로드
        self.dm.load_data()
        
        # 2. 메인 윈도우(부모)의 UI 리프레시 호출
        if hasattr(self.master, "refresh_ui"):
            self.master.refresh_ui()
            
        # 3. 창 종료
        self.destroy()