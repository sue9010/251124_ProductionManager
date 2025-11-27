# popups/settings_popup.py
from tkinter import filedialog, messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup


class SettingsPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback):
        # 높이를 늘려서 테마 설정 영역 확보 (500x300)
        super().__init__(parent, data_manager, refresh_callback, title="환경 설정", geometry="500x300")
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame

        # 1. 테마 설정 섹션 (신규 추가)
        ctk.CTkLabel(parent, text="테마 설정 (Appearance)", font=FONTS["header"]).pack(pady=(20, 10), padx=20, anchor="w")
        
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20)
        
        # 현재 테마값으로 초기화
        self.theme_var = ctk.StringVar(value=self.dm.current_theme)
        
        # Light / Dark 전환 스위치 (Segmented Button)
        self.theme_switch = ctk.CTkSegmentedButton(
            theme_frame, 
            values=["Light", "Dark"], 
            variable=self.theme_var,
            command=self.change_theme,
            font=FONTS["main_bold"],
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

        self.path_entry = ctk.CTkEntry(path_frame, width=350)
        self.path_entry.insert(0, self.dm.current_excel_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(path_frame, text="찾기", width=60, command=self.browse, fg_color=COLORS["bg_light"]).pack(side="right")
        
        # 3. 하단 저장 버튼
        ctk.CTkButton(parent, text="설정 저장 및 닫기", command=self.save, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="bottom", pady=20)

    def change_theme(self, new_theme):
        """테마 즉시 변경 (저장 전 미리보기 효과)"""
        ctk.set_appearance_mode(new_theme)

    def browse(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    def save(self):
        new_path = self.path_entry.get()
        new_theme = self.theme_var.get()
        
        if new_path:
            try:
                # 경로와 테마 모두 저장
                self.dm.save_config(new_path, new_theme)
                messagebox.showinfo("설정 저장", "설정이 저장되었습니다.")
                self.destroy()
                
                # 엑셀 경로 재로드 및 뷰 갱신
                self.dm.load_config() 
                self.refresh_callback()
            except Exception as e:
                messagebox.showerror("오류", f"설정 저장 실패: {e}")