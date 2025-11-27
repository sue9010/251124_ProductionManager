# popups/settings_popup.py
from tkinter import filedialog, messagebox

import customtkinter as ctk

from styles import COLORS, FONT_FAMILY, FONTS

from .base_popup import BasePopup


class SettingsPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback):
        # 높이를 조금 더 늘려서 첨부 파일 경로 섹션 확보 (500x300 -> 500x450)
        super().__init__(parent, data_manager, refresh_callback, title="환경 설정", geometry="500x450")
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame

        # 1. 테마 설정 섹션
        ctk.CTkLabel(parent, text="테마 설정 (Appearance)", font=FONTS["header"]).pack(pady=(20, 10), padx=20, anchor="w")
        
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20)
        
        self.theme_var = ctk.StringVar(value=self.dm.current_theme)
        
        self.theme_switch = ctk.CTkSegmentedButton(
            theme_frame, 
            values=["Light", "Dark"], 
            variable=self.theme_var,
            command=self.change_theme,
            font=(FONT_FAMILY, 12, "bold"),
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"]
        )
        self.theme_switch.pack(fill="x")

        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=20)

        # 2. 엑셀 파일 경로 설정 섹션
        ctk.CTkLabel(parent, text="엑셀 파일 경로 설정", font=FONTS["header"]).pack(pady=(0, 10), padx=20, anchor="w")

        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)

        self.path_entry = ctk.CTkEntry(path_frame, width=350, font=(FONT_FAMILY, 12))
        self.path_entry.insert(0, self.dm.current_excel_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(path_frame, text="찾기", width=60, command=self.browse_excel, fg_color=COLORS["bg_light"], font=(FONT_FAMILY, 12)).pack(side="right")
        
        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=20)

        # 3. [신규] 첨부 파일 저장 경로 설정 섹션
        ctk.CTkLabel(parent, text="첨부 파일 저장 폴더 설정", font=FONTS["header"]).pack(pady=(0, 10), padx=20, anchor="w")

        attach_frame = ctk.CTkFrame(parent, fg_color="transparent")
        attach_frame.pack(fill="x", padx=20)

        self.attach_path_entry = ctk.CTkEntry(attach_frame, width=350, font=(FONT_FAMILY, 12))
        self.attach_path_entry.insert(0, self.dm.attachment_dir)
        self.attach_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(attach_frame, text="폴더 선택", width=80, command=self.browse_folder, fg_color=COLORS["bg_light"], font=(FONT_FAMILY, 12)).pack(side="right")

        # 4. 하단 저장 버튼
        ctk.CTkButton(parent, text="설정 저장 및 닫기", command=self.save, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=(FONT_FAMILY, 12, "bold")).pack(side="bottom", pady=20)

    def change_theme(self, new_theme):
        """테마 즉시 변경"""
        ctk.set_appearance_mode(new_theme)

    def browse_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.attach_path_entry.delete(0, "end")
            self.attach_path_entry.insert(0, folder_path)

    def save(self):
        new_path = self.path_entry.get()
        new_theme = self.theme_var.get()
        new_attachment_dir = self.attach_path_entry.get()
        
        if new_path:
            try:
                # 경로와 테마, 첨부 폴더 모두 저장
                self.dm.save_config(new_path, new_theme, new_attachment_dir)
                messagebox.showinfo("설정 저장", "설정이 저장되었습니다.")
                self.destroy()
                
                # 엑셀 경로 재로드 및 뷰 갱신
                self.dm.load_config() 
                self.refresh_callback()
            except Exception as e:
                messagebox.showerror("오류", f"설정 저장 실패: {e}")