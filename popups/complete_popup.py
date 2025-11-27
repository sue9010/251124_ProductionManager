from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup
from .serial_input_popup import SerialInputPopup  # [신규] 임포트


class CompletePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return
            
        self.first_row = self.target_rows.iloc[0]
        self.current_status = str(self.first_row.get("Status", ""))
        
        super().__init__(parent, data_manager, refresh_callback, title=f"생산 완료 처리 - 번호 [{req_no}]", geometry="850x700", req_no=req_no)
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame
        
        # --- 상단 정보 (기존과 동일) ---
        file_path = self.first_row.get("파일경로", "-")
        common_info = {
            "업체명": self.first_row.get("업체명", "-"),
            "출고요청일": self.first_row.get("출고요청일", "-"),
            "출고예정일": self.first_row.get("출고예정일", "-"),
            "기타요청사항": self.first_row.get("기타요청사항", "-"),
            "특이사항": self.first_row.get("업체별 특이사항", "-")
        }

        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        header_line = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_line, text=f"생산 완료 처리 (번호: {self.req_no})", font=FONTS["title"]).pack(side="left")

        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")
        self._add_hold_button(header_line, self.req_no, self.current_status)

        grid_frame = ctk.CTkFrame(info_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)
        self._add_grid_item(grid_frame, "출고예정일", common_info["출고예정일"], 1, 0)
        self._add_grid_item(grid_frame, "특이사항", common_info["특이사항"], 1, 1)

        # --- [변경] 품목 리스트 및 상세 입력 버튼 ---
        ctk.CTkLabel(parent, text="품목별 상세 정보 입력 (시리얼 관리)", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(parent, height=250, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 데이터 저장소 (모델명 -> 시리얼 데이터 리스트)
        # 초기화 시 DM에서 기존 데이터가 있다면 불러와야 함은 SerialInputPopup 내부에서 처리하거나,
        # 여기서 미리 로드할 수도 있음. SerialInputPopup에서 로드하는게 더 깔끔.
        self.model_rows = []

        for idx, row in self.target_rows.iterrows():
            model = row.get('모델명')
            detail = row.get('상세')
            qty = row.get('수량', 0)
            
            card = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"])
            card.pack(fill="x", pady=5, padx=5)

            # 좌측 정보
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            ctk.CTkLabel(left, text=f"[{model}] {detail}", font=FONTS["main_bold"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"수량: {qty}개", font=FONTS["main"], text_color=COLORS["warning"]).pack(anchor="w")

            # 우측 버튼
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=10, pady=10)
            
            # 현재 입력된 개수 확인
            saved_count = len(self.dm.get_serial_list(self.req_no, model))
            
            status_lbl = ctk.CTkLabel(right, text=f"입력됨: {saved_count}/{qty}", font=FONTS["small"], text_color=COLORS["text_dim"])
            status_lbl.pack(side="left", padx=10)
            
            btn = ctk.CTkButton(right, text="상세 입력", width=100, 
                                command=lambda m=model, q=qty, l=status_lbl: self.open_serial_popup(m, q, l))
            btn.pack(side="left")

        # --- 하단 공통 정보 (출고일, 메모) ---
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(footer, text="출고일:").pack(side="left", padx=(0, 5))
        self.e_date = ctk.CTkEntry(footer, width=120)
        self.e_date.pack(side="left", padx=(0, 20))
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(footer, text="생산팀 메모:").pack(side="left", padx=(0, 5))
        self.e_memo = ctk.CTkEntry(footer, width=250)
        self.e_memo.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        # 기존 메모값 불러오기
        old_memo = self.first_row.get("생산팀 메모", "")
        if old_memo and str(old_memo) != "-":
            self.e_memo.delete(0, "end")
            self.e_memo.insert(0, str(old_memo))

        ctk.CTkButton(footer, text="최종 완료 처리", command=self.save_all, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], width=150).pack(side="right")
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], width=80).pack(side="right", padx=(0, 5))

    def open_serial_popup(self, model, qty, status_label):
        # 콜백 함수: 팝업에서 저장을 누르면 호출됨
        def on_save_callback(model_name, data_list):
            self.dm.update_serial_list(self.req_no, model_name, data_list)
            # 라벨 업데이트
            current_len = len(data_list)
            status_label.configure(text=f"입력됨: {current_len}/{qty}")
            # 시각적 피드백 (다 채우면 초록색 등)
            if current_len >= int(qty):
                status_label.configure(text_color=COLORS["success"])
            else:
                status_label.configure(text_color=COLORS["warning"])

        # 상세 입력 팝업 열기
        SerialInputPopup(self, self.dm, self.req_no, model, qty, on_save_callback)

    def save_all(self):
        # 모든 시리얼 정보는 이미 팝업에서 update_serial_list를 통해 메모리(DM)에 반영됨.
        # 여기서는 최종 상태 변경 및 엑셀 저장만 트리거하면 됨.
        
        # [검증] 모든 품목에 대해 시리얼이 입력되었는지 확인하려면 여기서 체크 가능
        # (현재는 강제하지 않고 진행)
        
        if messagebox.askyesno("완료 처리", "모든 데이터를 저장하고 '생산 완료' 처리하시겠습니까?"):
            try:
                # 상태 업데이트 및 엑셀 저장
                success, msg = self.dm.finalize_production(self.req_no, self.e_date.get(), self.e_memo.get())
                
                if success:
                    messagebox.showinfo("성공", "생산 완료 처리되었습니다.", parent=self)
                    self.destroy()
                    self.refresh_callback()
                else:
                    messagebox.showerror("실패", msg, parent=self)
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류: {e}", parent=self)