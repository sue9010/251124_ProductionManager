# popups/schedule_popup.py
import customtkinter as ctk
from tkinter import messagebox
from .base_popup import BasePopup
from datetime import datetime

class SchedulePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]
        
        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        self.first_row = self.target_rows.iloc[0]
        self.current_status = str(self.first_row.get("Status", ""))

        title = f"생산 일정 수립 - 번호 [{req_no}]"
        if self.current_status == "Hold":
            title = f"생산 재개 (Hold 해제) - 번호 [{req_no}]"

        super().__init__(parent, data_manager, refresh_callback, title=title, geometry="800x600")
        self.create_widgets()

    def create_widgets(self):
        file_path = self.first_row.get("파일경로", "-") 

        common_info = {
            "업체명": self.first_row.get("업체명", "-"),
            "기타요청사항": self.first_row.get("기타요청사항", "-"),
            "업체별 특이사항": self.first_row.get("업체별 특이사항", "-"),
            "출고요청일": self.first_row.get("출고요청일", "-"),
        }

        # 상단 정보 프레임
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)

        # 헤더 라인 (제목 + 버튼들)
        header_line = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))
        
        title_text = f"생산 일정 수립 (번호: {self.req_no})"
        if self.current_status == "Hold":
            title_text = f"생산 재개 (번호: {self.req_no})"
            
        ctk.CTkLabel(header_line, text=title_text, font=("Malgun Gothic", 20, "bold")).pack(side="left")
        
        # [배치 순서 중요: Right로 Pack 할 때 먼저 한게 제일 오른쪽]
        # 1. 제일 오른쪽: PDF 보기 버튼
        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color="#E04F5F", hover_color="#C0392B",
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")
        
        # 2. 그 왼쪽: Hold / 재개 버튼
        self._add_hold_button(header_line, self.req_no, self.current_status)

        # 3. 그 왼쪽: 생산대기 버튼 (팝업 오픈)
        ctk.CTkButton(header_line, text="생산 대기", width=80, fg_color="#E04F5F", hover_color="#C0392B", 
                      command=self.open_waiting_reason_popup).pack(side="right", padx=(0, 5))


        grid_frame = ctk.CTkFrame(info_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="x")

        # --- 그리드 배치 ---
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)
        self._add_grid_item(grid_frame, "기타요청사항", common_info["기타요청사항"], 1, 0)
        self._add_grid_item(grid_frame, "업체별 특이사항", common_info["업체별 특이사항"], 1, 1)

        # 품목 리스트
        ctk.CTkLabel(self, text="품목 리스트", font=("Malgun Gothic", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(self, height=200, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for idx, row in self.target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color="#333333")
            card.pack(fill="x", pady=5, padx=5)
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            ctk.CTkLabel(left, text=f"[{row.get('모델명')}] {row.get('상세')}", font=("Malgun Gothic", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"수량: {row.get('수량')}", font=("Malgun Gothic", 12), text_color="yellow").pack(anchor="w")

        # 하단 입력
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(footer, text="출고예정일:", font=("Malgun Gothic", 14, "bold")).pack(side="left", padx=(0, 10))
        
        self.date_entry = ctk.CTkEntry(footer, width=200, placeholder_text="yyyy-mm-dd")
        self.date_entry.pack(side="left", padx=(0, 20))
        
        # 기존 예정일이 있으면 채워넣기
        old_expected = self.first_row.get("출고예정일", "")
        if old_expected and str(old_expected) != "-":
             self.date_entry.insert(0, str(old_expected))
        else:
             self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        btn_text = "일정 등록 (생산 시작)"
        if self.current_status == "Hold":
            btn_text = "일정 재등록 및 생산 시작"
            
        ctk.CTkButton(footer, text=btn_text, command=self.confirm, fg_color="#3B8ED0", hover_color="#36719F").pack(side="right", padx=(5,0))
        
        # 삭제 버튼 추가
        ctk.CTkButton(footer, text="요청 삭제", command=self.delete_entry, fg_color="#E04F5F", hover_color="#C0392B").pack(side="right", padx=(0,0))
        

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

    def open_waiting_reason_popup(self):
        # 사유 입력을 위한 작은 팝업 생성
        reason_window = ctk.CTkToplevel(self)
        reason_window.title("생산 대기 설정")
        reason_window.geometry("400x200")
        reason_window.attributes("-topmost", True)
        
        ctk.CTkLabel(reason_window, text="대기 사유를 입력하세요.", font=("Malgun Gothic", 14, "bold")).pack(pady=(20, 10))
        
        e_reason = ctk.CTkEntry(reason_window, width=300)
        e_reason.pack(pady=5)
        e_reason.focus_set()
        
        def submit_reason():
            reason_text = e_reason.get().strip()
            if not reason_text:
                messagebox.showwarning("경고", "대기 사유를 입력해주세요.", parent=reason_window)
                return
            
            # 데이터 매니저를 통해 저장 (성공/실패 확인)
            success, msg = self.dm.update_status_to_waiting(self.req_no, reason_text)
            if success:
                messagebox.showinfo("성공", "상태가 '대기'로 변경되었습니다.", parent=reason_window)
                reason_window.destroy()
                self.destroy()
                self.refresh_callback() # 메인 화면 갱신
            else:
                messagebox.showerror("실패", msg, parent=reason_window)
        
        btn_frame = ctk.CTkFrame(reason_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="확인", command=submit_reason, fg_color="#3B8ED0", hover_color="#36719F", width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="취소", command=reason_window.destroy, fg_color="#555555", hover_color="#333333", width=80).pack(side="left", padx=5)

    def confirm(self):
        date_str = self.date_entry.get()
        if len(date_str) != 10:
            messagebox.showwarning("경고", "날짜 형식을 확인해주세요 (yyyy-mm-dd)", parent=self)
            return
        
        try:
            success, msg = self.dm.update_production_schedule(self.req_no, date_str)
            if success:
                messagebox.showinfo("성공", "생산 일정이 등록/수정 되었습니다.", parent=self)
                self.destroy()
                self.refresh_callback() # 메인 화면 갱신
            else:
                messagebox.showerror("실패", msg, parent=self)
        except Exception as e:
            messagebox.showerror("오류", f"오류 발생: {e}", parent=self)
