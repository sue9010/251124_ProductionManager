import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime

class PopupManager:
    def __init__(self, parent, data_manager, refresh_callback):
        self.parent = parent  # 메인 윈도우 (부모)
        self.dm = data_manager # 데이터 매니저 인스턴스
        self.refresh_callback = refresh_callback # 작업 완료 후 메인 UI 갱신 함수

    # ---------------------------------------------------------
    # 1. 환경 설정 팝업
    # ---------------------------------------------------------
    def open_settings(self):
        window = ctk.CTkToplevel(self.parent)
        window.title("환경 설정")
        window.geometry("500x200")
        window.attributes("-topmost", True)

        ctk.CTkLabel(window, text="엑셀 파일 경로 설정", font=("Malgun Gothic", 14, "bold")).pack(pady=(20, 10), padx=20, anchor="w")

        path_frame = ctk.CTkFrame(window, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)

        path_entry = ctk.CTkEntry(path_frame, width=350)
        path_entry.insert(0, self.dm.current_excel_path)
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def browse():
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
            if file_path:
                path_entry.delete(0, "end")
                path_entry.insert(0, file_path)

        ctk.CTkButton(path_frame, text="찾기", width=60, command=browse).pack(side="right")

        def save():
            new_path = path_entry.get()
            if new_path:
                try:
                    self.dm.save_config(new_path)
                    messagebox.showinfo("설정 저장", "파일 경로가 저장되었습니다.")
                    window.destroy()
                    self.dm.load_config() # 변경된 설정 즉시 반영
                except Exception as e:
                    messagebox.showerror("오류", f"설정 저장 실패: {e}")

        ctk.CTkButton(window, text="저장 및 적용", command=save, fg_color="#2CC985", hover_color="#26AB71").pack(pady=30)

    # ---------------------------------------------------------
    # 2. 생산 일정 수립 팝업 (생산 접수 -> 생산중)
    # ---------------------------------------------------------
    def open_schedule_popup(self, req_no):
        target_rows = self.dm.df[self.dm.df["번호"].astype(str) == str(req_no)]
        if target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        first_row = target_rows.iloc[0]
        common_info = {
            "업체명": first_row.get("업체명", "-"),
            "기타요청사항": first_row.get("기타요청사항", "-"),
            "업체별 특이사항": first_row.get("업체별 특이사항", "-"),
            "출고요청일": first_row.get("출고요청일", "-"),
        }

        popup = ctk.CTkToplevel(self.parent)
        popup.title(f"생산 일정 수립 - 번호 [{req_no}]")
        popup.geometry("800x600")
        popup.attributes("-topmost", True)

        # 상단 정보
        info_frame = ctk.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(info_frame, text=f"생산 일정 수립 (번호: {req_no})", font=("Malgun Gothic", 20, "bold")).pack(anchor="w", pady=(0, 10))

        grid_frame = ctk.CTkFrame(info_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="x")

        # --- 그리드 배치 ---
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)
        self._add_grid_item(grid_frame, "기타요청사항", common_info["기타요청사항"], 1, 0)
        self._add_grid_item(grid_frame, "업체별 특이사항", common_info["업체별 특이사항"], 1, 1)

        # 품목 리스트
        ctk.CTkLabel(popup, text="품목 리스트", font=("Malgun Gothic", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(popup, height=200, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for idx, row in target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color="#333333")
            card.pack(fill="x", pady=5, padx=5)
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            ctk.CTkLabel(left, text=f"[{row.get('모델명')}] {row.get('상세')}", font=("Malgun Gothic", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"수량: {row.get('수량')}", font=("Malgun Gothic", 12), text_color="yellow").pack(anchor="w")

        # 하단 입력
        footer = ctk.CTkFrame(popup, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(footer, text="출고예정일:", font=("Malgun Gothic", 14, "bold")).pack(side="left", padx=(0, 10))
        
        date_entry = ctk.CTkEntry(footer, width=200, placeholder_text="yyyy-mm-dd")
        date_entry.pack(side="left", padx=(0, 20))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        def confirm():
            date_str = date_entry.get()
            if len(date_str) != 10:
                messagebox.showwarning("경고", "날짜 형식을 확인해주세요 (yyyy-mm-dd)", parent=popup)
                return
            
            try:
                if self.dm.update_production_schedule(req_no, date_str):
                    messagebox.showinfo("성공", "생산 일정이 등록되었습니다.", parent=popup)
                    popup.destroy()
                    self.refresh_callback() # 메인 화면 갱신
                else:
                    messagebox.showerror("오류", "해당 번호의 데이터를 찾을 수 없습니다.", parent=popup)
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류: {e}", parent=popup)

        ctk.CTkButton(footer, text="일정 등록 (생산 시작)", command=confirm, fg_color="#2CC985", hover_color="#26AB71", height=40).pack(side="right", padx=(20,0))

    # ---------------------------------------------------------
    # 3. 생산 완료 처리 팝업 (생산중 -> 완료)
    # ---------------------------------------------------------
    def open_complete_popup(self, req_no):
        target_rows = self.dm.df[self.dm.df["번호"].astype(str) == str(req_no)]
        if target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        first_row = target_rows.iloc[0]
        common_info = {
            "업체명": first_row.get("업체명", "-"),
            "기타요청사항": first_row.get("기타요청사항", "-"),
            "업체별 특이사항": first_row.get("업체별 특이사항", "-"),
            "출고요청일": first_row.get("출고요청일", "-"),
            "출고예정일": first_row.get("출고예정일", "-") 
        }

        popup = ctk.CTkToplevel(self.parent)
        popup.title(f"생산 완료 처리 - 번호 [{req_no}]")
        popup.geometry("800x800")
        popup.attributes("-topmost", True)

        # 상단 정보
        info_frame = ctk.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(info_frame, text=f"생산 완료 처리 (번호: {req_no})", font=("Malgun Gothic", 20, "bold")).pack(anchor="w", pady=(0, 10))

        grid_frame = ctk.CTkFrame(info_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="x")

        # --- 그리드 배치 ---
        # 1. 업체명 / 출고요청일 (Row 0)
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)

        # 2. 출고예정일 (Row 1) - [변경] 버튼 포함
        ctk.CTkLabel(grid_frame, text="출고예정일", font=("Malgun Gothic", 12, "bold"), text_color="#3B8ED0").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        expected_date_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        expected_date_frame.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.lbl_expected_date = ctk.CTkLabel(expected_date_frame, text=str(common_info["출고예정일"]), font=("Malgun Gothic", 12), text_color="white")
        self.lbl_expected_date.pack(side="left")

        # [변경] 버튼
        def open_change_date_popup():
            # [핵심 수정] 현재 열려있는 popup을 부모(parent)로 지정하여 전달
            self._open_change_date_input(req_no, self.lbl_expected_date.cget("text"), parent=popup)

        ctk.CTkButton(expected_date_frame, text="변경", width=50, height=24, font=("Malgun Gothic", 11), fg_color="#555555", hover_color="#333333", command=open_change_date_popup).pack(side="left", padx=10)

        # 3. 기타요청사항 / 업체별 특이사항 (Row 2)
        self._add_grid_item(grid_frame, "기타요청사항", common_info["기타요청사항"], 2, 0)
        self._add_grid_item(grid_frame, "업체별 특이사항", common_info["업체별 특이사항"], 2, 1)

        # 품목 리스트
        ctk.CTkLabel(popup, text="품목별 상세 정보 입력", font=("Malgun Gothic", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(popup, height=300, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        entry_widgets = []

        for idx, row in target_rows.iterrows():
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

            entry_widgets.append({"index": idx, "serial_w": e_serial, "lens_w": e_lens})

        # 하단 입력
        footer = ctk.CTkFrame(popup, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(footer, text="출고일:").pack(side="left", padx=(0, 5))
        e_date = ctk.CTkEntry(footer, width=120)
        e_date.pack(side="left", padx=(0, 20))
        e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(footer, text="생산팀 메모:").pack(side="left", padx=(0, 5))
        e_memo = ctk.CTkEntry(footer, width=250)
        e_memo.pack(side="left", fill="x", expand=True, padx=(0, 20))

        def save():
            try:
                data_to_update = []
                for item in entry_widgets:
                    data_to_update.append({
                        "index": item["index"],
                        "serial": item["serial_w"].get(),
                        "lens": item["lens_w"].get()
                    })
                
                self.dm.update_production_complete(data_to_update, e_date.get(), e_memo.get())
                
                messagebox.showinfo("성공", "생산 완료 및 출고 처리가 되었습니다.", parent=popup)
                popup.destroy()
                self.refresh_callback()
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류: {e}", parent=popup)

        ctk.CTkButton(footer, text="입력 완료 및 저장", command=save, fg_color="#2CC985", hover_color="#26AB71", width=150, height=40).pack(side="right")

    def _add_grid_item(self, parent, label, value, r, c):
        """그리드에 라벨과 값을 추가하는 헬퍼 메서드"""
        real_c = c * 2
        ctk.CTkLabel(parent, text=label, font=("Malgun Gothic", 12, "bold"), text_color="#3B8ED0").grid(row=r, column=real_c, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(parent, text=str(value), font=("Malgun Gothic", 12), text_color="white").grid(row=r, column=real_c+1, padx=10, pady=5, sticky="w")

    def _open_change_date_input(self, req_no, current_date, parent=None):
        """출고예정일 변경을 위한 작은 팝업"""
        master = parent if parent else self.parent
        win = ctk.CTkToplevel(master)
        
        # [핵심 수정] transient를 사용하여 master 창 위에 고정
        win.transient(master) 
        
        win.title("출고예정일 변경")
        win.geometry("300x150")
        
        # [핵심 수정] lift()로 창을 최상단으로 올리고 topmost 설정
        win.lift()
        win.attributes("-topmost", True)
        
        ctk.CTkLabel(win, text="새로운 출고예정일을 입력하세요.", font=("Malgun Gothic", 12)).pack(pady=(20, 10))
        
        entry = ctk.CTkEntry(win, width=150)
        entry.pack(pady=5)
        entry.insert(0, current_date if current_date != '-' else datetime.now().strftime("%Y-%m-%d"))
        
        def confirm():
            new_date = entry.get()
            if not new_date: return
            
            # DB 업데이트
            self.dm.update_expected_date(req_no, new_date)
            
            # 현재 열려있는 팝업의 라벨 업데이트
            if hasattr(self, 'lbl_expected_date'):
                self.lbl_expected_date.configure(text=new_date)
            
            # 메인 리스트 갱신
            self.refresh_callback()
            
            win.destroy()
            
        ctk.CTkButton(win, text="변경 저장", command=confirm, fg_color="#3B8ED0", width=100).pack(pady=10)
        
        # 팝업에 포커스 강제 이동
        win.focus_force() 
        entry.focus_set()

    # ---------------------------------------------------------
    # 4. 완료 데이터 상세 조회 팝업 (완료 -> 조회)
    # ---------------------------------------------------------
    def open_completed_view_popup(self, req_no):
        target_rows = self.dm.df[self.dm.df["번호"].astype(str) == str(req_no)]
        if target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        # 첫 번째 행에서 공통 정보 추출
        row0 = target_rows.iloc[0]
        
        popup = ctk.CTkToplevel(self.parent)
        popup.title(f"출고 완료 상세 정보 - 번호 [{req_no}]")
        popup.geometry("900x650")
        popup.attributes("-topmost", True)

        # 1. 공통 정보 섹션 (헤더)
        header_frame = ctk.CTkFrame(popup, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(header_frame, text=f"출고 완료 상세 정보 (번호: {req_no})", font=("Malgun Gothic", 20, "bold")).pack(anchor="w", pady=(0, 10))

        # 정보 그리드 표시
        grid_frame = ctk.CTkFrame(header_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="x")

        # 표시할 공통 항목 정의
        common_items = [
            ("업체명", row0.get("업체명", "-")),
            ("Status", row0.get("Status", "-")),
            ("출고요청일", row0.get("출고요청일", "-")),
            ("출고예정일", row0.get("출고예정일", "-")),
            ("출고일", row0.get("출고일", "-")),
            ("생산팀 메모", row0.get("생산팀 메모", "-")),
            ("기타요청사항", row0.get("기타요청사항", "-")),
            ("업체별 특이사항", row0.get("업체별 특이사항", "-"))
        ]

        # 2열 그리드로 배치
        for i, (label, value) in enumerate(common_items):
            r = i // 2
            c = (i % 2) * 2
            
            # 라벨
            ctk.CTkLabel(
                grid_frame, 
                text=label, 
                font=("Malgun Gothic", 12, "bold"), 
                text_color="#3B8ED0"
            ).grid(row=r, column=c, padx=15, pady=8, sticky="w")
            
            # 값 (텍스트가 길 경우를 대비해 width 제한을 두거나 줄바꿈 고려 가능하지만 여기선 단순 라벨)
            ctk.CTkLabel(
                grid_frame, 
                text=str(value), 
                font=("Malgun Gothic", 12),
                text_color="white"
            ).grid(row=r, column=c+1, padx=15, pady=8, sticky="w")

        # 2. 품목 정보 섹션 (리스트)
        ctk.CTkLabel(popup, text="품목별 상세 정보", font=("Malgun Gothic", 14, "bold")).pack(anchor="w", padx=20, pady=(10, 5))

        scroll_frame = ctk.CTkScrollableFrame(popup, height=350, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for idx, row in target_rows.iterrows():
            # 카드 프레임
            card = ctk.CTkFrame(scroll_frame, fg_color="#333333", corner_radius=6)
            card.pack(fill="x", pady=5, padx=5)

            # 내용 컨테이너
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=15, pady=10)

            # 모델명 & 상세 (강조)
            model_info = f"[{row.get('모델명')}] {row.get('상세')}"
            ctk.CTkLabel(content, text=model_info, font=("Malgun Gothic", 14, "bold")).pack(anchor="w")

            # 세부 속성 (한 줄에 배치하거나 여러 줄 배치)
            details_frame = ctk.CTkFrame(content, fg_color="transparent")
            details_frame.pack(fill="x", pady=(5, 0))
            
            # 수량, 시리얼, 렌즈
            infos = [
                f"수량: {row.get('수량')}",
                f"시리얼: {row.get('시리얼번호')}",
                f"렌즈: {row.get('렌즈업체')}"
            ]
            
            for info in infos:
                ctk.CTkLabel(
                    details_frame, 
                    text=info, 
                    font=("Malgun Gothic", 12), 
                    fg_color="#444444", # 뱃지 느낌 배경
                    corner_radius=4
                ).pack(side="left", padx=(0, 10), ipadx=5)

        # 닫기 버튼
        ctk.CTkButton(popup, text="닫기", command=popup.destroy, fg_color="#555555", hover_color="#333333").pack(pady=20)