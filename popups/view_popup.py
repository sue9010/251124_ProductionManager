# popups/view_popup.py
import customtkinter as ctk
from tkinter import messagebox
from .base_popup import BasePopup
from styles import COLORS, FONTS

class ViewPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        self.row0 = self.target_rows.iloc[0]
        self.current_status = str(self.row0.get("Status", ""))
        
        super().__init__(parent, data_manager, refresh_callback, title=f"출고 완료 상세 정보 - 번호 [{req_no}]", geometry="900x650")
        self.create_widgets()

    def create_widgets(self):
        file_path = self.row0.get("파일경로", "-")

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        header_line = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header_line, text=f"출고 완료 상세 정보 (번호: {self.req_no})", font=FONTS["title"]).pack(side="left")

        # [버튼 배치]
        # 1. PDF 버튼
        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")
        
        # 2. Hold 버튼 (완료 상태에서도 Hold 가능하도록)
        self._add_hold_button(header_line, self.req_no, self.current_status)

        grid_frame = ctk.CTkFrame(header_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")

        common_items = [
            ("업체명", self.row0.get("업체명", "-")),
            ("Status", self.row0.get("Status", "-")),
            ("출고요청일", self.row0.get("출고요청일", "-")),
            ("출고예정일", self.row0.get("출고예정일", "-")),
            ("출고일", self.row0.get("출고일", "-")),
            ("생산팀 메모", self.row0.get("생산팀 메모", "-")),
            ("기타요청사항", self.row0.get("기타요청사항", "-")),
            ("업체별 특이사항", self.row0.get("업체별 특이사항", "-"))
        ]

        for i, (label, value) in enumerate(common_items):
            r = i // 2
            c = (i % 2) * 2
            ctk.CTkLabel(
                grid_frame, 
                text=label, 
                font=FONTS["main_bold"], 
                text_color=COLORS["primary"]
            ).grid(row=r, column=c, padx=15, pady=8, sticky="w")
            
            ctk.CTkLabel(
                grid_frame, 
                text=str(value), 
                font=FONTS["main"],
                text_color=COLORS["text"]
            ).grid(row=r, column=c+1, padx=15, pady=8, sticky="w")

        ctk.CTkLabel(self, text="품목별 상세 정보", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(10, 5))

        scroll_frame = ctk.CTkScrollableFrame(self, height=350, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for idx, row in self.target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=6)
            card.pack(fill="x", pady=5, padx=5)

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=15, pady=10)

            model_info = f"[{row.get('모델명')}] {row.get('상세')}"
            ctk.CTkLabel(content, text=model_info, font=FONTS["main_bold"]).pack(anchor="w")

            details_frame = ctk.CTkFrame(content, fg_color="transparent")
            details_frame.pack(fill="x", pady=(5, 0))
            
            infos = [
                f"수량: {row.get('수량')}",
                f"시리얼: {row.get('시리얼번호')}",
                f"렌즈: {row.get('렌즈업체')}"
            ]
            
            for info in infos:
                ctk.CTkLabel(
                    details_frame, 
                    text=info, 
                    font=FONTS["main"], 
                    fg_color=COLORS["border"], 
                    corner_radius=4
                ).pack(side="left", padx=(0, 10), ipadx=5)

        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(pady=20)

        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"]).pack(side="left", padx=5)
        ctk.CTkButton(footer_frame, text="요청 삭제", command=self.delete_entry, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=5)

    def delete_entry(self):
        """요청 번호에 해당하는 데이터를 삭제합니다."""
        if messagebox.askyesno("삭제 확인", f"정말로 요청 번호 [{self.req_no}]의 모든 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.", parent=self):
            success, msg = self.dm.delete_request(self.req_no)
            if success:
                messagebox.showinfo("삭제 완료", "데이터가 성공적으로 삭제되었습니다.", parent=self.master)
                self.destroy()
                self.refresh_callback()
            else:
                messagebox.showerror("삭제 실패", msg, parent=self)
