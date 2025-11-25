import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from styles import COLORS, FONTS


class KanbanView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 상태 정의 및 표시 순서
        self.columns = {
            "생산 접수": {"color": COLORS["primary"], "bg": COLORS["bg_dark"]},
            "대기":     {"color": COLORS["warning"], "bg": COLORS["bg_dark"]},
            "생산중":   {"color": COLORS["success"], "bg": COLORS["bg_dark"]},
            "작업 중지": {"color": COLORS["danger"],  "bg": COLORS["bg_dark"]},
            "완료":     {"color": COLORS["text_dim"], "bg": COLORS["bg_dark"]}
        }
        
        # UI 요소 저장소
        self.column_frames = {}  # { "상태명": scrollable_frame }
        self.cards = {}          # { req_no: card_widget }

        # 드래그 앤 드롭 상태
        self.drag_data = {
            "item": None,
            "req_no": None,
            "text": None,
            "window": None,
            "start_status": None
        }
        self.click_timer = None
        self.drag_started = False

        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # 1. 상단 툴바 (새로고침 등)
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(toolbar, text="📋 Kanban Board", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(
            toolbar, text="🔄 새로고침", width=80, height=32,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            command=self.refresh_data
        ).pack(side="right")

        # 2. 메인 보드 영역 (가로 스크롤 가능하게 하거나, 화면에 꽉 차게)
        # 여기서는 5개 열이므로 화면에 꽉 차게 Grid 사용
        self.board_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.board_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # [수정] 행(Row) 높이가 화면에 꽉 차도록 가중치 설정 (이 부분이 핵심입니다)
        self.board_frame.grid_rowconfigure(0, weight=1)

        # 5개 열 생성
        for i, (status, style) in enumerate(self.columns.items()):
            self.board_frame.grid_columnconfigure(i, weight=1, uniform="col")
            
            # 컬럼 컨테이너
            col_container = ctk.CTkFrame(self.board_frame, fg_color=style["bg"], corner_radius=10, border_width=1, border_color=COLORS["border"])
            col_container.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            col_container.status_tag = status # 식별 태그

            # 헤더
            header = ctk.CTkFrame(col_container, height=40, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=5)
            
            # 상태 점(Dot) + 텍스트
            dot = ctk.CTkLabel(header, text="●", font=("Arial", 14), text_color=style["color"])
            dot.pack(side="left", padx=(0, 5))
            
            title = ctk.CTkLabel(header, text=status, font=FONTS["header"])
            title.pack(side="left")
            
            # 건수 배지 (나중에 업데이트)
            count_badge = ctk.CTkLabel(header, text="0", width=24, height=24, fg_color=COLORS["bg_medium"], corner_radius=12, font=("Arial", 10, "bold"))
            count_badge.pack(side="right")
            
            # 카드 리스트 영역 (스크롤)
            scroll_frame = ctk.CTkScrollableFrame(col_container, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 저장
            self.column_frames[status] = {
                "frame": scroll_frame,
                "badge": count_badge,
                "container": col_container # 드롭 타겟 식별용
            }

    def refresh_data(self):
        # 데이터 로드
        df = self.dm.df
        if df.empty: return

        # 기존 카드 제거
        for status in self.column_frames:
            for widget in self.column_frames[status]["frame"].winfo_children():
                widget.destroy()

        # 상태별 데이터 그룹화
        # 용어 통일 (Hold -> 작업 중지)
        status_series = df['Status'].fillna('').astype(str).str.strip()
        
        for status in self.columns.keys():
            target_df = pd.DataFrame()
            
            if status == "작업 중지":
                target_df = df[status_series.isin(['Hold', '작업 중지', '중지'])].copy()
            else:
                target_df = df[status_series == status].copy()
            
            # 정렬: 번호 역순(최신순)
            if not target_df.empty:
                if "번호" in target_df.columns:
                    target_df = target_df.sort_values(by="번호", ascending=False)
            
            # 뱃지 업데이트
            count = len(target_df)
            self.column_frames[status]["badge"].configure(text=str(count))

            # 카드 생성
            self.create_cards(status, target_df)

    def create_cards(self, status, df):
        parent = self.column_frames[status]["frame"]
        
        for _, row in df.iterrows():
            req_no = row['번호']
            comp = str(row['업체명'])
            model = str(row['모델명'])
            qty = str(row['수량'])
            date = str(row['출고예정일']) if pd.notna(row['출고예정일']) else "-"
            if status == "생산 접수": date = str(row['출고요청일']) # 접수 단계에선 요청일 표시

            # 카드 프레임
            card = ctk.CTkFrame(parent, fg_color=COLORS["bg_medium"], corner_radius=6, border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=4, padx=2)
            
            # 내용
            # 상단: 업체명 | 수량
            top_row = ctk.CTkFrame(card, fg_color="transparent", height=20)
            top_row.pack(fill="x", padx=8, pady=(8, 2))
            
            ctk.CTkLabel(top_row, text=comp, font=("Malgun Gothic", 11, "bold"), text_color=COLORS["primary"]).pack(side="left")
            ctk.CTkLabel(top_row, text=f"{qty}EA", font=("Malgun Gothic", 11), text_color=COLORS["text_dim"]).pack(side="right")
            
            # 중단: 모델명
            mid_row = ctk.CTkFrame(card, fg_color="transparent")
            mid_row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(mid_row, text=model, font=("Malgun Gothic", 12), text_color=COLORS["text"], wraplength=180, justify="left").pack(anchor="w")
            
            # 하단: 번호 | 날짜
            bot_row = ctk.CTkFrame(card, fg_color="transparent")
            bot_row.pack(fill="x", padx=8, pady=(2, 8))
            ctk.CTkLabel(bot_row, text=f"No.{req_no}", font=("Arial", 10), text_color=COLORS["text_dim"]).pack(side="left")
            
            date_color = COLORS["text_dim"]
            if status == "생산중": date_color = COLORS["success"]
            ctk.CTkLabel(bot_row, text=date, font=("Arial", 10), text_color=date_color).pack(side="right")

            # 이벤트 바인딩 (DnD)
            # 카드 전체와 내부 라벨들에 이벤트 연결
            drag_text = f"[{req_no}] {comp} - {model}"
            for w in [card] + card.winfo_children() + top_row.winfo_children() + mid_row.winfo_children() + bot_row.winfo_children():
                w.bind("<Button-1>", lambda e, r=req_no, s=status, t=drag_text, w=card: self.start_drag(e, r, s, t, w))
                w.bind("<B1-Motion>", self.do_drag)
                w.bind("<ButtonRelease-1>", self.stop_drag)
                w.bind("<Double-1>", lambda e, r=req_no: self.on_card_double_click(r))

    def on_card_double_click(self, req_no):
        # 기존 팝업 매니저 로직 재사용을 위해 상태 조회
        status = self.dm.get_status_by_req_no(req_no)
        if status == "생산중":
            self.pm.open_complete_popup(req_no)
        elif status == "완료":
            self.pm.open_completed_view_popup(req_no)
        else:
            self.pm.open_schedule_popup(req_no)

    # ==========================================================
    # [Drag & Drop] 로직
    # ==========================================================
    def _start_drag_window(self, text):
        self.drag_started = True
        if self.drag_data["window"] is None:
            self.drag_data["window"] = ctk.CTkToplevel(self)
            self.drag_data["window"].overrideredirect(True)
            self.drag_data["window"].attributes("-topmost", True)
            self.drag_data["window"].attributes("-alpha", 0.7)
            
            lbl = ctk.CTkLabel(
                self.drag_data["window"], text=text, 
                fg_color=COLORS["primary"], text_color="white",
                corner_radius=5, padx=10, pady=5
            )
            lbl.pack()
            
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def start_drag(self, event, req_no, status, text, widget):
        self.drag_data.update({
            "item": widget, 
            "req_no": req_no, 
            "start_status": status,
            "text": text
        })
        self.drag_started = False
        if self.click_timer: self.after_cancel(self.click_timer)
        self.click_timer = self.after(150, lambda: self._start_drag_window(text))

    def do_drag(self, event):
        if self.drag_started and self.drag_data["window"]:
            x, y = self.winfo_pointerxy()
            self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def stop_drag(self, event):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None

        if self.drag_started:
            if self.drag_data["window"]:
                self.drag_data["window"].destroy()
                self.drag_data["window"] = None
            
            # 드롭 위치 판별
            x, y = self.winfo_pointerxy()
            target_widget = self.winfo_containing(x, y)
            target_status = self.find_target_column(target_widget)
            
            req_no = self.drag_data["req_no"]
            start_status = self.drag_data["start_status"]

            if target_status and target_status != start_status:
                self.handle_status_change(req_no, start_status, target_status)
            
        self.drag_data = {"item": None, "req_no": None, "start_status": None, "text": None, "window": None}
        self.drag_started = False

    def find_target_column(self, widget):
        """마우스가 놓인 위치의 컬럼 상태명을 찾습니다."""
        current = widget
        while current:
            # 컬럼 컨테이너에 status_tag를 심어뒀음
            if hasattr(current, "status_tag"):
                return current.status_tag
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return None

    def handle_status_change(self, req_no, from_status, to_status):
        """상태 변경 처리 로직"""
        success = False
        msg = ""

        # 1. 완료 처리 (팝업 필요)
        if to_status == "완료":
            # DnD로는 즉시 완료 처리가 애매함(시리얼 등 입력 필요). 팝업을 띄워줌
            self.pm.open_complete_popup(req_no)
            return # 팝업에서 저장하면 갱신됨

        # 2. 생산중 (날짜 지정 필요) -> 오늘 날짜로 자동 시작하거나, 기존 예정일 유지
        elif to_status == "생산중":
            # 기존 예정일이 있으면 유지, 없으면 오늘 날짜
            # 여기서는 단순화를 위해 오늘 날짜로 자동 설정 (필요 시 팝업)
            today = datetime.now().strftime("%Y-%m-%d")
            success, msg = self.dm.update_production_schedule(req_no, today)

        # 3. 작업 중지 (Hold)
        elif to_status == "작업 중지":
            success, msg = self.dm.update_status_to_hold(req_no)

        # 4. 대기
        elif to_status == "대기":
            success, msg = self.dm.update_status_to_waiting(req_no, reason="칸반 보드 이동")

        # 5. 생산 접수 (초기화?)
        elif to_status == "생산 접수":
            # 로직이 복잡할 수 있음 (초기화 등). 여기선 일단 경고
            messagebox.showwarning("알림", "생산 접수 상태로 되돌릴 수 없습니다. (데이터 관리 필요)")
            return

        if success:
            self.refresh_data()
        elif msg:
            messagebox.showerror("실패", msg)