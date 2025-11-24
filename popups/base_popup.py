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
        self.geometry(geometry)
        self.attributes("-topmost", True)

        # Helper to store entry widgets for later processing
        self.entry_widgets = []

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
                if messagebox.askyesno("생산 재개", f"번호 [{req_no}]의 생산을 재개하시겠습니까?\n(상태가 '생산중'으로 변경됩니다.)", parent=self):
                    success, msg = self.dm.update_status_resume(req_no)
                    if success:
                        self.refresh_callback()
                        self.destroy()
                    else:
                        messagebox.showerror("실패", msg, parent=self)
                    
            ctk.CTkButton(parent_frame, text="생산 재개", width=80, fg_color="#3B8ED0", hover_color="#36719F",
                          command=resume_production).pack(side="right", padx=(0, 5))
        else:
            def set_hold():
                if messagebox.askyesno("Hold 설정", f"번호 [{req_no}]를 Hold 상태로 변경하시겠습니까?", parent=self):
                    success, msg = self.dm.update_status_to_hold(req_no)
                    if success:
                        self.refresh_callback()
                        self.destroy()
                    else:
                        messagebox.showerror("실패", msg, parent=self)

            ctk.CTkButton(parent_frame, text="Hold", width=60, fg_color="#E04F5F", hover_color="#C0392B", 
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
        win.geometry("300x150")
        win.lift()
        win.attributes("-topmost", True)
        
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

    def create_widgets(self):
        # This method should be overridden by subclasses
        raise NotImplementedError
