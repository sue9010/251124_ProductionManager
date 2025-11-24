# popups/complete_popup.py
import customtkinter as ctk
from tkinter import messagebox
from .base_popup import BasePopup
from datetime import datetime

class CompletePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return
            
        self.first_row = self.target_rows.iloc[0]
        self.current_status = str(self.first_row.get("Status", ""))
        
        super().__init__(parent, data_manager, refresh_callback, title=f"생산 완료 처리 - 번호 [{req_no}]", geometry="800x800")
        self.create_widgets()

    def create_widgets(self):
        file_path = self.first_row.get("파일경로", "-")

        common_info = {
            "업체명": self.first_row.get("업체명", "-"),
            "기타요청사항": self.first_row.get("기타요청사항", "-"),
            "업체별 특이사항": self.first_row.get("업체별 특이사항", "-"),
            "출고요청일": self.first_row.get("출고요청일", "-"),
            "출고예정일": self.first_row.get("출고예정일", "-") 
        }

        # 상단 정보
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        # 헤더 라인
        header_line = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header_line, text=f"생산 완료 처리 (번호: {self.req_no})", font=("Malgun Gothic", 20, "bold")).pack(side="left")

        # [버튼 배치: 오른쪽부터 순서대로]
        # 1. PDF 버튼
        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color="#E04F5F", hover_color="#C0392B",
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")

        # 2. Hold 버튼
        self._add_hold_button(header_line, self.req_no, self.current_status)

        grid_frame = ctk.CTkFrame(info_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="x")

        # --- 그리드 배치 ---
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)

        ctk.CTkLabel(grid_frame, text="출고예정일", font=("Malgun Gothic", 12, "bold"), text_color="#3B8ED0").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        expected_date_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        expected_date_frame.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.lbl_expected_date = ctk.CTkLabel(expected_date_frame, text=str(common_info["출고예정일"]), font=("Malgun Gothic", 12), text_color="white")
        self.lbl_expected_date.pack(side="left")

        ctk.CTkButton(expected_date_frame, text="변경", width=50, height=24, font=("Malgun Gothic", 11), fg_color="#555555", hover_color="#333333", command=self.open_change_date_popup).pack(side="left", padx=10)

        self._add_grid_item(grid_frame, "기타요청사항", common_info["기타요청사항"], 2, 0)
        self._add_grid_item(grid_frame, "업체별 특이사항", common_info["업체별 특이사항"], 2, 1)

        # 품목 리스트
        ctk.CTkLabel(self, text="품목별 상세 정보 입력", font=("Malgun Gothic", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(self, height=300, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.entry_widgets = []

        for idx, row in self.target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color="#333333")
            card.pack(fill="x", pady=5, padx=5)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            ctk.CTkLabel(left, text=f"[{row.get('모델명')}] {row.get('상세')}", font=("Malgun Gothic", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"수량: {row.get('수량')}", font=("Malgun Gothic", 12), text_color="yellow").pack(anchor="w")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=10, pady=10)
            
            e_serial = ctk.CTkEntry(right, width=150, placeholder_text="시리얼 번호")
            e_serial.pack(side="left", padx=5)
            if row.get("시리얼번호") and str(row.get("시리얼번호")) != '-': e_serial.insert(0, str(row.get("시리얼번호")))

            e_lens = ctk.CTkEntry(right, width=120, placeholder_text="렌즈 업체")
            e_lens.pack(side="left", padx=5)
            if row.get("렌즈업체") and str(row.get("렌즈업체")) != '-': e_lens.insert(0, str(row.get("렌즈업체")))

            self.entry_widgets.append({"index": idx, "serial_w": e_serial, "lens_w": e_lens})

        # 하단 입력
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(footer, text="출고일:").pack(side="left", padx=(0, 5))
        self.e_date = ctk.CTkEntry(footer, width=120)
        self.e_date.pack(side="left", padx=(0, 20))
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(footer, text="생산팀 메모:").pack(side="left", padx=(0, 5))
        self.e_memo = ctk.CTkEntry(footer, width=250)
        self.e_memo.pack(side="left", fill="x", expand=True, padx=(0, 20))

        ctk.CTkButton(footer, text="입력 완료 및 저장", command=self.save, fg_color="#2CC985", hover_color="#26AB71", width=150, height=40).pack(side="right")

    def open_change_date_popup(self):
        self._open_change_date_input(self.req_no, self.lbl_expected_date.cget("text"), parent=self)

    def save(self):
        try:
            data_to_update = []
            for item in self.entry_widgets:
                data_to_update.append({
                    "index": item["index"],
                    "serial": item["serial_w"].get(),
                    "lens": item["lens_w"].get()
                })
            
            success, msg = self.dm.update_production_complete(data_to_update, self.e_date.get(), self.e_memo.get())
            if success:
                messagebox.showinfo("성공", "생산 완료 및 출고 처리가 되었습니다.", parent=self)
                self.destroy()
                self.refresh_callback()
            else:
                messagebox.showerror("실패", msg, parent=self)

        except Exception as e:
            messagebox.showerror("오류", f"저장 중 오류: {e}", parent=self)
