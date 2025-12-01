import getpass
import json
import os
import platform
import shutil
from datetime import datetime, timedelta

import pandas as pd

from config import Config


class DataManager:
    def __init__(self):
        self.df = pd.DataFrame()
        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS) 
        self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS)
        self.memo_log_df = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)
        # [신규] 시리얼 데이터프레임 추가
        self.serial_df = pd.DataFrame(columns=Config.SERIAL_COLUMNS)
        
        self.current_excel_path = Config.DEFAULT_EXCEL_PATH
        self.current_theme = "Dark"  
        self.attachment_dir = Config.DEFAULT_ATTACHMENT_DIR 
        
        # [신규] 개발자 모드 상태 초기화 (이 부분이 없으면 에러가 발생합니다)
        self.is_dev_mode = False
        
        self.load_config()

    def set_dev_mode(self, enabled: bool):
        """개발자 모드 상태 변경"""
        self.is_dev_mode = enabled

    # ---------------------------------------------------------
    # [개발자 모드 전용 기능]
    # ---------------------------------------------------------
    def create_backup(self):
        """현재 엑셀 파일 백업 생성"""
        if not os.path.exists(self.current_excel_path):
            return False, "원본 파일이 없습니다."
            
        try:
            # 원본 파일이 있는 폴더에 'backup' 폴더 생성
            base_dir = os.path.dirname(self.current_excel_path)
            backup_dir = os.path.join(base_dir, "backup")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(self.current_excel_path)
            name, ext = os.path.splitext(filename)
            backup_filename = f"{name}_backup_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(self.current_excel_path, backup_path)
            return True, f"백업 완료:\n{backup_path}"
        except Exception as e:
            return False, f"백업 실패: {e}"

    def clean_old_logs(self, months=3):
        """오래된 로그 정리 (기본 3개월)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=months*30)
            
            # Log 정리
            original_log_count = len(self.log_df)
            temp_log_dates = pd.to_datetime(self.log_df['일시'], errors='coerce')
            self.log_df = self.log_df[temp_log_dates >= cutoff_date]
            deleted_log = original_log_count - len(self.log_df)
            
            # Memo Log 정리
            original_memo_log_count = len(self.memo_log_df)
            temp_memo_dates = pd.to_datetime(self.memo_log_df['일시'], errors='coerce')
            self.memo_log_df = self.memo_log_df[temp_memo_dates >= cutoff_date]
            deleted_memo_log = original_memo_log_count - len(self.memo_log_df)
            
            # 변경사항 저장
            self.save_to_excel()
            
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            return True, f"로그 정리 완료 (기준일: {cutoff_str} 이전)\n- 일반 로그 삭제: {deleted_log}건\n- 메모 로그 삭제: {deleted_memo_log}건"
        except Exception as e:
            return False, f"로그 정리 실패: {e}"

    def hard_delete_request(self, req_no):
        """[Dev Only] 데이터 강제 완전 삭제 (연관 데이터 포함)"""
        if not self.is_dev_mode:
            return False, "개발자 모드가 아닙니다."

        try:
            # 1. Main Data 삭제
            mask_data = self.df["번호"].astype(str) == str(req_no)
            if not mask_data.any():
                return False, "데이터를 찾을 수 없습니다."
            
            self.df = self.df[~mask_data]
            
            # 2. Serial Data 삭제
            if not self.serial_df.empty:
                mask_serial = self.serial_df["요청번호"].astype(str) == str(req_no)
                self.serial_df = self.serial_df[~mask_serial]
                
            # 3. Memo 삭제
            if not self.memo_df.empty:
                mask_memo = self.memo_df["번호"].astype(str) == str(req_no)
                self.memo_df = self.memo_df[~mask_memo]
                
            # 4. Memo Log 삭제 -> 삭제하지 않음 (이력 보존)

            # 5. 작업 로그 남기기
            self._add_log("강제 삭제", f"[Dev] 번호[{req_no}] 및 연관 데이터 영구 삭제")
            
            return self.save_to_excel()
            
        except Exception as e:
            return False, f"강제 삭제 중 오류: {e}"

    def load_config(self):
        if os.path.exists(Config.CONFIG_FILENAME):
            try:
                with open(Config.CONFIG_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_excel_path = data.get("excel_path", Config.DEFAULT_EXCEL_PATH)
                    self.current_theme = data.get("theme", "Dark") 
                    self.attachment_dir = data.get("attachment_dir", Config.DEFAULT_ATTACHMENT_DIR)
            except Exception as e:
                print(f"설정 로드 실패: {e}")

    def save_config(self, new_path=None, new_theme=None, new_attachment_dir=None):
        if new_path: self.current_excel_path = new_path
        if new_theme: self.current_theme = new_theme
        if new_attachment_dir: self.attachment_dir = new_attachment_dir
        
        data = {
            "excel_path": self.current_excel_path,
            "theme": self.current_theme,
            "attachment_dir": self.attachment_dir 
        }
        try:
            with open(Config.CONFIG_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def load_data(self):
        """엑셀 파일 로드"""
        if os.path.exists(self.current_excel_path):
            try:
                with pd.ExcelFile(self.current_excel_path) as xls:
                    # 1. Data 시트
                    if Config.SHEET_DATA in xls.sheet_names:
                        self.df = pd.read_excel(xls, Config.SHEET_DATA)
                    else:
                        self.df = pd.read_excel(xls, 0)

                    # 2. Log 시트
                    if Config.SHEET_LOG in xls.sheet_names:
                        self.log_df = pd.read_excel(xls, Config.SHEET_LOG)
                    else:
                        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS)
                        
                    # 3. Memo 시트
                    if Config.SHEET_MEMO in xls.sheet_names:
                        self.memo_df = pd.read_excel(xls, Config.SHEET_MEMO)
                    else:
                        self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS)

                    # 4. Memo Log 시트
                    if Config.SHEET_MEMO_LOG in xls.sheet_names:
                        self.memo_log_df = pd.read_excel(xls, Config.SHEET_MEMO_LOG)
                    else:
                        self.memo_log_df = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)

                    # [신규] 5. Serial Data 시트
                    if Config.SHEET_SERIAL in xls.sheet_names:
                        self.serial_df = pd.read_excel(xls, Config.SHEET_SERIAL)
                        if not self.serial_df.empty:
                            self.serial_df["요청번호"] = self.serial_df["요청번호"].astype(str)
                    else:
                        self.serial_df = pd.DataFrame(columns=Config.SERIAL_COLUMNS)

                # 컬럼 정리
                current_cols_len = len(self.df.columns)
                config_cols_len = len(Config.COLUMNS)
                if current_cols_len >= config_cols_len:
                    self.df.columns = list(Config.COLUMNS) + list(self.df.columns[config_cols_len:])
                    self.df = self.df.iloc[:, :config_cols_len]
                else:
                    self.df.columns = Config.COLUMNS[:current_cols_len]
                
                self._preprocess_data()
                return True, os.path.basename(self.current_excel_path)
            
            except Exception as e:
                print(f"파일 로드 중 오류: {e}")
                return False, str(e)
        else:
            return False, self.current_excel_path

    def _preprocess_data(self):
        """데이터 내부 전처리"""
        if self.df.empty: return

        for col in Config.COLUMNS:
            if col not in self.df.columns: self.df[col] = '-'

        for date_col in ["출고요청일", "출고예정일", "출고일"]:
            if date_col in self.df.columns:
                 self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce', format='mixed').dt.strftime('%Y-%m-%d')

        self.df = self.df.fillna('-')
        
        if self.memo_df.empty: self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS)
        else:
            if "확인" not in self.memo_df.columns: self.memo_df["확인"] = "N"
            
        if self.memo_log_df.empty: self.memo_log_df = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)
        
        if self.serial_df.empty:
            self.serial_df = pd.DataFrame(columns=Config.SERIAL_COLUMNS)
        else:
            self.serial_df = self.serial_df.fillna("-")

    def save_to_excel(self):
        """데이터, 로그, 메모, 시리얼데이터를 엑셀 파일에 저장"""
        existing_cols = [c for c in Config.COLUMNS if c in self.df.columns]
        output_df = self.df[existing_cols]

        try:
            with pd.ExcelWriter(self.current_excel_path, engine="openpyxl") as writer:
                output_df.to_excel(writer, sheet_name=Config.SHEET_DATA, index=False)
                self.log_df.to_excel(writer, sheet_name=Config.SHEET_LOG, index=False)
                self.memo_df.to_excel(writer, sheet_name=Config.SHEET_MEMO, index=False)
                self.memo_log_df.to_excel(writer, sheet_name=Config.SHEET_MEMO_LOG, index=False)
                self.serial_df.to_excel(writer, sheet_name=Config.SHEET_SERIAL, index=False)
            
            self.load_data()
            return True, "저장되었습니다."

        except PermissionError:
            return False, "엑셀 파일이 현재 열려있어 저장할 수 없습니다.\n파일을 닫거나 잠시 후 다시 시도해주세요."
        except Exception as e:
            return False, f"저장 중 오류 발생: {e}"

    def _add_log(self, action, details):
        try: user = getpass.getuser()
        except: user = "Unknown"
        new_entry = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": user, "구분": action, "상세내용": details}
        self.log_df = pd.concat([self.log_df, pd.DataFrame([new_entry])], ignore_index=True)

    def _add_memo_log(self, action, req_no, content):
        try: user = getpass.getuser()
        except: user = "Unknown"
        new_entry = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": user, "구분": action, "요청번호": str(req_no), "내용": content}
        self.memo_log_df = pd.concat([self.memo_log_df, pd.DataFrame([new_entry])], ignore_index=True)

    def add_memo(self, req_no, content):
        try: user = getpass.getuser()
        except: user = "Unknown"
        try: pc_info = platform.node()
        except: pc_info = "Unknown"
        new_memo = {"번호": str(req_no), "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": user, "PC정보": pc_info, "내용": content, "확인": "N"}
        self.memo_df = pd.concat([self.memo_df, pd.DataFrame([new_memo])], ignore_index=True)
        self._add_memo_log("추가", req_no, content)
        return self.save_to_excel()

    def update_memo_check(self, req_no, timestamp, content, new_status):
        mask = ((self.memo_df["번호"].astype(str) == str(req_no)) & (self.memo_df["일시"] == timestamp) & (self.memo_df["내용"] == content))
        if mask.any():
            self.memo_df.loc[mask, "확인"] = new_status
            return self.save_to_excel()
        return False, "메모를 찾을 수 없습니다."

    def get_memos(self, req_no):
        if self.memo_df.empty: return []
        mask = self.memo_df["번호"].astype(str) == str(req_no)
        target_memos = self.memo_df[mask].copy()
        if target_memos.empty: return []
        target_memos = target_memos.sort_values(by="일시", ascending=False)
        return target_memos.to_dict('records')

    def get_unchecked_memo_count(self, req_no):
        if self.memo_df.empty: return 0
        mask = (self.memo_df["번호"].astype(str) == str(req_no)) & (self.memo_df["확인"] == "N")
        return len(self.memo_df[mask])

    def delete_memo(self, req_no, timestamp, content):
        mask = ((self.memo_df["번호"].astype(str) == str(req_no)) & (self.memo_df["일시"] == timestamp) & (self.memo_df["내용"] == content))
        if mask.any():
            if "[파일첨부]" in content and "(경로:" in content:
                try:
                    file_path = None
                    # [수정] 줄 단위 파싱으로 변경
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith("(경로:") and line.endswith(")"):
                            file_path = line[5:-1].strip()
                            break
                    
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                except: pass
            self.memo_df = self.memo_df[~mask]
            self._add_memo_log("삭제", req_no, content)
            return self.save_to_excel()
        return False, "삭제할 메모를 찾을 수 없습니다."

    def save_attachment(self, source_path):
        if not os.path.exists(source_path): return None, "원본 파일이 존재하지 않습니다."
        try:
            if not os.path.exists(self.attachment_dir): os.makedirs(self.attachment_dir)
            file_name = os.path.basename(source_path)
            name, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(self.attachment_dir, new_file_name)
            shutil.copy2(source_path, dest_path)
            return dest_path, None
        except Exception as e: return None, str(e)

    def get_status_list(self):
        if "Status" in self.df.columns: return sorted(self.df["Status"].astype(str).unique().tolist())
        return []

    def get_status_by_req_no(self, req_no):
        if self.df.empty or "번호" not in self.df.columns: return None
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any(): return self.df.loc[mask, "Status"].iloc[0]
        return None

    def get_filtered_data(self, status_filter_list=None, search_keyword="", sort_by=None, ascending=True):
        if self.df.empty: return self.df
        filtered_df = self.df.copy()
        
        if not search_keyword:
            if status_filter_list is not None and len(status_filter_list) > 0:
                filtered_df = filtered_df[filtered_df["Status"].astype(str).isin(status_filter_list)]
            elif status_filter_list is not None and len(status_filter_list) == 0:
                return filtered_df.iloc[0:0]
        
        if search_keyword:
            search_cols = [col for col in Config.SEARCH_TARGET_COLS if col in filtered_df.columns]
            if search_cols:
                mask = pd.Series(False, index=filtered_df.index)
                for col in search_cols: mask |= filtered_df[col].astype(str).str.contains(search_keyword, case=False, na=False)
                filtered_df = filtered_df[mask]
                
        if sort_by and sort_by in filtered_df.columns:
            if sort_by == "번호":
                filtered_df["_sort_helper"] = pd.to_numeric(filtered_df[sort_by], errors='coerce')
                filtered_df = filtered_df.sort_values(by="_sort_helper", ascending=ascending)
                filtered_df = filtered_df.drop(columns=["_sort_helper"])
            else:
                filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        return filtered_df

    def update_production_schedule(self, req_no, date_str):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            self.df.loc[mask, "출고예정일"] = date_str
            self.df.loc[mask, "Status"] = "생산중"
            self._add_log("일정 수립", f"번호[{req_no}] 예정일({date_str}) 등록 및 생산시작")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def get_serial_list(self, req_no, model_name):
        if self.serial_df.empty: return []
        mask = (self.serial_df["요청번호"].astype(str) == str(req_no)) & (self.serial_df["모델명"] == model_name)
        target_data = self.serial_df[mask].copy()
        try:
            target_data["_sort"] = pd.to_numeric(target_data["순번"])
            target_data = target_data.sort_values("_sort")
        except:
            target_data = target_data.sort_values("순번")
        return target_data.to_dict('records')

    def update_serial_list(self, req_no, model_name, new_data_list):
        if not self.serial_df.empty:
            mask = (self.serial_df["요청번호"].astype(str) == str(req_no)) & (self.serial_df["모델명"] == model_name)
            self.serial_df = self.serial_df[~mask]
        if new_data_list:
            new_rows_df = pd.DataFrame(new_data_list)
            self.serial_df = pd.concat([self.serial_df, new_rows_df], ignore_index=True)
            
        serial_list = [
            str(item.get("시리얼번호", "")).strip()
            for item in new_data_list
            if item.get("시리얼번호") and str(item.get("시리얼번호")).strip() != "" and str(item.get("시리얼번호")) != "-"
        ]
        joined_serials = ", ".join(serial_list)

        lens_list = [
            str(item.get("렌즈업체", "")).strip()
            for item in new_data_list
            if item.get("렌즈업체") and str(item.get("렌즈업체")).strip() != "" and str(item.get("렌즈업체")) != "-"
        ]
        unique_lenses = sorted(list(set(lens_list)))
        joined_lenses = ", ".join(unique_lenses)
        
        mask_main = (self.df["번호"].astype(str) == str(req_no)) & (self.df["모델명"] == model_name)
        if mask_main.any():
            self.df.loc[mask_main, "시리얼번호"] = joined_serials
            self.df.loc[mask_main, "렌즈업체"] = joined_lenses
            
        return True

    def finalize_production(self, req_no, out_date):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            self.df.loc[mask, "출고일"] = out_date
            self.df.loc[mask, "Status"] = "완료"
            self._add_log("생산 완료", f"번호[{req_no}] 출고일({out_date}) 처리 완료.")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def update_expected_date(self, req_no, new_date):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            old_date = self.df.loc[mask, "출고예정일"].iloc[0]
            self.df.loc[mask, "출고예정일"] = new_date
            self._add_log("일정 변경", f"번호[{req_no}] 예정일 변경 ({old_date} -> {new_date})")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def update_status_to_hold(self, req_no):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            old_status = self.df.loc[mask, "Status"].iloc[0]
            self.df.loc[mask, "Status"] = "중지"
            self.df.loc[mask, "출고예정일"] = pd.NaT 
            self._add_log("중지 설정", f"번호[{req_no}] 상태 변경 ({old_status} -> 중지)")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def update_status_resume(self, req_no, new_date):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            self.df.loc[mask, "Status"] = "생산중"
            self.df.loc[mask, "출고예정일"] = new_date
            self._add_log("생산 재개", f"번호[{req_no}] 중지 -> 생산중 변경, 예정일({new_date}) 설정")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def update_status_to_waiting(self, req_no, reason="달력에서 이동"):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            old_status = self.df.loc[mask, "Status"].iloc[0]
            self.df.loc[mask, "Status"] = "대기"
            self.df.loc[mask, "대기사유"] = reason
            self.df.loc[mask, "출고예정일"] = pd.NaT
            self._add_log("대기 설정", f"번호[{req_no}] 상태 변경 ({old_status} -> 대기) / 사유: {reason}")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def delete_request(self, req_no):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            details = f"번호[{req_no}] 데이터 삭제"
            self._add_log("데이터 삭제", details)
            self.df = self.df[~mask]
            
            if not self.serial_df.empty:
                s_mask = self.serial_df["요청번호"].astype(str) == str(req_no)
                self.serial_df = self.serial_df[~s_mask]
            
            if not self.memo_df.empty:
                m_mask = self.memo_df["번호"].astype(str) == str(req_no)
                self.memo_df = self.memo_df[~m_mask]

            return self.save_to_excel()
        return False, "삭제할 데이터를 찾을 수 없습니다."