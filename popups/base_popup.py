import os
import re
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("Warning: tkinterdnd2 library not found. Drag and drop will not work.")

from styles import COLORS, FONT_FAMILY, FONTS


class BasePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, title="Popup", geometry="800x600", req_no=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.req_no = req_no

        self.title(title)
        
        try:
            w_str, h_str = geometry.split('x')
            base_width = int(w_str)
            base_height = int(h_str)
        except:
            base_width, base_height = 800, 600

        SIDEBAR_WIDTH = 320
        total_width = base_width + SIDEBAR_WIDTH if req_no else base_width

        self.center_window(total_width, base_height)
        self.attributes("-topmost", True)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        if req_no:
            self.main_container.grid_columnconfigure(0, weight=1) 
            self.main_container.grid_columnconfigure(1, weight=0, minsize=SIDEBAR_WIDTH) 
            self.main_container.grid_rowconfigure(0, weight=1)

            self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            self.content_frame.grid(row=0, column=0, sticky="nsew")

            self.sidebar_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS["bg_medium"], corner_radius=0, width=SIDEBAR_WIDTH)
            self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
            self.sidebar_frame.grid_propagate(False)

            self._create_memo_sidebar()
        else:
            self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            self.content_frame.pack(fill="both", expand=True)

        self.bind("<Escape>", self.close)

    def close(self, event=None):
        self.destroy()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    # ----------------------------------------------------------------
    # Shared Helper Methods
    # ----------------------------------------------------------------
    def _add_dev_edit_button(self, parent_frame):
        """개발자 모드일 경우 정보 수정 버튼을 추가합니다."""
        if getattr(self.dm, 'is_dev_mode', False):
            ctk.CTkButton(parent_frame, text="✏️ 정보 수정", width=100, command=self.open_edit_popup, 
                          fg_color=COLORS["warning"], hover_color="#D35400").pack(side="right", padx=(0, 5))

    def open_edit_popup(self):
        """[Dev] 공통 정보 및 품목별 정보 수정 팝업"""
        if not getattr(self.dm, 'is_dev_mode', False):
            return

        target_indices = self.dm.df[self.dm.df["번호"].astype(str) == str(self.req_no)].index
        if len(target_indices) == 0:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.", parent=self)
            return
        
        first_row = self.dm.df.loc[target_indices[0]]

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"[DEV] 데이터 수정 - {self.req_no}")
        edit_win.geometry("600x700")
        edit_win.transient(self)
        edit_win.attributes("-topmost", True)
        
        container = ctk.CTkScrollableFrame(edit_win)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- A. 공통 정보 수정 섹션 ---
        ctk.CTkLabel(container, text="■ 공통 정보 (일괄 적용)", font=FONTS["header"]).pack(anchor="w", pady=(0, 10))
        
        common_fields = ["업체명", "출고요청일", "출고예정일", "출고일", "Status", "기타요청사항", "업체별 특이사항", "대기사유"]
        common_entries = {}
        
        for field in common_fields:
            row_frame = ctk.CTkFrame(container, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=field, width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row_frame, height=28)
            entry.pack(side="left", fill="x", expand=True)
            
            val = first_row.get(field, "")
            entry.insert(0, str(val))
            common_entries[field] = entry

        # --- B. 품목별 정보 수정 섹션 ---
        ctk.CTkFrame(container, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=20)
        ctk.CTkLabel(container, text="■ 품목별 상세 정보", font=FONTS["header"]).pack(anchor="w", pady=(0, 10))

        item_entries = []

        for idx in target_indices:
            row_data = self.dm.df.loc[idx]
            
            item_card = ctk.CTkFrame(container, fg_color=COLORS["bg_dark"])
            item_card.pack(fill="x", pady=5, padx=5)
            
            r1 = ctk.CTkFrame(item_card, fg_color="transparent")
            r1.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(r1, text="모델명:", width=60, anchor="w").pack(side="left")
            e_model = ctk.CTkEntry(r1, width=200)
            e_model.insert(0, str(row_data.get("모델명", "")))
            e_model.pack(side="left", fill="x", expand=True)
            
            r2 = ctk.CTkFrame(item_card, fg_color="transparent")
            r2.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(r2, text="상세:", width=60, anchor="w").pack(side="left")
            e_detail = ctk.CTkEntry(r2, width=150)
            e_detail.insert(0, str(row_data.get("상세", "")))
            e_detail.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkLabel(r2, text="수량:", width=40, anchor="w").pack(side="left")
            e_qty = ctk.CTkEntry(r2, width=60)
            e_qty.insert(0, str(row_data.get("수량", "")))
            e_qty.pack(side="left")

            item_entries.append({
                "index": idx,
                "model": e_model,
                "detail": e_detail,
                "qty": e_qty
            })
            
        def save_changes():
            new_common_data = {f: e.get() for f, e in common_entries.items()}
            
            for idx in target_indices:
                for col, val in new_common_data.items():
                    self.dm.df.loc[idx, col] = val
            
            for item in item_entries:
                idx = item["index"]
                self.dm.df.loc[idx, "모델명"] = item["model"].get()
                self.dm.df.loc[idx, "상세"] = item["detail"].get()
                
                qty_val = item["qty"].get()
                try:
                    self.dm.df.loc[idx, "수량"] = int(qty_val)
                except:
                    self.dm.df.loc[idx, "수량"] = qty_val
            
            edit_win.attributes("-topmost", False)
            self.attributes("-topmost", False)
            
            success, msg = self.dm.save_to_excel()
            
            if success:
                messagebox.showinfo("성공", "데이터가 수정되었습니다.", parent=edit_win)
                edit_win.destroy()
                self.destroy()
                if self.refresh_callback:
                    self.refresh_callback()
            else:
                messagebox.showerror("실패", msg, parent=edit_win)
                edit_win.attributes("-topmost", True)
                self.attributes("-topmost", True)

        ctk.CTkButton(edit_win, text="모든 변경사항 저장", command=save_changes, fg_color=COLORS["primary"], height=40, font=FONTS["main_bold"]).pack(pady=20, padx=20, fill="x")

    # ----------------------------------------------------------------
    # Memo Sidebar Logic
    # ----------------------------------------------------------------
    def _create_memo_sidebar(self):
        header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="작업 메모", font=FONTS["header"], text_color=COLORS["text"]).pack(side="left")

        self.memo_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.memo_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        input_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 20), side="bottom")
        
        if DND_AVAILABLE:
            guide_text = "메시지를 입력하거나 파일을 드래그하세요."
        else:
            guide_text = "메시지를 입력하세요."
            
        ctk.CTkLabel(input_frame, text=guide_text, font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(anchor="w", padx=2, pady=(0,2))

        self.memo_entry = ctk.CTkTextbox(input_frame, height=60, font=FONTS["main"], fg_color=COLORS["bg_dark"], border_color=COLORS["border"], border_width=1)
        self.memo_entry.pack(fill="x", pady=(0, 5))
        
        self.memo_entry.bind("<Return>", self._handle_enter_key)
        
        if DND_AVAILABLE:
            try:
                self.memo_entry.drop_target_register(DND_FILES)
                self.memo_entry.dnd_bind('<<Drop>>', self._on_drop_file)
            except Exception as e:
                print(f"DnD bind error: {e}")

        btn_add = ctk.CTkButton(input_frame, text="메모 등록", height=30, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], command=self._add_memo)
        btn_add.pack(fill="x")

        self._refresh_memo_list()
        
    def _on_drop_file(self, event):
        files = event.data
        if not files: return
        
        paths = re.findall(r'\{.*?\}|\S+', files)
        
        success_count = 0
        error_msg = ""

        for file_path in paths:
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            if os.path.exists(file_path):
                saved_path, error = self.dm.save_attachment(file_path)
                if saved_path:
                    current_text = self.memo_entry.get("1.0", "end").strip()
                    new_text = f"[파일첨부] {os.path.basename(saved_path)}\n(경로: {saved_path})"
                    
                    if current_text:
                        self.memo_entry.insert("end", "\n" + new_text)
                    else:
                        self.memo_entry.insert("1.0", new_text)
                    success_count += 1
                else:
                    error_msg += f"\n{os.path.basename(file_path)}: {error}"
        
        if error_msg:
             messagebox.showerror("일부 파일 저장 실패", error_msg, parent=self)

    def _handle_enter_key(self, event):
        if event.state & 0x0001: 
            return 
        else:
            self._add_memo()
            return "break" 

    def _add_memo(self):
        text = self.memo_entry.get("1.0", "end").strip()
        if not text:
            return

        success, msg = self.dm.add_memo(self.req_no, text)
        if success:
            self.memo_entry.delete("1.0", "end")
            self._refresh_memo_list()
        else:
            messagebox.showerror("오류", f"메모 저장 실패: {msg}", parent=self)

    def _refresh_memo_list(self):
        for widget in self.memo_scroll.winfo_children():
            widget.destroy()

        memos = self.dm.get_memos(self.req_no)
        
        if not memos:
            ctk.CTkLabel(self.memo_scroll, text="등록된 메모가 없습니다.", text_color=COLORS["text_dim"], font=FONTS["small"]).pack(pady=20)
            return

        for memo in memos:
            self._create_memo_item(memo)

    def _create_memo_item(self, memo):
        card = ctk.CTkFrame(self.memo_scroll, fg_color=COLORS["bg_dark"], corner_radius=6)
        card.pack(fill="x", pady=5, padx=5)

        header_frame = ctk.CTkFrame(card, fg_color="transparent", height=20)
        header_frame.pack(fill="x", padx=10, pady=(8, 2))

        header_text = f"{memo['일시']} | {memo['작업자']} ({memo['PC정보']})"
        ctk.CTkLabel(header_frame, text=header_text, font=(FONT_FAMILY, 12), text_color=COLORS["text_dim"]).pack(side="left")

        content_text = memo['내용']
        
        if "[파일첨부]" in content_text and "(경로:" in content_text:
            try:
                start_idx = content_text.find("(경로:") + 5
                end_idx = content_text.find(")", start_idx)
                file_path = content_text[start_idx:end_idx].strip()
                display_text = content_text.split('\n')[0] 
                
                btn_file = ctk.CTkButton(
                    card, 
                    text=f"📁 {display_text}", 
                    fg_color=COLORS["bg_medium"], 
                    hover_color=COLORS["bg_light"],
                    text_color=COLORS["primary"],
                    anchor="w",
                    command=lambda p=file_path: self._open_pdf_file(p) 
                )
                btn_file.pack(fill="x", padx=10, pady=(0, 0))
            except:
                content_lbl = ctk.CTkLabel(card, text=content_text, font=FONTS["main"], text_color=COLORS["text"], wraplength=260, justify="left")
                content_lbl.pack(anchor="w", padx=10, pady=(0, 0))
        else:
            content_lbl = ctk.CTkLabel(card, text=content_text, font=FONTS["main"], text_color=COLORS["text"], wraplength=260, justify="left")
            content_lbl.pack(anchor="w", padx=10, pady=(0, 0))

        footer_frame = ctk.CTkFrame(card, fg_color="transparent")
        footer_frame.pack(fill="x", padx=10, pady=(5, 8))

        btn_del = ctk.CTkButton(
            footer_frame, 
            text="×", 
            width=20, 
            height=20, 
            fg_color="transparent", 
            hover_color=COLORS["danger"], 
            text_color=COLORS["text_dim"], 
            font=(FONT_FAMILY, 16, "bold"),
            command=lambda m=memo: self._delete_memo_confirm(m)
        )
        btn_del.pack(side="right", padx=(5, 0), anchor="center")

        is_checked = str(memo.get('확인', 'N')) == 'Y'
        check_text = "✓✓" if is_checked else "✓"
        check_fg_color = COLORS["transparent"] if is_checked else "transparent"
        check_text_color = COLORS["text_dim"] if is_checked else COLORS["text_dim"]

        btn_check = ctk.CTkButton(
            footer_frame,
            text=check_text,
            width=20,
            height=20,
            fg_color=check_fg_color,
            hover_color=COLORS["bg_light_hover"] if not is_checked else COLORS["bg_light_hover"],
            text_color=check_text_color,
            font=(FONT_FAMILY, 16, "bold")
        )
        btn_check.configure(command=lambda b=btn_check, m=memo: self._toggle_check(b, m))
        btn_check.pack(side="right", anchor="center")

    def _toggle_check(self, btn, memo):
        current_status = str(memo.get('확인', 'N'))
        new_status = 'N' if current_status == 'Y' else 'Y'
        success, msg = self.dm.update_memo_check(self.req_no, memo['일시'], memo['내용'], new_status)
        if success:
            self._refresh_memo_list()
        else:
            messagebox.showerror("오류", f"상태 변경 실패: {msg}", parent=self)

    def _delete_memo_confirm(self, memo):
        if messagebox.askyesno("메모 삭제", "선택한 메모를 삭제하시겠습니까?", parent=self):
            success, msg = self.dm.delete_memo(self.req_no, memo['일시'], memo['내용'])
            if success:
                self._refresh_memo_list()
            else:
                messagebox.showerror("오류", msg, parent=self)

    def _open_pdf_file(self, path):
        if not path or str(path).strip() == "-" or str(path).strip() == "":
            messagebox.showinfo("알림", "등록된 파일 경로가 없습니다.", parent=self)
            return
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("에러", f"파일을 여는 중 오류가 발생했습니다.\n{e}", parent=self)
        else:
            messagebox.showerror("에러", f"파일을 찾을 수 없습니다.\n경로: {path}", parent=self)

    def _add_hold_button(self, parent_frame, req_no, current_status):
        if current_status == "중지":
            def resume_production():
                self._open_resume_production_popup(req_no)
                    
            ctk.CTkButton(parent_frame, text="생산 재개", width=80, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                          command=resume_production).pack(side="right", padx=(0, 5))
        else:
            def set_hold():
                if messagebox.askyesno("중지 설정", f"번호 [{req_no}]를 중지 상태로 변경하시겠습니까?", parent=self):
                    success, msg = self.dm.update_status_to_hold(req_no)
                    if success:
                        self.refresh_callback()
                        self.destroy()
                    else:
                        messagebox.showerror("실패", msg, parent=self)

            ctk.CTkButton(parent_frame, text="중지", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], 
                          command=set_hold).pack(side="right", padx=(0, 5))

    def _add_grid_item(self, parent, label, value, r, c):
        real_c = c * 2
        ctk.CTkLabel(parent, text=label, font=FONTS["main_bold"], text_color=COLORS["primary"]).grid(row=r, column=real_c, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(parent, text=str(value), font=FONTS["main"], text_color=COLORS["text"]).grid(row=r, column=real_c+1, padx=10, pady=5, sticky="w")

    def _open_change_date_input(self, req_no, current_date, parent=None):
        master = parent if parent else self
        win = ctk.CTkToplevel(master)
        win.transient(master) 
        win.title("출고예정일 변경")
        
        width, height = 300, 150
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.attributes("-topmost", True)
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(win, text="새로운 출고예정일을 입력하세요.", font=FONTS["main"]).pack(pady=(20, 10))
        
        entry = ctk.CTkEntry(win, width=150)
        entry.pack(pady=5)
        entry.insert(0, current_date if current_date != '-' else datetime.now().strftime("%Y-%m-%d"))
        
        def confirm():
            new_date = entry.get()
            if not new_date: return
            
            success, msg = self.dm.update_expected_date(req_no, new_date)
            if success:
                if hasattr(self, 'lbl_expected_date'):
                    self.lbl_expected_date.configure(text=new_date)
                self.refresh_callback()
                win.destroy()
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="변경 저장", command=confirm, fg_color=COLORS["primary"], width=100).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def _open_resume_production_popup(self, req_no):
        win = ctk.CTkToplevel(self)
        win.transient(self) 
        win.title("생산 재개")
        
        # [수정] 팝업 크기 확장
        width, height = 500, 450
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.attributes("-topmost", True)
        win.bind("<Escape>", lambda e: win.destroy())
        
        ctk.CTkLabel(win, text=f"번호 [{req_no}] 생산을 재개합니다.\n새로운 출고예정일을 입력하세요.", font=FONTS["main_bold"]).pack(pady=(20, 10))
        
        # 날짜 입력
        entry = ctk.CTkEntry(win, width=200)
        entry.pack(pady=5)
        entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # [신규] 품목 정보 및 시리얼 번호 표시 영역
        ctk.CTkLabel(win, text="품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 5))
        scroll = ctk.CTkScrollableFrame(win, height=150, corner_radius=6, fg_color=COLORS["bg_medium"])
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        target_rows = self.dm.df[self.dm.df["번호"].astype(str) == str(req_no)]
        
        for _, row in target_rows.iterrows():
            item_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            # 모델명 및 수량
            model_info = f"[{row.get('모델명')}] {row.get('상세')} ({row.get('수량')}개)"
            ctk.CTkLabel(item_frame, text=model_info, font=FONTS["main_bold"], anchor="w").pack(fill="x")
            
            # 시리얼 번호
            serials = str(row.get('시리얼번호', '')).strip()
            if serials == '-' or serials == 'nan': serials = ""
            if serials:
                ctk.CTkLabel(item_frame, text=f"S/N: {serials}", font=FONTS["small"], text_color=COLORS["text_dim"], 
                             wraplength=420, justify="left", anchor="w").pack(fill="x")

        def confirm():
            new_date = entry.get()
            if not new_date:
                messagebox.showwarning("입력 오류", "날짜를 입력해주세요.", parent=win)
                return

            success, msg = self.dm.update_status_resume(req_no, new_date)
            if success:
                self.refresh_callback()
                win.destroy()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="저장 및 생산 재개", command=confirm, fg_color=COLORS["primary"], width=150).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def create_widgets(self):
        raise NotImplementedError