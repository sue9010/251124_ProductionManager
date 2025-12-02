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
        self.serial_df = pd.DataFrame(columns=Config.SERIAL_COLUMNS)
        
        self.current_excel_path = Config.DEFAULT_EXCEL_PATH
        self.current_theme = "Dark"  
        self.attachment_dir = Config.DEFAULT_ATTACHMENT_DIR 
        
        self.is_dev_mode = False
        
        self.load_config()

    def set_dev_mode(self, enabled: bool):
        """개발자 모드 상태 변경"""
        self.is_dev_mode = enabled

    # ---------------------------------------------------------
    # [핵심] 트랜잭션 처리 (동시성 제어)
    # ---------------------------------------------------------
    def _execute_transaction(self, update_logic_func):
        """
        데이터 충돌 방지를 위한 트랜잭션 함수
        1. 최신 엑셀 파일 로드 (읽기)
        2. update_logic_func 실행 (수정 로직 적용)
        3. 엑셀 파일 저장 (쓰기)
        4. 메모리 데이터 갱신 (UI 반영용)
        """
        if not os.path.exists(self.current_excel_path):
            return False, "엑셀 파일이 존재하지 않습니다."

        try:
            # 1. 저장 직전 최신 상태 읽기 (임시 변수에 로드)
            with pd.ExcelFile(self.current_excel_path) as xls:
                # Data 시트
                if Config.SHEET_DATA in xls.sheet_names:
                    temp_df = pd.read_excel(xls, Config.SHEET_DATA)
                else:
                    temp_df = pd.read_excel(xls, 0)
                
                # Log 시트
                if Config.SHEET_LOG in xls.sheet_names:
                    temp_log = pd.read_excel(xls, Config.SHEET_LOG)
                else:
                    temp_log = pd.DataFrame(columns=Config.LOG_COLUMNS)
                
                # Memo 시트
                if Config.SHEET_MEMO in xls.sheet_names:
                    temp_memo = pd.read_excel(xls, Config.SHEET_MEMO)
                else:
                    temp_memo = pd.DataFrame(columns=Config.MEMO_COLUMNS)
                
                # Memo Log 시트
                if Config.SHEET_MEMO_LOG in xls.sheet_names:
                    temp_memo_log = pd.read_excel(xls, Config.SHEET_MEMO_LOG)
                else:
                    temp_memo_log = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)
                
                # Serial 시트
                if Config.SHEET_SERIAL in xls.sheet_names:
                    temp_serial = pd.read_excel(xls, Config.SHEET_SERIAL)
                    if not temp_serial.empty:
                        temp_serial["요청번호"] = temp_serial["요청번호"].astype(str)
                else:
                    temp_serial = pd.DataFrame(columns=Config.SERIAL_COLUMNS)

            # 전처리 (결측치 처리 등)
            for col in Config.COLUMNS:
                if col not in temp_df.columns: temp_df[col] = '-'
            # 날짜 컬럼 등은 필요 시 여기서 변환하지만, 저장 시에는 문자열로 저장되므로 생략 가능
            temp_df = temp_df.fillna('-')
            
            # 2. 수정 로직 실행 (콜백 함수 호출)
            # dfs 딕셔너리에 모든 데이터프레임을 담아 전달
            dfs = {
                "df": temp_df, 
                "log": temp_log, 
                "memo": temp_memo, 
                "memo_log": temp_memo_log, 
                "serial": temp_serial
            }
            
            success, msg = update_logic_func(dfs)
            
            if not success:
                return False, msg

            # 3. 파일 저장 (수정된 최신 데이터로 덮어쓰기)
            with pd.ExcelWriter(self.current_excel_path, engine="openpyxl") as writer:
                dfs["df"].to_excel(writer, sheet_name=Config.SHEET_DATA, index=False)
                dfs["log"].to_excel(writer, sheet_name=Config.SHEET_LOG, index=False)
                dfs["memo"].to_excel(writer, sheet_name=Config.SHEET_MEMO, index=False)
                dfs["memo_log"].to_excel(writer, sheet_name=Config.SHEET_MEMO_LOG, index=False)
                dfs["serial"].to_excel(writer, sheet_name=Config.SHEET_SERIAL, index=False)

            # 4. 내 메모리 갱신 (UI 업데이트용)
            self.load_data() 
            return True, "저장되었습니다."

        except PermissionError:
            return False, "엑셀 파일이 현재 열려있어 저장할 수 없습니다.\n파일을 닫거나 잠시 후 다시 시도해주세요."
        except Exception as e:
            return False, f"트랜잭션 저장 중 오류 발생: {e}"

    def _create_log_entry(self, action, details):
        """트랜잭션 내부용 로그 생성 헬퍼"""
        try: user = getpass.getuser()
        except: user = "Unknown"
        return {
            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업자": user,
            "구분": action,
            "상세내용": details
        }

    # ---------------------------------------------------------
    # [설정 및 파일 관리]
    # ---------------------------------------------------------
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
        """엑셀 파일 로드 (읽기 전용)"""
        if os.path.exists(self.current_excel_path):
            try:
                with pd.ExcelFile(self.current_excel_path) as xls:
                    # 1. Data
                    if Config.SHEET_DATA in xls.sheet_names:
                        self.df = pd.read_excel(xls, Config.SHEET_DATA)
                    else:
                        self.df = pd.read_excel(xls, 0)

                    # 2. Log
                    if Config.SHEET_LOG in xls.sheet_names:
                        self.log_df = pd.read_excel(xls, Config.SHEET_LOG)
                    else:
                        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS)
                        
                    # 3. Memo
                    if Config.SHEET_MEMO in xls.sheet_names:
                        self.memo_df = pd.read_excel(xls, Config.SHEET_MEMO)
                    else:
                        self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS)

                    # 4. Memo Log
                    if Config.SHEET_MEMO_LOG in xls.sheet_names:
                        self.memo_log_df = pd.read_excel(xls, Config.SHEET_MEMO_LOG)
                    else:
                        self.memo_log_df = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)

                    # 5. Serial Data
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
        """
        [주의] 단순 저장 메서드. 
        동시성 문제가 발생할 수 있으므로 단순 로컬 작업이나 일괄 정리 작업 외에는
        _execute_transaction을 사용하는 메서드를 호출하는 것을 권장함.
        """
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

    # ---------------------------------------------------------
    # [개발자 모드 및 유지보수]
    # ---------------------------------------------------------
    def create_backup(self):
        if not os.path.exists(self.current_excel_path):
            return False, "원본 파일이 없습니다."
        try:
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
        """오래된 로그 정리 (트랜잭션 적용)"""
        def logic(dfs):
            try:
                cutoff_date = datetime.now() - timedelta(days=months*30)
                
                # Log 정리
                original_log_count = len(dfs["log"])
                temp_log_dates = pd.to_datetime(dfs["log"]['일시'], errors='coerce')
                dfs["log"] = dfs["log"][temp_log_dates >= cutoff_date]
                deleted_log = original_log_count - len(dfs["log"])
                
                # Memo Log 정리
                original_memo_log_count = len(dfs["memo_log"])
                temp_memo_dates = pd.to_datetime(dfs["memo_log"]['일시'], errors='coerce')
                dfs["memo_log"] = dfs["memo_log"][temp_memo_dates >= cutoff_date]
                deleted_memo_log = original_memo_log_count - len(dfs["memo_log"])
                
                msg = f"로그 정리 완료 (기준: {cutoff_date.strftime('%Y-%m-%d')})\n- 일반 로그 삭제: {deleted_log}건\n- 메모 로그 삭제: {deleted_memo_log}건"
                return True, msg
            except Exception as e:
                return False, f"로그 정리 중 오류: {e}"

        return self._execute_transaction(logic)

    def hard_delete_request(self, req_no):
        """[Dev Only] 데이터 강제 완전 삭제 (트랜잭션 적용)"""
        if not self.is_dev_mode:
            return False, "개발자 모드가 아닙니다."

        def logic(dfs):
            # 1. Main Data 삭제
            mask_data = dfs["df"]["번호"].astype(str) == str(req_no)
            if not mask_data.any():
                return False, "데이터를 찾을 수 없습니다."
            dfs["df"] = dfs["df"][~mask_data]
            
            # 2. Serial Data 삭제
            if not dfs["serial"].empty:
                mask_serial = dfs["serial"]["요청번호"].astype(str) == str(req_no)
                dfs["serial"] = dfs["serial"][~mask_serial]
                
            # 3. Memo 삭제
            if not dfs["memo"].empty:
                mask_memo = dfs["memo"]["번호"].astype(str) == str(req_no)
                dfs["memo"] = dfs["memo"][~mask_memo]
            
            # 4. 로그 남기기
            new_log = self._create_log_entry("강제 삭제", f"[Dev] 번호[{req_no}] 및 연관 데이터 영구 삭제")
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            
            return True, ""

        return self._execute_transaction(logic)

    # ---------------------------------------------------------
    # [비즈니스 로직 - 트랜잭션 적용]
    # ---------------------------------------------------------
    def update_production_schedule(self, req_no, date_str):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                dfs["df"].loc[mask, "출고예정일"] = date_str
                dfs["df"].loc[mask, "Status"] = "생산중"
                
                new_log = self._create_log_entry("일정 수립", f"번호[{req_no}] 예정일({date_str}) 등록 및 생산시작")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "데이터를 찾을 수 없습니다 (삭제되었거나 변경됨)."

        return self._execute_transaction(logic)

    def update_status_to_hold(self, req_no):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                old_status = dfs["df"].loc[mask, "Status"].iloc[0]
                dfs["df"].loc[mask, "Status"] = "중지"
                dfs["df"].loc[mask, "출고예정일"] = pd.NaT 
                
                new_log = self._create_log_entry("중지 설정", f"번호[{req_no}] 상태 변경 ({old_status} -> 중지)")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "데이터를 찾을 수 없습니다."

        return self._execute_transaction(logic)

    def update_status_to_waiting(self, req_no, reason="달력에서 이동"):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                old_status = dfs["df"].loc[mask, "Status"].iloc[0]
                dfs["df"].loc[mask, "Status"] = "대기"
                dfs["df"].loc[mask, "대기사유"] = reason
                dfs["df"].loc[mask, "출고예정일"] = pd.NaT
                
                new_log = self._create_log_entry("대기 설정", f"번호[{req_no}] 상태 변경 ({old_status} -> 대기) / 사유: {reason}")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "데이터를 찾을 수 없습니다."
            
        return self._execute_transaction(logic)

    def update_expected_date(self, req_no, new_date):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                old_date = dfs["df"].loc[mask, "출고예정일"].iloc[0]
                dfs["df"].loc[mask, "출고예정일"] = new_date
                
                new_log = self._create_log_entry("일정 변경", f"번호[{req_no}] 예정일 변경 ({old_date} -> {new_date})")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "데이터를 찾을 수 없습니다."
        return self._execute_transaction(logic)

    def finalize_production(self, req_no, out_date):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                dfs["df"].loc[mask, "출고일"] = out_date
                dfs["df"].loc[mask, "Status"] = "완료"
                
                new_log = self._create_log_entry("생산 완료", f"번호[{req_no}] 출고일({out_date}) 처리 완료.")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "데이터를 찾을 수 없습니다."
        return self._execute_transaction(logic)

    def update_status_resume(self, req_no, new_date):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                dfs["df"].loc[mask, "Status"] = "생산중"
                dfs["df"].loc[mask, "출고예정일"] = new_date
                
                new_log = self._create_log_entry("생산 재개", f"번호[{req_no}] 중지 -> 생산중 변경, 예정일({new_date}) 설정")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "데이터를 찾을 수 없습니다."
        return self._execute_transaction(logic)

    def delete_request(self, req_no):
        def logic(dfs):
            mask = dfs["df"]["번호"].astype(str) == str(req_no)
            if mask.any():
                dfs["df"] = dfs["df"][~mask]
                
                # 시리얼 삭제
                if not dfs["serial"].empty:
                    s_mask = dfs["serial"]["요청번호"].astype(str) == str(req_no)
                    dfs["serial"] = dfs["serial"][~s_mask]
                
                # 메모 삭제
                if not dfs["memo"].empty:
                    m_mask = dfs["memo"]["번호"].astype(str) == str(req_no)
                    dfs["memo"] = dfs["memo"][~m_mask]

                new_log = self._create_log_entry("데이터 삭제", f"번호[{req_no}] 데이터 삭제")
                dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "삭제할 데이터를 찾을 수 없습니다."
        return self._execute_transaction(logic)

    # ---------------------------------------------------------
    # [메모 및 시리얼 관리 - 트랜잭션 적용]
    # ---------------------------------------------------------
    def add_memo(self, req_no, content):
        def logic(dfs):
            try: user = getpass.getuser()
            except: user = "Unknown"
            try: pc_info = platform.node()
            except: pc_info = "Unknown"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_memo = {
                "번호": str(req_no), 
                "일시": timestamp, 
                "작업자": user, "PC정보": pc_info, 
                "내용": content, "확인": "N"
            }
            dfs["memo"] = pd.concat([dfs["memo"], pd.DataFrame([new_memo])], ignore_index=True)
            
            new_memo_log = {
                "일시": timestamp,
                "작업자": user, "구분": "추가", "요청번호": str(req_no), "내용": content
            }
            dfs["memo_log"] = pd.concat([dfs["memo_log"], pd.DataFrame([new_memo_log])], ignore_index=True)
            return True, ""
        return self._execute_transaction(logic)

    def update_memo_check(self, req_no, timestamp, content, new_status):
        def logic(dfs):
            mask = ((dfs["memo"]["번호"].astype(str) == str(req_no)) & 
                    (dfs["memo"]["일시"] == timestamp) & 
                    (dfs["memo"]["내용"] == content))
            if mask.any():
                dfs["memo"].loc[mask, "확인"] = new_status
                return True, ""
            return False, "메모를 찾을 수 없습니다."
        return self._execute_transaction(logic)

    def delete_memo(self, req_no, timestamp, content):
        def logic(dfs):
            mask = ((dfs["memo"]["번호"].astype(str) == str(req_no)) & 
                    (dfs["memo"]["일시"] == timestamp) & 
                    (dfs["memo"]["내용"] == content))
            if mask.any():
                # 파일 삭제 시도 (로컬 파일 삭제는 트랜잭션과 별개로 수행)
                if "[파일첨부]" in content and "(경로:" in content:
                    try:
                        for line in content.split('\n'):
                            line = line.strip()
                            if line.startswith("(경로:") and line.endswith(")"):
                                file_path = line[5:-1].strip()
                                if file_path and os.path.exists(file_path):
                                    os.remove(file_path)
                                break
                    except: pass
                
                dfs["memo"] = dfs["memo"][~mask]
                
                # 메모 로그에 삭제 기록
                new_log = {
                    "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "작업자": getpass.getuser(), "구분": "삭제", "요청번호": str(req_no), "내용": content
                }
                dfs["memo_log"] = pd.concat([dfs["memo_log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "삭제할 메모를 찾을 수 없습니다."
        return self._execute_transaction(logic)

    def update_serial_list(self, req_no, model_name, new_data_list):
        """시리얼 번호 및 렌즈 업체 정보를 업데이트합니다."""
        def logic(dfs):
            # 1. Serial Dataframe 업데이트
            if not dfs["serial"].empty:
                # 기존 데이터 삭제 (해당 요청번호, 모델명에 해당하는 것)
                mask = (dfs["serial"]["요청번호"].astype(str) == str(req_no)) & (dfs["serial"]["모델명"] == model_name)
                dfs["serial"] = dfs["serial"][~mask]
            
            if new_data_list:
                new_rows_df = pd.DataFrame(new_data_list)
                dfs["serial"] = pd.concat([dfs["serial"], new_rows_df], ignore_index=True)
            
            # 2. Main Dataframe 업데이트 (시리얼번호, 렌즈업체 요약)
            serial_list = [
                str(item.get("시리얼번호", "")).strip()
                for item in new_data_list
                if item.get("시리얼번호") and str(item.get("시리얼번호")).strip() not in ["", "-"]
            ]
            joined_serials = ", ".join(serial_list)

            lens_list = [
                str(item.get("렌즈업체", "")).strip()
                for item in new_data_list
                if item.get("렌즈업체") and str(item.get("렌즈업체")).strip() not in ["", "-"]
            ]
            unique_lenses = sorted(list(set(lens_list)))
            joined_lenses = ", ".join(unique_lenses)
            
            mask_main = (dfs["df"]["번호"].astype(str) == str(req_no)) & (dfs["df"]["모델명"] == model_name)
            if mask_main.any():
                dfs["df"].loc[mask_main, "시리얼번호"] = joined_serials
                dfs["df"].loc[mask_main, "렌즈업체"] = joined_lenses
                
            return True, ""

        return self._execute_transaction(logic)

    # ---------------------------------------------------------
    # [Read-Only Helper Methods]
    # 읽기 전용 메서드는 기존 메모리(self.df 등)를 사용해도 무방합니다.
    # 단, 최신 데이터를 보장하려면 사용자가 '새로고침' 버튼을 눌러 load_data를 호출해야 합니다.
    # ---------------------------------------------------------
    def get_status_list(self):
        if "Status" in self.df.columns: return sorted(self.df["Status"].astype(str).unique().tolist())
        return []

    def get_status_by_req_no(self, req_no):
        if self.df.empty or "번호" not in self.df.columns: return None
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any(): return self.df.loc[mask, "Status"].iloc[0]
        return None

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

    def save_attachment(self, source_path):
        if not os.path.exists(source_path): return None, "원본 파일이 존재하지 않습니다."
        try:
            if not os.path.exists(self.attachment_dir): os.makedirs(self.attachment_dir)
            file_name = os.path.basename(source_path)
            name, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(self.attachment_dir, new_file_name)
            
            dest_path = os.path.normpath(dest_path)
            
            shutil.copy2(source_path, dest_path)
            return dest_path, None
        except Exception as e: return None, str(e)