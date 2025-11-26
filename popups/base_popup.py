# popups/base_popup.py
import os
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

from styles import COLORS, FONTS


class BasePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, title="Popup", geometry="800x600", req_no=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.req_no = req_no

        self.title(title)
        
        # geometry 문자열 파싱
        try:
            w_str, h_str = geometry.split('x')
            base_width = int(w_str)
            base_height = int(h_str)
        except:
            base_width, base_height = 800, 600

        # 사이드바가 있으면 너비를 늘림
        SIDEBAR_WIDTH = 320
        total_width = base_width + SIDEBAR_WIDTH if req_no else base_width

        self.center_window(total_width, base_height)
        self.attributes("-topmost", True)

        # 메인 컨테이너 (그리드 레이아웃)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        if req_no:
            # 사이드바 모드: 2열 구조
            self.main_container.grid_columnconfigure(0, weight=1) # 컨텐츠
            self.main_container.grid_columnconfigure(1, weight=0, minsize=SIDEBAR_WIDTH) # 사이드바
            self.main_container.grid_rowconfigure(0, weight=1)

            # 1. 컨텐츠 프레임 (자식 클래스들이 위젯을 넣을 곳)
            self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            self.content_frame.grid(row=0, column=0, sticky="nsew")

            # 2. 메모 사이드바 프레임
            self.sidebar_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS["bg_medium"], corner_radius=0, width=SIDEBAR_WIDTH)
            self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
            self.sidebar_frame.grid_propagate(False) # 크기 고정

            self._create_memo_sidebar()
        else:
            # 일반 모드 (SettingsPopup 등)
            self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            self.content_frame.pack(fill="both", expand=True)

        # ESC 키로 창 닫기
        self.bind("<Escape>", self.close)

    def close(self, event=None):
        """창을 닫습니다."""
        self.destroy()

    def center_window(self, width, height):
        """화면 중앙에 윈도우를 배치하는 함수"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    # ----------------------------------------------------------------
    # Memo Sidebar Logic
    # ----------------------------------------------------------------
    def _create_memo_sidebar(self):
        # Header
        header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="작업 메모", font=FONTS["header"], text_color=COLORS["text"]).pack(side="left")

        # Memo List Area
        self.memo_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.memo_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Input Area
        input_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 20), side="bottom")

        self.memo_entry = ctk.CTkTextbox(input_frame, height=60, font=FONTS["main"], fg_color=COLORS["bg_dark"], border_color=COLORS["border"], border_width=1)
        self.memo_entry.pack(fill="x", pady=(0, 5))
        
        # Shift+Enter로 줄바꿈, Enter로 전송 (바인딩)
        self.memo_entry.bind("<Return>", self._handle_enter_key)

        btn_add = ctk.CTkButton(input_frame, text="메모 등록", height=30, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], command=self._add_memo)
        btn_add.pack(fill="x")

        self._refresh_memo_list()

    def _handle_enter_key(self, event):
        if event.state & 0x0001: # Shift key pressed
            return # 기본 줄바꿈 동작 허용
        else:
            self._add_memo()
            return "break" # 기본 엔터 동작 방지

    def _add_memo(self):
        text = self.memo_entry.get("1.0", "end").strip()
        if not text:
            return

        success, msg = self.dm.add_memo(self.req_no, text)
        if success:
            self.memo_entry.delete("1.0", "end")
            self._refresh_memo_list()
        else:
            messagebox.showerror("오류", f"메모 저장 실패: {msg}", parent=self)

    def _refresh_memo_list(self):
        # 기존 위젯 제거
        for widget in self.memo_scroll.winfo_children():
            widget.destroy()

        memos = self.dm.get_memos(self.req_no)
        
        if not memos:
            ctk.CTkLabel(self.memo_scroll, text="등록된 메모가 없습니다.", text_color=COLORS["text_dim"], font=FONTS["small"]).pack(pady=20)
            return

        for memo in memos:
            self._create_memo_item(memo)

    def _create_memo_item(self, memo):
        card = ctk.CTkFrame(self.memo_scroll, fg_color=COLORS["bg_dark"], corner_radius=6)
        card.pack(fill="x", pady=5, padx=5)

        # Header: Date | User (PC)
        header_text = f"{memo['일시']} | {memo['작업자']} ({memo['PC정보']})"
        ctk.CTkLabel(card, text=header_text, font=("Malgun Gothic", 12), text_color=COLORS["text_dim"]).pack(anchor="w", padx=10, pady=(8, 2))

        # Content
        content_lbl = ctk.CTkLabel(card, text=memo['내용'], font=FONTS["main"], text_color=COLORS["text"], wraplength=260, justify="left")
        content_lbl.pack(anchor="w", padx=10, pady=(0, 8))

    # ----------------------------------------------------------------
    # Common Helpers
    # ----------------------------------------------------------------
    def _open_pdf_file(self, path):
        """주어진 경로의 파일을 시스템 기본 프로그램으로 엽니다."""
        if not path or str(path).strip() == "-" or str(path).strip() == "":
            messagebox.showinfo("알림", "등록된 파일 경로가 없습니다.", parent=self)
            return
        
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("에러", f"파일을 여는 중 오류가 발생했습니다.\n{e}", parent=self)
        else:
            messagebox.showerror("에러", f"파일을 찾을 수 없습니다.\n경로: {path}", parent=self)

    def _add_hold_button(self, parent_frame, req_no, current_status):
        if current_status == "중지":
            def resume_production():
                self._open_resume_production_popup(req_no)
                    
            ctk.CTkButton(parent_frame, text="생산 재개", width=80, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                          command=resume_production).pack(side="right", padx=(0, 5))
        else:
            def set_hold():
                if messagebox.askyesno("중지 설정", f"번호 [{req_no}]를 중지 상태로 변경하시겠습니까?", parent=self):
                    success, msg = self.dm.update_status_to_hold(req_no)
                    if success:
                        self.refresh_callback()
                        self.destroy()
                    else:
                        messagebox.showerror("실패", msg, parent=self)

            ctk.CTkButton(parent_frame, text="중지", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], 
                          command=set_hold).pack(side="right", padx=(0, 5))

    def _add_grid_item(self, parent, label, value, r, c):
        real_c = c * 2
        ctk.CTkLabel(parent, text=label, font=FONTS["main_bold"], text_color=COLORS["primary"]).grid(row=r, column=real_c, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(parent, text=str(value), font=FONTS["main"], text_color=COLORS["text"]).grid(row=r, column=real_c+1, padx=10, pady=5, sticky="w")

    def _open_change_date_input(self, req_no, current_date, parent=None):
        master = parent if parent else self
        win = ctk.CTkToplevel(master)
        win.transient(master) 
        win.title("출고예정일 변경")
        
        width, height = 300, 150
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.attributes("-topmost", True)
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(win, text="새로운 출고예정일을 입력하세요.", font=FONTS["main"]).pack(pady=(20, 10))
        
        entry = ctk.CTkEntry(win, width=150)
        entry.pack(pady=5)
        entry.insert(0, current_date if current_date != '-' else datetime.now().strftime("%Y-%m-%d"))
        
        def confirm():
            new_date = entry.get()
            if not new_date: return
            
            success, msg = self.dm.update_expected_date(req_no, new_date)
            if success:
                if hasattr(self, 'lbl_expected_date'):
                    self.lbl_expected_date.configure(text=new_date)
                self.refresh_callback()
                win.destroy()
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="변경 저장", command=confirm, fg_color=COLORS["primary"], width=100).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def _open_resume_production_popup(self, req_no):
        win = ctk.CTkToplevel(self)
        win.transient(self) 
        win.title("생산 재개")
        
        width, height = 350, 180
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.attributes("-topmost", True)
        win.bind("<Escape>", lambda e: win.destroy())
        
        ctk.CTkLabel(win, text=f"번호 [{req_no}] 생산을 재개합니다.\n새로운 출고예정일을 입력하세요.", font=FONTS["main"]).pack(pady=(20, 10))
        
        entry = ctk.CTkEntry(win, width=150)
        entry.pack(pady=5)
        entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        def confirm():
            new_date = entry.get()
            if not new_date:
                messagebox.showwarning("입력 오류", "날짜를 입력해주세요.", parent=win)
                return

            success, msg = self.dm.update_status_resume(req_no, new_date)
            if success:
                self.refresh_callback()
                win.destroy()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="저장 및 생산 재개", command=confirm, fg_color=COLORS["primary"], width=120).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def create_widgets(self):
        raise NotImplementedError