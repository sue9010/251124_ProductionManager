import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter as ctk

from config import Config
from styles import COLORS, FONTS


class TableView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 로컬 상태 변수
        self.search_start_date = None
        self.search_end_date = None
        self.sort_col = None
        self.sort_desc = False
        
        # 필터 상태 (기본값)
        self.filter_states = {
            "생산 접수": True, "대기": False, "생산중": True, "중지": False, "완료": False
        }
        self.filter_check_vars = {}

        self.create_widgets()
        self.style_treeview()
        
        # 이벤트 바인딩
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # 초기 데이터 로드
        self.refresh_data()

    def create_widgets(self):
        # ===================================================
        # 1. Toolbar (상단 툴바)
        # ===================================================
        self.toolbar_wrapper = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], height=60)
        self.toolbar_wrapper.pack(side="top", fill="x", padx=20, pady=(20, 10))

        # [Left] Filter Dropdown Group
        view_frame = ctk.CTkFrame(self.toolbar_wrapper, fg_color="transparent")
        view_frame.pack(side="left")
        
        ctk.CTkLabel(view_frame, text="Filter:", font=("Malgun Gothic", 12, "bold"), text_color=COLORS["text_dim"]).pack(side="left", padx=(0, 10))

        FILTER_WIDTH = 120
        self.filter_dropdown_btn = ctk.CTkButton(
            view_frame, text="필터 선택 ▼", command=self.toggle_filter_dropdown,
            width=FILTER_WIDTH, height=34, fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            border_color=COLORS["border"], border_width=1, font=("Malgun Gothic", 12), anchor="w"
        )
        self.filter_dropdown_btn.pack(side="left")

        # Dropdown Frame (메인 윈도우에 부착하기 위해 winfo_toplevel 사용)
        self.dropdown_frame = ctk.CTkFrame(self.winfo_toplevel(), width=FILTER_WIDTH, fg_color=COLORS["bg_medium"], border_width=1, border_color=COLORS["primary"], corner_radius=5)
        self.dropdown_frame.pack_propagate(False) # 크기 고정
        
        self._init_filter_checkboxes()
        self.is_dropdown_open = False

        # [Right] Search Group
        control_frame = ctk.CTkFrame(self.toolbar_wrapper, fg_color="transparent")
        control_frame.pack(side="right")

        self.search_entry = ctk.CTkEntry(control_frame, width=220, height=34, placeholder_text="번호, 업체, 모델...", border_color=COLORS["border"], fg_color=COLORS["bg_medium"])
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh_data())

        ctk.CTkButton(
            control_frame, text="검색", command=self.refresh_data, 
            width=60, height=34, fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], 
            border_width=1, border_color=COLORS["border"]
        ).pack(side="left", padx=2)

        # ===================================================
        # 2. Treeview (중앙 리스트)
        # ===================================================
        self.tree_bg_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.tree_bg_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.tree_frame = ctk.CTkFrame(self.tree_bg_frame, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=2, pady=2)

        scroll_y = ctk.CTkScrollbar(self.tree_frame, orientation="vertical")
        self.tree = ttk.Treeview(self.tree_frame, columns=Config.DISPLAY_COLUMNS, show="headings", yscrollcommand=scroll_y.set)
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

        # ===================================================
        # 3. Dashboard (하단 정보바)
        # ===================================================
        self.dashboard_frame = ctk.CTkFrame(self, height=40, fg_color=COLORS["bg_medium"], corner_radius=0)
        self.dashboard_frame.pack(side="bottom", fill="x")
        
        self.dashboard_label = ctk.CTkLabel(self.dashboard_frame, text="Ready", font=("Malgun Gothic", 11), text_color=COLORS["text_dim"])
        self.dashboard_label.pack(side="left", padx=30, pady=8)

    # ===================================================
    # Data Logic
    # ===================================================
    def refresh_data(self):
        """현재 필터/검색 조건으로 데이터 다시 불러오기"""
        selected_statuses = [s for s, active in self.filter_states.items() if active]
        keyword = self.search_entry.get().strip()
        
        # DataManager에서 필터링된 데이터 가져오기
        filtered_df = self.dm.get_filtered_data(
            selected_statuses, keyword, 
            sort_by=self.sort_col, ascending=not self.sort_desc
        )
        
        # 트리뷰 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        today_str = datetime.now().strftime("%Y-%m-%d")

        if filtered_df is not None and not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                values = list(row[col] for col in Config.DISPLAY_COLUMNS)
                status = row['Status']
                req_date = str(row['출고요청일'])
                
                row_tags = [status]
                
                # [수정] 번개 아이콘(⚡) 제거, 배경색 강조(today 태그)는 유지
                if req_date == today_str:
                    # values[model_idx] = f"⚡ {values[model_idx]}" # 이 줄을 제거하여 아이콘 삭제
                    row_tags.append("today")
                
                self.tree.insert("", "end", values=values, tags=tuple(row_tags))
        
        self.update_dashboard(filtered_df)

    def update_dashboard(self, df):
        """하단 대시보드 갱신"""
        if df is None or df.empty or 'Status' not in df.columns:
            total, waiting, hold = 0, 0, 0
        else:
            total = len(df)
            waiting = len(df[df['Status'] == '대기'])
            hold = len(df[df['Status'].isin(['Hold', '중지', '중지'])])
            
        status_text = f"  📦 전체 항목: {total}   |   ⏳ 생산 대기: {waiting}   |   ⛔ 중지: {hold}"
        self.dashboard_label.configure(text=status_text)

    # ===================================================
    # Event Handlers
    # ===================================================
    def on_header_click(self, col):
        """헤더 클릭 시 정렬"""
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
        self.refresh_data()

    def on_double_click(self, event):
        """행 더블 클릭 시 팝업 오픈"""
        selected = self.tree.selection()
        if not selected: return
        
        item = selected[0]
        values = self.tree.item(item, "values")
        req_no = values[0]
        
        # 정확한 상태 파악을 위해 DM 조회
        status = self.dm.get_status_by_req_no(req_no)
        
        if status in ["생산 접수", "대기","중지"]:
            self.pm.open_schedule_popup(req_no)
        elif status == "생산중":
            self.pm.open_complete_popup(req_no)
        elif status == "완료":
            self.pm.open_completed_view_popup(req_no)

    # ===================================================
    # Filter Dropdown Logic (Custom)
    # ===================================================
    def _init_filter_checkboxes(self):
        # 전체 선택
        self.cb_all = ctk.CTkCheckBox(
            self.dropdown_frame, text="전체", command=self.toggle_all_filters,
            font=("Malgun Gothic", 11, "bold"), fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]
        )
        self.cb_all.pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkFrame(self.dropdown_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=5, pady=2)
        
        # 개별 상태
        for status, is_checked in self.filter_states.items():
            var = ctk.BooleanVar(value=is_checked)
            self.filter_check_vars[status] = var
            cb = ctk.CTkCheckBox(
                self.dropdown_frame, text=status, variable=var, command=self.on_filter_change,
                font=("Malgun Gothic", 11), fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]
            )
            cb.pack(anchor="w", padx=10, pady=3)
            
        # 높이 자동 조절
        item_count = len(self.filter_states)
        calc_height = 45 + (item_count * 32) + 0
        self.dropdown_frame.configure(height=calc_height)
        self.update_dropdown_btn_text()

    def toggle_filter_dropdown(self):
        if self.is_dropdown_open:
            self.dropdown_frame.place_forget()
            self.is_dropdown_open = False
        else:
            root_x = self.filter_dropdown_btn.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
            root_y = self.filter_dropdown_btn.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.filter_dropdown_btn.winfo_height() + 5
            
            self.dropdown_frame.place(x=root_x, y=root_y)
            self.dropdown_frame.lift()
            self.is_dropdown_open = True

    def close_dropdown(self):
        """외부에서 호출하여 드롭다운 닫기"""
        if self.is_dropdown_open:
            self.dropdown_frame.place_forget()
            self.is_dropdown_open = False

    def toggle_all_filters(self):
        new_state = bool(self.cb_all.get())
        for status, var in self.filter_check_vars.items():
            var.set(new_state)
            self.filter_states[status] = new_state
        self.on_filter_change()

    def on_filter_change(self):
        cnt = 0
        for status, var in self.filter_check_vars.items():
            is_checked = var.get()
            self.filter_states[status] = is_checked
            if is_checked: cnt += 1
            
        self.update_dropdown_btn_text(cnt)
        self.refresh_data()

    def update_dropdown_btn_text(self, count=None):
        if count is None: count = sum(self.filter_states.values())
        
        if count == len(self.filter_states):
            text = "전체 (All) ▼"
        elif count == 0:
            text = "선택 안함 ▼"
        else:
            text = f"선택됨 ({count}) ▼"
        self.filter_dropdown_btn.configure(text=text)

    # ===================================================
    # Styling
    # ===================================================
    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        bg_color = COLORS["bg_dark"]
        header_bg = "#3a3a3a"
        
        style.configure(
            "Treeview", background=bg_color, foreground="#eeeeee", 
            fieldbackground=bg_color, rowheight=38, font=("Malgun Gothic", 11), borderwidth=0
        )
        style.configure(
            "Treeview.Heading", background=header_bg, foreground=COLORS["primary"], 
            font=("Malgun Gothic", 12, "bold"), relief="flat", padding=(0, 8)
        )
        style.map("Treeview.Heading", background=[('active', "#444444")])
        style.map("Treeview", background=[('selected', COLORS["primary_hover"])])
        
        # 태그별 색상
        self.tree.tag_configure("중지", background="#4a2626", foreground="#ffcccc")
        self.tree.tag_configure("중지", background="#4a2626", foreground="#ffcccc")
        self.tree.tag_configure("Hold", background="#4a2626", foreground="#ffcccc")
        self.tree.tag_configure("완료", foreground="#888888")
        self.tree.tag_configure("생산중", foreground="#4caf50")
        self.tree.tag_configure("대기", foreground="#ff9800")
        
        # 당일 건 강조 (배경색만 남김)
        self.tree.tag_configure("today", background="#2c3e50")