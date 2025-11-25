import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from config import Config
from data_manager import DataManager
from popup_manager import PopupManager
from styles import COLORS, FONTS
from views.calendar_view import CalendarView
from views.kanban_view import KanbanView
# views 패키지에서 뷰 가져오기
from views.table_view import TableView


class COXProductionManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 기본 설정
        self.title(f"COX Production Manager - v{Config.APP_VERSION}")
        self.geometry("1650x900")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # 2. 모듈 초기화
        self.dm = DataManager()
        # [변경] PopupManager 콜백은 현재 활성화된 뷰의 리프레시를 호출하도록 수정 필요
        # 임시로 self.refresh_current_view 연결
        self.pm = PopupManager(self, self.dm, self.refresh_current_view)

        self.current_view = None

        # 3. 레이아웃 (좌: 사이드바, 우: 컨텐츠)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 4. UI 생성
        self.create_sidebar()
        self.create_content_area()
        
        # 전역 클릭 이벤트 (드롭다운 닫기용) - TableView의 로직을 호출
        self.bind("<Button-1>", self.handle_global_click)

        # 5. 초기화
        self.load_data_initial()
        self.show_table_view()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        logo = ctk.CTkLabel(self.sidebar_frame, text="🏭 COX PM", font=("Emoji", 24, "bold"), text_color=COLORS["primary"])
        logo.pack(pady=(30, 10), padx=20, anchor="w")
        
        ctk.CTkLabel(self.sidebar_frame, text=f"v{Config.APP_VERSION}", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(pady=(0, 30), padx=20, anchor="w")

        self.nav_buttons = {}
        btn_data = [
            ("📊  테이블 뷰", self.show_table_view),
            ("📅  생산 달력", self.show_calendar_view),
            ("📋  칸반 보드", self.show_kanban_view),
            ("📈  간트 차트", self.show_gantt_view),
        ]

        for text, cmd in btn_data:
            btn = ctk.CTkButton(
                self.sidebar_frame, text=text, command=cmd,
                height=45, anchor="w", fg_color="transparent", 
                text_color=COLORS["text_dim"], hover_color=COLORS["bg_medium"], font=FONTS["main_bold"]
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[text] = btn

        # 하단 버튼
        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20, padx=10, side="bottom")
        ctk.CTkButton(self.sidebar_frame, text="⚙️  설정", command=self.pm.open_settings, height=40, anchor="w", fg_color="transparent", text_color=COLORS["text_dim"], hover_color=COLORS["bg_medium"]).pack(fill="x", padx=10, pady=5, side="bottom")
        ctk.CTkButton(self.sidebar_frame, text="🔄  데이터 로드", command=self.reload_all_data, height=40, anchor="w", fg_color=COLORS["bg_medium"], text_color=COLORS["text"], hover_color=COLORS["bg_light"]).pack(fill="x", padx=10, pady=10, side="bottom")

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # 뷰 인스턴스 생성 (미리 생성해두고 pack/forget으로 전환)
        self.view_table = TableView(self.content_frame, self.dm, self.pm)
        self.view_calendar = CalendarView(self.content_frame, self.dm, self.pm)
        self.view_kanban = KanbanView(self.content_frame, self.dm, self.pm)

    def switch_view(self, view_name, view_instance):
        # 버튼 스타일 업데이트
        for text, btn in self.nav_buttons.items():
            if text == view_name:
                btn.configure(fg_color=COLORS["bg_light"], text_color=COLORS["text"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_dim"])
        
        # 화면 전환
        for child in self.content_frame.winfo_children():
            child.pack_forget()
        
        view_instance.pack(fill="both", expand=True)
        self.current_view = view_instance
        
        # 데이터 리프레시 (선택 사항)
        if hasattr(view_instance, "refresh_data"):
            view_instance.refresh_data()

    def show_table_view(self):
        self.switch_view("📊  테이블 뷰", self.view_table)

    def show_calendar_view(self):
        self.switch_view("📅  생산 달력", self.view_calendar)

    def show_kanban_view(self):
        # [수정됨] messagebox 제거하고 정상적으로 화면 전환 호출
        self.switch_view("📋  칸반 보드", self.view_kanban)

    def show_gantt_view(self):
        messagebox.showinfo("준비중", "간트 차트는 개발 중입니다.")

    def reload_all_data(self):
        """전체 데이터 다시 로드 및 현재 뷰 갱신"""
        success, msg = self.dm.load_data()
        if success:
            messagebox.showinfo("완료", "데이터를 새로고침했습니다.")
            self.refresh_current_view()
        else:
            messagebox.showerror("오류", msg)

    def load_data_initial(self):
        self.dm.load_data()

    def refresh_current_view(self):
        if self.current_view and hasattr(self.current_view, "refresh_data"):
            self.current_view.refresh_data()

    def handle_global_click(self, event):
        """Table View의 드롭다운을 닫기 위한 전역 이벤트 핸들러"""
        # 현재 뷰가 테이블 뷰일 때만 전달
        if self.current_view == self.view_table:
            # 간단하게: 드롭다운이 열려있으면, 클릭된 위젯이 드롭다운이 아닐 때 닫음
            if self.view_table.is_dropdown_open:
                # 클릭 좌표
                x, y = event.x_root, event.y_root
                dd = self.view_table.dropdown_frame
                btn = self.view_table.filter_dropdown_btn
                
                # 드롭다운 영역 확인
                dd_x = dd.winfo_rootx()
                dd_y = dd.winfo_rooty()
                dd_w = dd.winfo_width()
                dd_h = dd.winfo_height()
                
                # 버튼 영역 확인
                btn_x = btn.winfo_rootx()
                btn_y = btn.winfo_rooty()
                btn_w = btn.winfo_width()
                btn_h = btn.winfo_height()

                in_dd = (dd_x <= x <= dd_x + dd_w) and (dd_y <= y <= dd_y + dd_h)
                in_btn = (btn_x <= x <= btn_x + btn_w) and (btn_y <= y <= btn_y + btn_h)

                if not in_dd and not in_btn:
                    self.view_table.close_dropdown()

if __name__ == "__main__":
    app = COXProductionManager()
    app.mainloop()