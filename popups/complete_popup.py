from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup
from .serial_input_popup import SerialInputPopup


class CompletePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            # 여기서는 창이 생성되기 전이므로 parent(메인윈도우) 기준으로 메시지를 띄움
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return
            
        self.first_row = self.target_rows.iloc[0]
        self.current_status = str(self.first_row.get("Status", ""))
        
        super().__init__(parent, data_manager, refresh_callback, title=f"생산 완료 처리 - 번호 [{req_no}]", geometry="850x700", req_no=req_no)
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame
        
        # --- 상단 정보 ---
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
            # PDF 보기 버튼: BasePopup의 메서드 사용 시에도 Z-order 이슈가 있을 수 있어 래핑 필요하나, 
            # 일단 메인 기능(완료 처리) 위주로 수정
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._safe_open_pdf(file_path)).pack(side="right")
        
        self._add_hold_button(header_line, self.req_no, self.current_status)

        grid_frame = ctk.CTkFrame(info_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)
        self._add_grid_item(grid_frame, "출고예정일", common_info["출고예정일"], 1, 0)
        self._add_grid_item(grid_frame, "특이사항", common_info["특이사항"], 1, 1)

        # --- 품목 리스트 및 상세 입력 버튼 ---
        ctk.CTkLabel(parent, text="품목별 상세 정보 입력 (시리얼 관리)", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(parent, height=250, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

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

        # --- 하단 공통 정보 ---
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(footer, text="출고일:").pack(side="left", padx=(0, 5))
        self.e_date = ctk.CTkEntry(footer, width=120)
        self.e_date.pack(side="left", padx=(0, 20))
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(footer, text="생산팀 메모:").pack(side="left", padx=(0, 5))
        self.e_memo = ctk.CTkEntry(footer, width=250)
        self.e_memo.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        old_memo = self.first_row.get("생산팀 메모", "")
        if old_memo and str(old_memo) != "-":
            self.e_memo.delete(0, "end")
            self.e_memo.insert(0, str(old_memo))

        ctk.CTkButton(footer, text="최종 완료 처리", command=self.save_all, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], width=150).pack(side="right")
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], width=80).pack(side="right", padx=(0, 5))

    def _safe_open_pdf(self, path):
        # 메시지 박스 띄울 때 Topmost 임시 해제
        self.attributes("-topmost", False)
        self._open_pdf_file(path)
        self.attributes("-topmost", True)

    def open_serial_popup(self, model, qty, status_label):
        def on_save_callback(model_name, data_list):
            self.dm.update_serial_list(self.req_no, model_name, data_list)
            current_len = len(data_list)
            status_label.configure(text=f"입력됨: {current_len}/{qty}")
            if current_len >= int(qty):
                status_label.configure(text_color=COLORS["success"])
            else:
                status_label.configure(text_color=COLORS["warning"])

        # 상세 입력 팝업은 Toplevel이므로 자동으로 위에 뜸 (Transient 설정됨)
        # 하지만 혹시 모르니 이 팝업의 topmost를 잠시 꺼둘 필요는 없음 (입력 팝업이 이 팝업 위에 뜨므로)
        SerialInputPopup(self, self.dm, self.req_no, model, qty, on_save_callback)

    def save_all(self):
        # [핵심 수정] 메시지 박스가 팝업 뒤에 숨지 않도록 Topmost 잠시 해제
        self.attributes("-topmost", False)
        
        answer = messagebox.askyesno("완료 처리", "모든 데이터를 저장하고 '생산 완료' 처리하시겠습니까?", parent=self)
        
        # 메시지 박스가 닫히면 일단 다시 Topmost 복구 (취소했을 경우를 대비)
        self.attributes("-topmost", True)
        
        if answer:
            try:
                success, msg = self.dm.finalize_production(self.req_no, self.e_date.get(), self.e_memo.get())
                
                if success:
                    # 성공 메시지 띄울 때도 Topmost 해제 필요
                    self.attributes("-topmost", False)
                    messagebox.showinfo("성공", "생산 완료 처리되었습니다.", parent=self)
                    self.destroy()
                    self.refresh_callback()
                else:
                    self.attributes("-topmost", False)
                    messagebox.showerror("실패", msg, parent=self)
                    self.attributes("-topmost", True)
                    
            except Exception as e:
                self.attributes("-topmost", False)
                messagebox.showerror("오류", f"저장 중 오류: {e}", parent=self)
                self.attributes("-topmost", True)