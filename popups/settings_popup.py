# popups/settings_popup.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .base_popup import BasePopup
from styles import COLORS, FONTS

class SettingsPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback):
        super().__init__(parent, data_manager, refresh_callback, title="환경 설정", geometry="500x200")
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="엑셀 파일 경로 설정", font=FONTS["header"]).pack(pady=(20, 10), padx=20, anchor="w")

        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)

        self.path_entry = ctk.CTkEntry(path_frame, width=350)
        self.path_entry.insert(0, self.dm.current_excel_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(path_frame, text="찾기", width=60, command=self.browse, fg_color=COLORS["bg_light"]).pack(side="right")
        ctk.CTkButton(self, text="저장 및 적용", command=self.save, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(pady=30)

    def browse(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    def save(self):
        new_path = self.path_entry.get()
        if new_path:
            try:
                self.dm.save_config(new_path)
                messagebox.showinfo("설정 저장", "파일 경로가 저장되었습니다.")
                self.destroy()
                self.dm.load_config() # 변경된 설정 즉시 반영
            except Exception as e:
                messagebox.showerror("오류", f"설정 저장 실패: {e}")
