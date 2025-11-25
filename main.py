import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter as ctk

# 모듈 임포트
from calendar_view import CalendarView
from config import Config
from data_manager import DataManager
from popup_manager import PopupManager
from styles import COLORS, FONTS


# ==========================================
# [App] 메인 프로그램 클래스 (Main View)
# ==========================================
class COXProductionManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 기본 윈도우 설정
        self.title(f"COX Production Manager - v{Config.APP_VERSION}")
        self.geometry("1650x900") 
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # 2. 모듈 초기화
        self.dm = DataManager()
        self.pm = PopupManager(self, self.dm, self.refresh_ui)

        # 3. 데이터 관리 변수
        self.search_start_date = None
        self.search_end_date = None
        self.sort_col = None
        self.sort_desc = False

        # [복원] 다중 필터 상태 관리 (기본값: 중지, 완료 제외하고 모두 True)
        self.filter_states = {
            "생산 접수": True,
            "대기": True,
            "생산중": True,
            "중지": False,
            "완료": False
        }
        self.filter_check_vars = {} # 체크박스 변수 저장용

        # 4. UI 생성
        self.create_widgets()
        self.style_treeview()
        
        # 5. 이벤트 바인딩
        self.tree.bind("<Double-1>", self.on_double_click)
        # 빈 곳 클릭 시 드롭다운 닫기 위한 바인딩
        self.bind("<Button-1>", self.close_dropdown_if_clicked_outside)

        # 6. 초기 데이터 로드
        self.load_data_btn_click(show_msg=False)

    def create_widgets(self):
        # [수정 포인트 1] 너비 상수 정의 (여기서 한 번만 바꾸면 버튼과 박스 모두 적용됨)
        # 100px은 너무 좁으므로 120px 정도 추천합니다.
        FILTER_WIDTH = 120

        # 전체 메인 컨테이너
        self.main_container = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # ---------------------------------------------------------
        # 1. Header Frame (Top)
        # ---------------------------------------------------------
        self.header_frame = ctk.CTkFrame(self.main_container, height=80, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.header_frame.pack(side="top", fill="x", pady=(0, 1))

        # 로고 영역
        logo_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        logo_frame.pack(side="left", padx=30, pady=20)
        
        # ctk.CTkLabel(logo_frame, text="🏭", font=("Emoji", 32)).pack(side="left", padx=(0, 10))
        
        title_box = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_box.pack(side="left")
        
        ctk.CTkLabel(title_box, text="COX Production Manager", font=("Malgun Gothic", 20, "bold"), text_color=COLORS["text"], anchor="w").pack(side="top", fill="x")
        # ctk.CTkLabel(title_box, text="v1.0.0", font=("Malgun Gothic", 12), text_color=COLORS["text_dim"], anchor="w").pack(side="top", fill="x")

        # 시스템 버튼 그룹
        sys_btn_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        sys_btn_frame.pack(side="right", padx=30)

        self.btn_calendar = ctk.CTkButton(
            sys_btn_frame, text="📅  일정 달력", 
            command=self.open_calendar_popup,
            width=120, height=38,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            font=FONTS["main_bold"], corner_radius=8
        )
        self.btn_calendar.pack(side="left", padx=5)

        self.btn_settings = ctk.CTkButton(
            sys_btn_frame, text="⚙️ 설정", 
            command=self.pm.open_settings,
            width=90, height=38,
            fg_color="transparent", border_width=1, border_color=COLORS["border"],
            hover_color=COLORS["bg_medium"],
            font=FONTS["main"], corner_radius=8
        )
        self.btn_settings.pack(side="left", padx=(10,0))

        ctk.CTkFrame(self.main_container, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # ---------------------------------------------------------
        # 2. Toolbar Frame (Custom Dropdown 스타일)
        # ---------------------------------------------------------
        self.toolbar_wrapper = ctk.CTkFrame(self.main_container, fg_color=COLORS["bg_dark"], height=60)
        self.toolbar_wrapper.pack(side="top", fill="x", padx=30, pady=(5, 10))

        # [Left] 다중 선택 필터 드롭다운
        view_frame = ctk.CTkFrame(self.toolbar_wrapper, fg_color="transparent")
        view_frame.pack(side="left")

        ctk.CTkLabel(
            view_frame, text="Filter:", 
            font=("Malgun Gothic", 12, "bold"), text_color=COLORS["text_dim"]
        ).pack(side="left", padx=(0, 10))

        # [수정 포인트 2] 버튼 너비에 변수 적용
        self.filter_dropdown_btn = ctk.CTkButton(
            view_frame,
            text="필터 선택 ▼", # 초기 텍스트 짧게 수정
            command=self.toggle_filter_dropdown,
            width=FILTER_WIDTH, height=34,
            fg_color=COLORS["bg_medium"],
            hover_color=COLORS["bg_light"],
            border_color=COLORS["border"],
            border_width=1,
            font=("Malgun Gothic", 12),
            anchor="w"
        )
        self.filter_dropdown_btn.pack(side="left")

        # [수정 포인트 3] 드롭다운 프레임 너비 및 고정 설정
        self.dropdown_frame = ctk.CTkFrame(
            self, 
            width=FILTER_WIDTH, 
            fg_color=COLORS["bg_medium"], 
            border_width=1, 
            border_color=COLORS["primary"],
            corner_radius=5
        )
        # [핵심!] 이 설정이 있어야 내부 글자가 길어도 프레임이 늘어나지 않고 고정됩니다.
        self.dropdown_frame.pack_propagate(False)
        
        # 드롭다운 내부 체크박스 생성
        self._init_filter_checkboxes()
        self.is_dropdown_open = False

        # [Right] 검색 그룹
        control_frame = ctk.CTkFrame(self.toolbar_wrapper, fg_color="transparent")
        control_frame.pack(side="right")
        
        # 기간 검색
        ctk.CTkButton(
            control_frame, text="📅 기간 검색", 
            command=self.open_date_range_popup,
            width=90, height=34,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            corner_radius=6
        ).pack(side="left", padx=5)

        # 검색창
        self.search_entry = ctk.CTkEntry(
            control_frame, 
            width=220, height=34, 
            placeholder_text="번호, 업체, 모델명...",
            border_color=COLORS["border"],
            fg_color=COLORS["bg_medium"],
            corner_radius=6
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh_ui())
        
        ctk.CTkButton(
            control_frame, text="검색", 
            command=self.refresh_ui, 
            width=60, height=34,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            border_width=1, border_color=COLORS["border"],
            corner_radius=6
        ).pack(side="left", padx=2)

        # 데이터 로드
        ctk.CTkButton(
            control_frame, text="🔄 Reload", 
            command=self.load_data_btn_click,
            width=90, height=34,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            font=FONTS["main_bold"], corner_radius=6
        ).pack(side="left", padx=(10, 0))

        # ---------------------------------------------------------
        # 3. Treeview Frame (Main)
        # ---------------------------------------------------------
        self.tree_bg_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.tree_bg_frame.pack(side="top", fill="both", expand=True, padx=30, pady=(10, 20))
        
        self.tree_frame = ctk.CTkFrame(self.tree_bg_frame, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=2, pady=2)

        scroll_y = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", button_color=COLORS["bg_light"], button_hover_color=COLORS["bg_light_hover"])
        
        self.tree = ttk.Treeview(
            self.tree_frame, 
            columns=Config.DISPLAY_COLUMNS, 
            show="headings", 
            yscrollcommand=scroll_y.set
        )
        scroll_y.configure(command=self.tree.yview)
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        for col in Config.DISPLAY_COLUMNS:
            self.tree.heading(col, text=col, command=lambda c=col: self.on_header_click(c))
            width = 100
            if col in ["업체명", "모델명", "상세"]: width = 160
            if col == "번호": width = 70
            if col == "Status": width = 100
            self.tree.column(col, width=width, anchor="center")

        # ---------------------------------------------------------
        # 4. Dashboard Frame (Bottom)
        # ---------------------------------------------------------
        self.dashboard_frame = ctk.CTkFrame(self.main_container, height=40, fg_color=COLORS["bg_medium"], corner_radius=0)
        self.dashboard_frame.pack(side="bottom", fill="x")
        
        ctk.CTkFrame(self.dashboard_frame, height=1, fg_color=COLORS["primary"]).pack(side="top", fill="x")

        self.dashboard_label = ctk.CTkLabel(
            self.dashboard_frame, 
            text="Ready", 
            font=("Malgun Gothic", 11), 
            text_color=COLORS["text_dim"]
        )
        self.dashboard_label.pack(side="left", padx=30, pady=8)
        
        ctk.CTkLabel(
            self.dashboard_frame,
            text=f"Ver {Config.APP_VERSION}",
            font=("Arial", 10),
            text_color="#555555"
        ).pack(side="right", padx=20)


    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        bg_color = COLORS["bg_dark"]
        header_bg = "#3a3a3a"
        text_color = "#eeeeee"
        
        style.configure(
            "Treeview", 
            background=bg_color, 
            foreground=text_color, 
            fieldbackground=bg_color, 
            rowheight=38,
            font=("Malgun Gothic", 11),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading", 
            background=header_bg, 
            foreground=COLORS["primary"], 
            font=("Malgun Gothic", 12, "bold"), 
            relief="flat",
            padding=(0, 8)
        )
        style.map("Treeview.Heading", background=[('active', "#444444")])
        style.map("Treeview", background=[('selected', COLORS["primary_hover"])])

        self.tree.tag_configure("중지", background="#4a2626", foreground="#ffcccc")
        self.tree.tag_configure("완료", foreground="#888888")
        self.tree.tag_configure("생산중", foreground="#4caf50")
        self.tree.tag_configure("대기", foreground="#ff9800")
        self.tree.tag_configure("today", background="#2c3e50")

    # ------------------------------------------------------------------
    # [핵심] 커스텀 드롭다운 메뉴 로직
    # ------------------------------------------------------------------
    def _init_filter_checkboxes(self):
        """드롭다운 프레임 내부에 체크박스를 생성합니다."""
        # 전체 선택 버튼
        self.cb_all = ctk.CTkCheckBox(
            self.dropdown_frame, text="전체", 
            command=self.toggle_all_filters,
            font=("Malgun Gothic", 11, "bold"),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]
        )
        self.cb_all.pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkFrame(self.dropdown_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=5, pady=2)

        # 개별 상태 체크박스
        for status, is_checked in self.filter_states.items():
            var = ctk.BooleanVar(value=is_checked)
            self.filter_check_vars[status] = var
            cb = ctk.CTkCheckBox(
                self.dropdown_frame, 
                text=status, 
                variable=var, 
                command=self.on_filter_change,
                font=("Malgun Gothic", 11),
                fg_color=COLORS["primary"], 
                hover_color=COLORS["primary_hover"]
            )
            cb.pack(anchor="w", padx=10, pady=3)
        
        # [수정] 박스 높이 자동 조절 (항목 수에 맞춰 빈 공간 없이 딱 맞게)
        # 계산식: 헤더(45px) + (항목 수 * 32px) + 하단 여백(0px)
        item_count = len(self.filter_states)
        calc_height = 45 + (item_count * 32) + 0
        self.dropdown_frame.configure(height=calc_height)
        
        self.update_dropdown_btn_text()

    def toggle_filter_dropdown(self):
        """드롭다운 메뉴를 열거나 닫습니다."""
        if self.is_dropdown_open:
            self.dropdown_frame.place_forget()
            self.is_dropdown_open = False
        else:
            # 버튼 바로 아래에 위치 계산
            x = self.filter_dropdown_btn.winfo_rootx() - self.winfo_rootx()
            y = self.filter_dropdown_btn.winfo_rooty() - self.winfo_rooty() + self.filter_dropdown_btn.winfo_height() + 5
            
            self.dropdown_frame.place(x=x, y=y)
            self.dropdown_frame.lift() # 맨 위로 올리기
            self.is_dropdown_open = True

    def close_dropdown_if_clicked_outside(self, event):
        """드롭다운 영역 밖을 클릭하면 닫습니다."""
        if self.is_dropdown_open:
            # 클릭된 위젯이 드롭다운이나 그 자식이 아니면 닫기
            x, y = event.x_root, event.y_root
            if not (self.dropdown_frame.winfo_rootx() <= x <= self.dropdown_frame.winfo_rootx() + self.dropdown_frame.winfo_width() and
                    self.dropdown_frame.winfo_rooty() <= y <= self.dropdown_frame.winfo_rooty() + self.dropdown_frame.winfo_height()):
                
                # 버튼 자체를 클릭했을 때는 toggle 함수가 처리하므로 제외
                if self.filter_dropdown_btn.winfo_rootx() <= x <= self.filter_dropdown_btn.winfo_rootx() + self.filter_dropdown_btn.winfo_width() and \
                   self.filter_dropdown_btn.winfo_rooty() <= y <= self.filter_dropdown_btn.winfo_rooty() + self.filter_dropdown_btn.winfo_height():
                    return

                self.dropdown_frame.place_forget()
                self.is_dropdown_open = False

    def toggle_all_filters(self):
        """전체 선택/해제 토글"""
        new_state = bool(self.cb_all.get())
        for status, var in self.filter_check_vars.items():
            var.set(new_state)
            self.filter_states[status] = new_state
        self.on_filter_change()

    def on_filter_change(self):
        """체크박스 변경 시 호출"""
        # 1. 상태 동기화
        selected_count = 0
        for status, var in self.filter_check_vars.items():
            is_checked = var.get()
            self.filter_states[status] = is_checked
            if is_checked: selected_count += 1
        
        # 2. 버튼 텍스트 업데이트
        self.update_dropdown_btn_text(selected_count)
        
        # 3. UI 갱신
        self.refresh_ui()

    def update_dropdown_btn_text(self, count=None):
        if count is None:
            count = sum(self.filter_states.values())
        
        total = len(self.filter_states)
        if count == total:
            # [수정 포인트 4] 글자가 잘리지 않도록 짧게 변경
            text = "전체 (All) ▼"
        elif count == 0:
            text = "선택 안함 ▼"
        else:
            text = f"선택됨 ({count}) ▼"
        
        self.filter_dropdown_btn.configure(text=text)

    # ------------------------------------------------------------------

    def load_data_btn_click(self, show_msg=True):
        try:
            success, path_name = self.dm.load_data()
            if success:
                if show_msg:
                    messagebox.showinfo("성공", f"데이터 로드 완료\n({path_name})")
            else:
                if messagebox.askyesno("파일 없음", "테스트용 데이터를 생성할까요?"):
                    self.dm.create_dummy_data()
                else:
                    return
            self.refresh_ui()
        except Exception as e:
            messagebox.showerror("에러", f"로딩 오류: {e}")

    def refresh_ui(self):
        # 1. 현재 체크된 상태들 가져오기
        selected_statuses = [s for s, active in self.filter_states.items() if active]
        keyword = self.search_entry.get().strip()
        
        # 2. 데이터 조회
        # 선택된 게 하나도 없으면 빈 리스트 전달 -> 0건 조회됨
        filtered_df = self.dm.get_filtered_data(
            selected_statuses, 
            keyword, 
            sort_by=self.sort_col, 
            ascending=not self.sort_desc
        )
        
        if self.search_start_date and self.search_end_date:
            pass

        # 3. 트리뷰 갱신
        for item in self.tree.get_children():
            self.tree.delete(item)

        today_str = datetime.now().strftime("%Y-%m-%d")

        if filtered_df is not None and not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                values = list(row[col] for col in Config.DISPLAY_COLUMNS)
                status = row['Status']
                req_date = str(row['출고요청일'])

                model_idx = Config.DISPLAY_COLUMNS.index("모델명")
                row_tags = [status]

                if req_date == today_str:
                    values[model_idx] = f"⚡ {values[model_idx]}"
                    row_tags.append("today")
                
                self.tree.insert("", "end", values=values, tags=tuple(row_tags))
        
        self.update_dashboard(filtered_df)

    def update_dashboard(self, df):
        if df is None:
            total, waiting, hold = 0, 0, 0
        else:
            total = len(df)
            waiting = len(df[df['Status'] == '대기'])
            hold = len(df[df['Status'] == '중지'])
        
        status_text = f"  📦 전체 항목: {total}   |   ⏳ 생산 대기: {waiting}   |   ⛔ 중지: {hold}"
        self.dashboard_label.configure(text=status_text)

    def on_header_click(self, col):
        if self.sort_col == col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col = col
            self.sort_desc = False
        
        for c in Config.DISPLAY_COLUMNS:
            text = c
            if c == self.sort_col:
                text += " ▼" if self.sort_desc else " ▲"
            self.tree.heading(c, text=text)
        self.refresh_ui()

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        item = selected[0]
        values = self.tree.item(item, "values")
        req_no = values[0]
        status = self.dm.get_status_by_req_no(req_no)

        if status in ["생산 접수", "대기", "중지"]:
            self.pm.open_schedule_popup(req_no)
        elif status == "생산중":
            self.pm.open_complete_popup(req_no)
        elif status == "완료": 
            self.pm.open_completed_view_popup(req_no)

    def open_calendar_popup(self):
        if not hasattr(self, "calendar_window") or not self.calendar_window.winfo_exists():
            self.calendar_window = CalendarView(self, self.dm, self.pm)
        else:
            self.calendar_window.focus()

    def open_date_range_popup(self):
        messagebox.showinfo("알림", "기간 검색 기능은 준비 중입니다.")

if __name__ == "__main__":
    app = COXProductionManager()
    app.mainloop()