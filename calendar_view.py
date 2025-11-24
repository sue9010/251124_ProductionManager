import calendar
from datetime import datetime

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

        self.create_widgets()
        self.update_calendar()

    def create_widgets(self):
        # 헤더 프레임 (네비게이션)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(header_frame, text="< 이전 달", command=self.prev_month).pack(side="left")
        self.month_label = ctk.CTkLabel(header_frame, text="", font=("Malgun Gothic", 16, "bold"))
        self.month_label.pack(side="left", expand=True)
        ctk.CTkButton(header_frame, text="다음 달 >", command=self.next_month).pack(side="right")

        # 메인 달력 프레임
        self.calendar_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.calendar_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def update_calendar(self):
        # 기존 위젯 삭제
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_label.configure(text=f"{self.year}년 {self.month}월")

        # 요일 헤더 (일요일 시작)
        days = ["일", "월", "화", "수", "목", "금", "토"]
        for i, day in enumerate(days):
            text_color = "white"
            if i == 0: text_color = "#FF6B6B" # 일요일 빨강
            elif i == 6: text_color = "#4D96FF" # 토요일 파랑
            
            ctk.CTkLabel(self.calendar_frame, text=day, font=("Malgun Gothic", 12, "bold"), text_color=text_color).grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

        # [레이아웃] 열 너비 고정
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="days")

        # 데이터 로드 및 그룹화
        df = self.dm.df
        events = {}
        if not df.empty and '출고예정일' in df.columns:
            df_filtered = df[df['출고예정일'].str.startswith(f"{self.year}-{str(self.month).zfill(2)}", na=False)].copy()
            df_filtered['day'] = pd.to_datetime(df_filtered['출고예정일']).dt.day
            events = df_filtered.groupby('day').apply(lambda x: x.to_dict('records')).to_dict()

        # 달력 날짜 생성 (일요일 시작)
        cal = calendar.Calendar(firstweekday=6).monthdayscalendar(self.year, self.month)
        
        for r, week in enumerate(cal):
            # [레이아웃] 행 높이 고정
            self.calendar_frame.grid_rowconfigure(r + 1, weight=1, uniform="weeks")
            
            for c, day in enumerate(week):
                cell_frame = ctk.CTkFrame(self.calendar_frame, border_width=1, border_color="#444444", fg_color="transparent")
                cell_frame.grid(row=r + 1, column=c, sticky="nsew")

                if day == 0:
                    continue
                
                # Cell 내부 레이아웃
                cell_frame.grid_rowconfigure(1, weight=1)
                cell_frame.grid_columnconfigure(0, weight=1)
                
                # 날짜 텍스트
                day_color = "white"
                if c == 0: day_color = "#FF6B6B"
                elif c == 6: day_color = "#4D96FF"
                
                ctk.CTkLabel(cell_frame, text=str(day), font=("Malgun Gothic", 12), text_color=day_color).grid(row=0, column=0, sticky="nw", padx=5, pady=5)
                
                # 해당 날짜의 이벤트 표시
                if day in events:
                    event_scroll_frame = ctk.CTkScrollableFrame(cell_frame, fg_color="transparent")
                    event_scroll_frame.grid(row=1, column=0, sticky='nsew', padx=3, pady=3)
                    
                    # 업체명으로 정렬
                    day_events = sorted(events[day], key=lambda x: str(x['업체명']))
                    
                    last_comp_name = None 

                    for event in day_events:
                        current_comp_name = str(event['업체명'])
                        model_name = str(event['모델명'])
                        qty = event['수량']

                        # 1. 업체명이 바뀔 때만 '헤더' 생성
                        if current_comp_name != last_comp_name:
                            display_comp_name = current_comp_name
                            if len(display_comp_name) > 8:
                                display_comp_name = display_comp_name[:8] + ".."
                            
                            # 업체명 헤더 (그룹 간 구분을 위해 상단에만 아주 미세한 여백 2 부여)
                            header_label = ctk.CTkLabel(
                                event_scroll_frame,
                                text=f"• {display_comp_name}",
                                font=("Malgun Gothic", 11, "bold"),
                                text_color="#3B8ED0", # 파란색 강조
                                anchor="w",
                                height=15 # 높이 강제 제한 (컴팩트하게)
                            )
                            # pady=(2, 0): 위쪽 2px, 아래쪽 0px
                            header_label.pack(fill="x", pady=(2, 0), padx=2)
                            last_comp_name = current_comp_name

                        # 2. 품목(모델) 생성 (여백 0)
                        item_text = f"  - {model_name} ({qty})"
                        item_label = ctk.CTkLabel(
                            event_scroll_frame, 
                            text=item_text, 
                            justify="left", 
                            font=("Malgun Gothic", 10), 
                            anchor="w",
                            height=15 # 높이 강제 제한 (컴팩트하게)
                        )
                        # pady=0: 위아래 여백 없음 (딱 붙임)
                        item_label.pack(fill="x", pady=0, padx=2)

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