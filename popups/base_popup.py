# popups/base_popup.py
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime


class BasePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, title="Popup", geometry="800x600"):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback

        self.title(title)

        # geometry 문자열에서 너비와 높이 추출
        width, height = map(int, geometry.split('x'))
        self.center_window(width, height)

        self.attributes("-topmost", True)

        # Helper to store entry widgets for later processing
        self.entry_widgets = []

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
        """
        헤더 영역에 Hold 또는 생산재개 버튼을 추가합니다.
        pack(side='right')를 사용하므로, PDF 버튼보다 먼저 호출해야 PDF 버튼 왼쪽에 위치합니다.
        """
        if current_status == "Hold":
            def resume_production():
                # 날짜를 입력받는 팝업을 새로 연다
                self._open_resume_production_popup(req_no)
                    
            ctk.CTkButton(parent_frame, text="생산 재개", width=80, fg_color="#3B8ED0", hover_color="#36719F",
                          command=resume_production).pack(side="right", padx=(0, 5))
        else:
        # elif current_status != "대기":
            def set_hold():
                if messagebox.askyesno("Hold 설정", f"번호 [{req_no}]를 Hold 상태로 변경하시겠습니까?", parent=self):
                    success, msg = self.dm.update_status_to_hold(req_no)
                    if success:
                        self.refresh_callback()
                        self.destroy()
                    else:
                        messagebox.showerror("실패", msg, parent=self)

            ctk.CTkButton(parent_frame, text="Hold", width=80, fg_color="#E04F5F", hover_color="#C0392B", 
                          command=set_hold).pack(side="right", padx=(0, 5))

    def _add_grid_item(self, parent, label, value, r, c):
        """그리드에 라벨과 값을 추가하는 헬퍼 메서드"""
        real_c = c * 2
        ctk.CTkLabel(parent, text=label, font=("Malgun Gothic", 12, "bold"), text_color="#3B8ED0").grid(row=r, column=real_c, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(parent, text=str(value), font=("Malgun Gothic", 12), text_color="white").grid(row=r, column=real_c+1, padx=10, pady=5, sticky="w")

    def _open_change_date_input(self, req_no, current_date, parent=None):
        """출고예정일 변경을 위한 작은 팝업"""
        master = parent if parent else self
        win = ctk.CTkToplevel(master)
        win.transient(master) 
        win.title("출고예정일 변경")
        
        # 작은 팝업 화면 중앙 배치
        width = 300
        height = 150
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.attributes("-topmost", True)
        
        # ESC 키로 창 닫기
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(win, text="새로운 출고예정일을 입력하세요.", font=("Malgun Gothic", 12)).pack(pady=(20, 10))
        
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
            
        ctk.CTkButton(win, text="변경 저장", command=confirm, fg_color="#3B8ED0", width=100).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def _open_resume_production_popup(self, req_no):
        """생산 재개를 위한 출고예정일 입력 팝업"""
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
        
        ctk.CTkLabel(win, text=f"번호 [{req_no}] 생산을 재개합니다.\n새로운 출고예정일을 입력하세요.", font=("Malgun Gothic", 12)).pack(pady=(20, 10))
        
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
                win.destroy() # 날짜 입력 팝업 닫기
                self.destroy() # 기본 팝업 (상세보기) 닫기
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="저장 및 생산 재개", command=confirm, fg_color="#3B8ED0", width=120).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def create_widgets(self):
        # This method should be overridden by subclasses
        raise NotImplementedError


class StandardPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, title="Popup", geometry="800x600"):
        super().__init__(parent, data_manager, refresh_callback, title=title, geometry=geometry)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(10, 5))

        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=20, pady=(0, 20))

    def setup_header(self, title):
        header_line = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header_line, text=title, font=("Malgun Gothic", 20, "bold")).pack(side="left")
        return header_line

    def setup_info(self, data_dict, columns=2):
        grid_frame = ctk.CTkFrame(self.info_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="x")

        for i, (label, value) in enumerate(data_dict.items()):
            r = i // columns
            c = i % columns
            self._add_grid_item(grid_frame, label, value, r, c)

        return grid_frame

    def setup_list(self, df, title="품목 리스트", height=250):
        ctk.CTkLabel(self.list_frame, text=title, font=("Malgun Gothic", 14, "bold")).pack(anchor="w", pady=(0, 5))

        scroll_frame = ctk.CTkScrollableFrame(self.list_frame, height=height, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True)
        return scroll_frame

    def setup_footer(self, buttons=None):
        footer = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        footer.pack(fill="x")

        if buttons:
            for spec in buttons:
                btn_options = spec.copy()
                text = btn_options.pop("text", "")
                command = btn_options.pop("command", None)
                ctk.CTkButton(footer, text=text, command=command, **btn_options).pack(side="right", padx=(5, 0))

        return footer
