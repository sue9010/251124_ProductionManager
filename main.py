import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from calendar_view import CalendarView
from config import Config
from data_manager import DataManager
from popups import PopupManager


# ==========================================
# [App] 메인 프로그램 클래스 (Main View)
# ==========================================
class COXProductionManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 기본 윈도우 설정
        self.title("COX Production Manager")
        self.geometry("1600x800")
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # 2. 모듈 초기화
        self.dm = DataManager() # 데이터 로직 담당
        self.pm = PopupManager(self, self.dm, self.refresh_ui)

        # 필터 상태 관리 (기본값: 접수/생산중=True, 완료=False)
        self.filter_states = {
            "생산 접수": True,
            "생산중": True,
            "완료": False
        }

        # [추가] 정렬 상태 관리
        self.sort_col = None     # 현재 정렬된 컬럼
        self.sort_desc = False   # 내림차순 여부 (False: 오름차순, True: 내림차순)

        # 3. UI 생성
        self.create_widgets()
        self.style_treeview()
        
        # 초기 버튼 스타일 적용
        self.update_filter_buttons_visuals()
        
        # 4. 이벤트 바인딩
        self.tree.bind("<Double-1>", self.on_double_click)

        # 5. 초기 데이터 로드 시도
        self.load_data_btn_click()

    def create_widgets(self):
        # 상단 프레임
        top_frame = ctk.CTkFrame(self, corner_radius=10)
        top_frame.pack(fill="x", padx=20, pady=20)

        # 로고
        ctk.CTkLabel(top_frame, text="COX Production Manager", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20, pady=15)

        # --- [우측 컨트롤 그룹] ---
        # 1. 설정 버튼
        ctk.CTkButton(top_frame, text="설정", command=self.pm.open_settings, width=60, fg_color="#555555", hover_color="#333333").pack(side="right", padx=(10, 20))

        # [NEW] 달력으로 보기 버튼
        ctk.CTkButton(top_frame, text="달력으로 보기", command=self.open_calendar_popup, width=110, fg_color="#555555", hover_color="#333333").pack(side="right", padx=(5, 0))

        # 2. 검색 버튼
        ctk.CTkButton(top_frame, text="검색", command=self.refresh_ui, width=50, fg_color="#777777", hover_color="#555555").pack(side="right", padx=(5, 5))

        # 3. 검색창
        self.search_entry = ctk.CTkEntry(top_frame, width=200, placeholder_text="번호, 업체, 모델, 시리얼...")
        self.search_entry.pack(side="right", padx=(10, 5))
        self.search_entry.bind("<Return>", lambda e: self.refresh_ui())

        # 4. 데이터 읽어오기 버튼
        ctk.CTkButton(top_frame, text="데이터 읽어오기", command=self.load_data_btn_click, font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#3B8ED0", hover_color="#36719F").pack(side="right", padx=10)

        # 5. [필터 버튼 그룹]
        ctk.CTkFrame(top_frame, width=2, height=30, fg_color="#444444").pack(side="right", padx=10)
        self.filter_buttons = {}

        # (3) 완료 버튼
        self.btn_complete = ctk.CTkButton(top_frame, text="완료", command=lambda: self.toggle_filter("완료"), width=80, height=35, font=ctk.CTkFont(size=12, weight="bold"))
        self.btn_complete.pack(side="right", padx=5)
        self.filter_buttons["완료"] = self.btn_complete

        # (2) 생산중 버튼
        self.btn_prod = ctk.CTkButton(top_frame, text="생산중", command=lambda: self.toggle_filter("생산중"), width=80, height=35, font=ctk.CTkFont(size=12, weight="bold"))
        self.btn_prod.pack(side="right", padx=5)
        self.filter_buttons["생산중"] = self.btn_prod

        # (1) 생산 접수 버튼
        self.btn_receipt = ctk.CTkButton(top_frame, text="생산 접수", command=lambda: self.toggle_filter("생산 접수"), width=80, height=35, font=ctk.CTkFont(size=12, weight="bold"))
        self.btn_receipt.pack(side="right", padx=5)
        self.filter_buttons["생산 접수"] = self.btn_receipt


        # 트리뷰 프레임
        tree_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 스크롤바
        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")

        # 트리뷰
        self.tree = ttk.Treeview(tree_frame, columns=Config.DISPLAY_COLUMNS, show="headings", yscrollcommand=scroll_y.set)
        scroll_y.configure(command=self.tree.yview)
        scroll_y.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # 트리뷰 헤더 설정 (클릭 이벤트 바인딩)
        for col in Config.DISPLAY_COLUMNS:
            self.tree.heading(col, text=col, command=lambda c=col: self.on_header_click(c))
            
            width = 100
            if col in ["업체명", "모델명", "상세"]: width = 150
            if col == "번호": width = 50
            if col == "Status": width = 80
            self.tree.column(col, width=width, anchor="center")

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=35, font=("Malgun Gothic", 12))
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="#3B8ED0", font=("Malgun Gothic", 14, "bold"), relief="flat")
        style.map("Treeview.Heading", background=[('active', '#333333')])

    # -----------------------------------------------------
    # Logic: Sorting
    # -----------------------------------------------------
    def on_header_click(self, col):
        """헤더 클릭 시 정렬 로직"""
        if self.sort_col == col:
            # 같은 컬럼 클릭 시 순서 반전
            self.sort_desc = not self.sort_desc
        else:
            # 다른 컬럼 클릭 시 해당 컬럼 오름차순으로 시작
            self.sort_col = col
            self.sort_desc = False
        
        # 헤더 텍스트 업데이트 (화살표 표시)
        for c in Config.DISPLAY_COLUMNS:
            text = c
            if c == self.sort_col:
                text += " ▼" if self.sort_desc else " ▲"
            self.tree.heading(c, text=text)

        self.refresh_ui()

    # -----------------------------------------------------
    # Logic: Filter Buttons
    # -----------------------------------------------------
    def toggle_filter(self, status):
        """필터 버튼 클릭 시 상태 토글"""
        self.filter_states[status] = not self.filter_states[status]
        self.update_filter_buttons_visuals()
        self.refresh_ui()

    def update_filter_buttons_visuals(self):
        active_color = "#3B8ED0" # 활성 색상 (Blue)
        text_color_active = "white"
        
        inactive_fg = "transparent" # 비활성 배경
        inactive_border = "#555555" # 비활성 테두리
        text_color_inactive = "#AAAAAA"

        for status, btn in self.filter_buttons.items():
            is_active = self.filter_states.get(status, False)
            if is_active:
                btn.configure(fg_color=active_color, text_color=text_color_active, border_width=0)
            else:
                btn.configure(fg_color=inactive_fg, text_color=text_color_inactive, border_width=2, border_color=inactive_border)

    def reset_default_filters(self):
        self.filter_states["생산 접수"] = True
        self.filter_states["생산중"] = True
        self.filter_states["완료"] = False
        self.update_filter_buttons_visuals()

    # -----------------------------------------------------
    # Event Handlers & Logic Connection
    # -----------------------------------------------------
    def load_data_btn_click(self):
        """데이터 읽어오기 버튼 클릭 시"""
        try:
            success, path_name = self.dm.load_data()
            if success:
                messagebox.showinfo("성공", f"데이터를 불러왔습니다.\n({path_name})")
            else:
                if messagebox.askyesno("파일 없음", "파일이 없습니다. 테스트용 데이터를 생성할까요?"):
                    self.dm.create_dummy_data()
                else:
                    return
            
            # 정렬 상태 초기화 (원하면 유지 가능)
            self.sort_col = None
            self.sort_desc = False
            for col in Config.DISPLAY_COLUMNS:
                self.tree.heading(col, text=col)

            self.reset_default_filters()
            self.refresh_ui()
            
        except Exception as e:
            messagebox.showerror("에러", f"로딩 중 오류 발생: {e}")

    def refresh_ui(self):
        """현재 필터(버튼)/검색/정렬 조건에 맞춰 테이블 갱신"""
        selected_statuses = [s for s, active in self.filter_states.items() if active]
        keyword = self.search_entry.get().strip()
        
        # [수정] 정렬 파라미터 전달
        filtered_df = self.dm.get_filtered_data(
            selected_statuses, 
            keyword, 
            sort_by=self.sort_col, 
            ascending=not self.sort_desc
        )
        
        for item in self.tree.get_children():
            self.tree.delete(item)

        if filtered_df is not None and not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                values = [row[col] for col in Config.DISPLAY_COLUMNS]
                self.tree.insert("", "end", values=values)

    def on_double_click(self, event):
        """더블 클릭 이벤트 라우팅"""
        selected = self.tree.selection()
        if not selected: return
        
        item = selected[0]
        values = self.tree.item(item, "values")
        req_no = values[0]
        status = str(values[-1]).strip()

        if status == "생산 접수":
            self.pm.open_schedule_popup(req_no)
        elif status == "생산중":
            self.pm.open_complete_popup(req_no)
        elif status == "완료": 
            self.pm.open_completed_view_popup(req_no)

    def open_calendar_popup(self):
        """달력 팝업을 엽니다."""
        # Check if a calendar window already exists
        if not hasattr(self, "calendar_window") or not self.calendar_window.winfo_exists():
            self.calendar_window = CalendarView(self, self.dm)
        else:
            self.calendar_window.focus() # If it exists, bring it to the front

if __name__ == "__main__":
    app = COXProductionManager()
    app.mainloop()