import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

# 드래그 앤 드롭 라이브러리 임포트
try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("⚠️ tkinterdnd2 라이브러리가 설치되지 않았습니다. 드래그 앤 드롭 기능이 제한됩니다.")

from config import Config
from data_manager import DataManager
from popup_manager import PopupManager
from styles import COLORS, FONT_FAMILY, FONTS
# 뷰 임포트
from views.calendar_view import CalendarView
from views.dashboard import DashboardView  # [신규] 임포트
from views.gantt_view import GanttView
from views.kanban_view import KanbanView
from views.table_view import TableView

# TkinterDnD.DnDWrapper 상속 (DnD 기능 활성화)
if DND_AVAILABLE:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class BaseApp(ctk.CTk):
        pass

class COXProductionManager(BaseApp):
    def __init__(self):
        super().__init__()

        # 1. 모듈 초기화 (설정을 먼저 불러와야 함) - [수정] 순서 변경: 가장 먼저 실행
        self.dm = DataManager()

        # 2. 기본 설정
        self.title(f"COX Production Manager - v{Config.APP_VERSION}")
        self.geometry("1650x900")
        
        # 저장된 테마 불러와서 적용
        ctk.set_appearance_mode(self.dm.current_theme)
        ctk.set_default_color_theme("dark-blue")
        
        # 종료 시 호출할 함수 연결
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 팝업 매니저 초기화
        self.pm = PopupManager(self, self.dm, self.refresh_current_view)

        self.current_view = None

        # 3. 레이아웃 (좌: 사이드바, 우: 컨텐츠)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 4. UI 생성
        self.create_sidebar()
        self.create_content_area()
        
        # 전역 클릭 이벤트 (드롭다운 닫기용)
        self.bind("<Button-1>", self.handle_global_click)

        # 5. 초기화
        self.load_data_initial()
        
        # [수정] 시작 시 대시보드 뷰 표시
        self.show_dashboard_view()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        logo = ctk.CTkLabel(self.sidebar_frame, text="Production Manager", font=("Emoji", 24, "bold"), text_color=COLORS["primary"])
        logo.pack(pady=(30, 20), padx=20, anchor="w")
        
        # [신규] 로고 클릭 시 대시보드로 이동 (커서 변경 효과 추가)
        logo.bind("<Button-1>", lambda e: self.show_dashboard_view())
        logo.bind("<Enter>", lambda e: logo.configure(cursor="hand2"))
        logo.bind("<Leave>", lambda e: logo.configure(cursor=""))
        
        self.nav_buttons = {}
        # [수정] 대시보드 버튼 추가
        btn_data = [
            ("🏠  대시보드", self.show_dashboard_view),
            ("📊  테이블 뷰", self.show_table_view),
            ("📅  생산 달력", self.show_calendar_view),
            ("📋  칸반 보드", self.show_kanban_view),
            ("📈  간트 차트", self.show_gantt_view),
        ]

        for text, cmd in btn_data:
            btn = ctk.CTkButton(
                self.sidebar_frame, text=text, command=cmd,
                height=45, anchor="w", fg_color="transparent", 
                text_color=COLORS["text_dim"], hover_color=COLORS["bg_medium"], font=FONTS["header"]
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[text] = btn

        # 하단 버튼
        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20, padx=10, side="bottom")
        ctk.CTkButton(self.sidebar_frame, text="⚙️  설정", command=self.pm.open_settings, height=40, anchor="w", fg_color="transparent", text_color=COLORS["text_dim"], hover_color=COLORS["bg_medium"], font=FONTS["header"]).pack(fill="x", padx=10, pady=5, side="bottom")
        ctk.CTkButton(self.sidebar_frame, text="🔄  데이터 로드", command=self.reload_all_data, height=40, anchor="w", fg_color=COLORS["bg_medium"], text_color=COLORS["text"], hover_color=COLORS["bg_light"], font=FONTS["header"]).pack(fill="x", padx=10, pady=10, side="bottom")

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # 뷰 인스턴스 생성
        # [신규] 대시보드 인스턴스 추가
        self.view_dashboard = DashboardView(self.content_frame, self.dm, self.pm)
        self.view_table = TableView(self.content_frame, self.dm, self.pm)
        self.view_calendar = CalendarView(self.content_frame, self.dm, self.pm)
        self.view_kanban = KanbanView(self.content_frame, self.dm, self.pm)
        self.view_gantt = GanttView(self.content_frame, self.dm, self.pm)

    def switch_view(self, view_name, view_instance):
        # [✅ 수정] 뷰를 전환하기 전에 테이블 뷰의 드롭다운이 열려있다면 닫습니다.
        if hasattr(self, 'view_table') and self.view_table.is_dropdown_open:
            self.view_table.close_dropdown()
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
        
        # 데이터 리프레시
        if hasattr(view_instance, "refresh_data"):
            view_instance.refresh_data()

    # [신규] 대시보드 뷰 전환 함수
    def show_dashboard_view(self):
        self.switch_view("🏠  대시보드", self.view_dashboard)

    def show_table_view(self):
        self.switch_view("📊  테이블 뷰", self.view_table)

    def show_calendar_view(self):
        self.switch_view("📅  생산 달력", self.view_calendar)

    def show_kanban_view(self):
        self.switch_view("📋  칸반 보드", self.view_kanban)

    def show_gantt_view(self):
        self.switch_view("📈  간트 차트", self.view_gantt)

    def reload_all_data(self):
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
        if self.current_view == self.view_table:
            if self.view_table.is_dropdown_open:
                x, y = event.x_root, event.y_root
                dd = self.view_table.dropdown_frame
                btn = self.view_table.filter_dropdown_btn
                
                dd_x, dd_y = dd.winfo_rootx(), dd.winfo_rooty()
                dd_w, dd_h = dd.winfo_width(), dd.winfo_height()
                
                btn_x, btn_y = btn.winfo_rootx(), btn.winfo_rooty()
                btn_w, btn_h = btn.winfo_width(), btn.winfo_height()

                in_dd = (dd_x <= x <= dd_x + dd_w) and (dd_y <= y <= dd_y + dd_h)
                in_btn = (btn_x <= x <= btn_x + btn_w) and (btn_y <= y <= btn_y + btn_h)

                if not in_dd and not in_btn:
                    self.view_table.close_dropdown()

    def on_closing(self):
        self.quit()    # 메인루프 중단
        self.destroy() # 위젯 파괴

if __name__ == "__main__":
    app = COXProductionManager()
    app.mainloop()