# popups/view_popup.py
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup
from .serial_input_popup import SerialInputPopup  # [신규] SerialInputPopup 임포트


class ViewPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        self.row0 = self.target_rows.iloc[0]
        self.current_status = str(self.row0.get("Status", ""))
        
        # [수정] req_no 전달
        super().__init__(parent, data_manager, refresh_callback, title=f"출고 완료 상세 정보 - 번호 [{req_no}]", geometry="900x650", req_no=req_no)
        self.create_widgets()

    def create_widgets(self):
        # [수정] self.content_frame 사용
        parent = self.content_frame

        file_path = self.row0.get("파일경로", "-")

        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        header_line = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header_line, text=f"출고 완료 상세 정보 (번호: {self.req_no})", font=FONTS["title"]).pack(side="left")

        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")
        
        self._add_hold_button(header_line, self.req_no, self.current_status)

        grid_frame = ctk.CTkFrame(header_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")

        common_items = [
            ("업체명", self.row0.get("업체명", "-")),
            ("Status", self.row0.get("Status", "-")),
            ("출고요청일", self.row0.get("출고요청일", "-")),
            ("출고예정일", self.row0.get("출고예정일", "-")),
            ("출고일", self.row0.get("출고일", "-")),
            # [수정] 생산팀 메모 표시 제거
            # ("생산팀 메모", self.row0.get("생산팀 메모", "-")),
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

        ctk.CTkLabel(parent, text="품목별 상세 정보", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(10, 5))

        scroll_frame = ctk.CTkScrollableFrame(parent, height=350, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for idx, row in self.target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=6)
            card.pack(fill="x", pady=5, padx=5)

            # 카드 내용을 담을 프레임 (좌측)
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(side="left", fill="both", expand=True, padx=15, pady=10)

            model_name = row.get('모델명')
            qty = row.get('수량')
            model_info = f"[{model_name}] {row.get('상세')}"
            ctk.CTkLabel(content, text=model_info, font=FONTS["main_bold"]).pack(anchor="w")

            # 상세 정보 레이아웃
            top_info_frame = ctk.CTkFrame(content, fg_color="transparent")
            top_info_frame.pack(fill="x", pady=(5, 0))
            
            infos_top = [
                f"수량: {qty}",
                f"렌즈: {row.get('렌즈업체')}"
            ]
            
            for info in infos_top:
                ctk.CTkLabel(
                    top_info_frame, 
                    text=info, 
                    font=FONTS["main"], 
                    fg_color=COLORS["border"], 
                    corner_radius=4
                ).pack(side="left", padx=(0, 10), ipadx=5)

            serial_text = f"시리얼: {row.get('시리얼번호')}"
            ctk.CTkLabel(
                content, 
                text=serial_text, 
                font=FONTS["main"], 
                fg_color=COLORS["border"], 
                corner_radius=4,
                wraplength=650,  # 버튼 공간 확보를 위해 길이 조정
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=(5, 0), ipadx=5)

            # [신규] 우측 버튼 프레임
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            # [수정] anchor="ne"를 추가하여 버튼을 우측 상단으로 이동
            btn_frame.pack(side="right", anchor="ne", padx=10, pady=10)

            ctk.CTkButton(
                btn_frame, 
                text="상세 보기", 
                width=80, 
                height=30,
                fg_color=COLORS["bg_light"], 
                hover_color=COLORS["bg_light_hover"],
                text_color=COLORS["text"],
                command=lambda m=model_name, q=qty: self.open_serial_popup(m, q)
            ).pack()

        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(pady=20)

        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"]).pack(side="left", padx=5)
        ctk.CTkButton(footer_frame, text="요청 삭제", command=self.delete_entry, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=5)

    def delete_entry(self):
        if messagebox.askyesno("삭제 확인", f"정말로 요청 번호 [{self.req_no}]의 모든 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.", parent=self):
            success, msg = self.dm.delete_request(self.req_no)
            if success:
                messagebox.showinfo("삭제 완료", "데이터가 성공적으로 삭제되었습니다.", parent=self.master)
                self.destroy()
                self.refresh_callback()
            else:
                messagebox.showerror("삭제 실패", msg, parent=self)

    # [신규] 상세 보기 팝업 오픈 메서드
    def open_serial_popup(self, model, qty):
        popup = None

        # ViewPopup에서는 데이터 수정 후 UI 갱신이 필요 없으므로 빈 콜백 전달 (혹은 재조회 로직 추가 가능)
        def on_save_callback(model_name, data_list):
            # [수정] 알림창이 가려지는 현상 방지를 위해 팝업들의 Topmost 속성 잠시 해제
            if popup:
                popup.attributes("-topmost", False)
            self.attributes("-topmost", False)

            # 1. 데이터 매니저 업데이트 (메모리 상) - Serial_Data 및 Data 시트(시리얼/렌즈 컬럼) 동기화
            self.dm.update_serial_list(self.req_no, model_name, data_list)
            
            # 2. 엑셀 파일에 즉시 저장 (Data 시트 반영을 위해 필수)
            success, msg = self.dm.save_to_excel()
            
            # 메시지 박스의 부모를 현재 조작 중인 팝업(popup)으로 설정하여 그 위에 뜨게 함
            target_parent = popup if popup else self

            if success:
                # 3. 성공 시 메인 뷰 갱신 및 팝업 닫기
                if self.refresh_callback:
                    self.refresh_callback()
                messagebox.showinfo("저장 완료", "수정된 내용이 저장되었습니다.", parent=target_parent)
                self.destroy()
            else:
                messagebox.showerror("저장 실패", msg, parent=target_parent)
                
                # 실패 시에는 창이 닫히지 않으므로 Topmost 속성 복구
                if popup:
                    popup.attributes("-topmost", True)
                self.attributes("-topmost", True)

        popup = SerialInputPopup(self, self.dm, self.req_no, model, qty, on_save_callback)