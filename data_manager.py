import getpass
import json
import os
import platform
from datetime import datetime

import pandas as pd

from config import Config


class DataManager:
    def __init__(self):
        self.df = pd.DataFrame()
        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS) # 로그 데이터프레임
        self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS) # [신규] 메모 데이터프레임
        self.current_excel_path = Config.DEFAULT_EXCEL_PATH
        self.current_theme = "Dark"  # [신규] 기본 테마 설정
        self.load_config()

    def load_config(self):
        """config.json 파일 로드"""
        if os.path.exists(Config.CONFIG_FILENAME):
            try:
                with open(Config.CONFIG_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_excel_path = data.get("excel_path", Config.DEFAULT_EXCEL_PATH)
                    self.current_theme = data.get("theme", "Dark") # [신규] 테마 로드
            except Exception as e:
                print(f"설정 로드 실패: {e}")

    def save_config(self, new_path=None, new_theme=None):
        """config.json 파일 저장"""
        if new_path:
            self.current_excel_path = new_path
        if new_theme:
            self.current_theme = new_theme
            
        data = {
            "excel_path": self.current_excel_path,
            "theme": self.current_theme # [신규] 테마 저장
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
                    # 1. 생산 데이터 시트 로드
                    if Config.SHEET_DATA in xls.sheet_names:
                        self.df = pd.read_excel(xls, Config.SHEET_DATA)
                    else:
                        self.df = pd.read_excel(xls, 0)

                    # 2. 로그 시트 로드
                    if Config.SHEET_LOG in xls.sheet_names:
                        self.log_df = pd.read_excel(xls, Config.SHEET_LOG)
                    else:
                        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS)
                        
                    # 3. [신규] 메모 시트 로드
                    if Config.SHEET_MEMO in xls.sheet_names:
                        self.memo_df = pd.read_excel(xls, Config.SHEET_MEMO)
                    else:
                        self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS)

                # 컬럼 매핑 보정
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
        if self.df.empty:
            return

        for col in Config.COLUMNS:
            if col not in self.df.columns:
                self.df[col] = '-'

        for date_col in ["출고요청일", "출고예정일", "출고일"]:
            if date_col in self.df.columns:
                 self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce', format='mixed').dt.strftime('%Y-%m-%d')

        self.df = self.df.fillna('-')
        
        # 메모 데이터프레임 전처리
        if self.memo_df.empty:
            self.memo_df = pd.DataFrame(columns=Config.MEMO_COLUMNS)

    def save_to_excel(self):
        """데이터, 로그, 메모를 엑셀 파일에 저장"""
        existing_cols = [c for c in Config.COLUMNS if c in self.df.columns]
        output_df = self.df[existing_cols]

        try:
            with pd.ExcelWriter(self.current_excel_path, engine="openpyxl") as writer:
                output_df.to_excel(writer, sheet_name=Config.SHEET_DATA, index=False)
                self.log_df.to_excel(writer, sheet_name=Config.SHEET_LOG, index=False)
                self.memo_df.to_excel(writer, sheet_name=Config.SHEET_MEMO, index=False)
            
            self.load_data()
            return True, "저장되었습니다."

        except PermissionError:
            return False, "엑셀 파일이 현재 열려있어 저장할 수 없습니다.\n파일을 닫거나 잠시 후 다시 시도해주세요."
        except Exception as e:
            return False, f"저장 중 오류 발생: {e}"

    # -----------------------------------------------------
    # [Logging System]
    # -----------------------------------------------------
    def _add_log(self, action, details):
        try:
            user = getpass.getuser()
        except:
            user = "Unknown"

        new_entry = {
            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업자": user,
            "구분": action,
            "상세내용": details
        }
        self.log_df = pd.concat([self.log_df, pd.DataFrame([new_entry])], ignore_index=True)

    # -----------------------------------------------------
    # [Memo System] (신규)
    # -----------------------------------------------------
    def add_memo(self, req_no, content):
        """특정 번호에 대한 메모 추가"""
        try:
            user = getpass.getuser()
            pc_info = platform.node()
        except:
            user = "Unknown"
            pc_info = "Unknown"

        new_memo = {
            "번호": str(req_no),
            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업자": user,
            "PC정보": pc_info,
            "내용": content
        }
        self.memo_df = pd.concat([self.memo_df, pd.DataFrame([new_memo])], ignore_index=True)
        return self.save_to_excel()

    def get_memos(self, req_no):
        """특정 번호의 메모 목록 조회 (최신순 정렬)"""
        if self.memo_df.empty:
            return []
            
        mask = self.memo_df["번호"].astype(str) == str(req_no)
        target_memos = self.memo_df[mask].copy()
        
        if target_memos.empty:
            return []
            
        # 최신순 정렬 (일시 기준 내림차순)
        target_memos = target_memos.sort_values(by="일시", ascending=False)
        return target_memos.to_dict('records')

    def delete_memo(self, req_no, timestamp, content):
        """특정 메모 삭제"""
        mask = (
            (self.memo_df["번호"].astype(str) == str(req_no)) & 
            (self.memo_df["일시"] == timestamp) & 
            (self.memo_df["내용"] == content)
        )
        
        if mask.any():
            self.memo_df = self.memo_df[~mask]
            return self.save_to_excel()
        return False, "삭제할 메모를 찾을 수 없습니다."

    # -----------------------------------------------------
    # Business Logic
    # -----------------------------------------------------
    def get_status_list(self):
        if "Status" in self.df.columns:
            return sorted(self.df["Status"].astype(str).unique().tolist())
        return []

    def get_status_by_req_no(self, req_no):
        if self.df.empty or "번호" not in self.df.columns:
            return None
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            return self.df.loc[mask, "Status"].iloc[0]
        return None

    def get_filtered_data(self, status_filter_list=None, search_keyword="", sort_by=None, ascending=True):
        if self.df.empty: return self.df
        filtered_df = self.df.copy()

        if status_filter_list is not None and len(status_filter_list) > 0:
            filtered_df = filtered_df[filtered_df["Status"].astype(str).isin(status_filter_list)]
        elif status_filter_list is not None and len(status_filter_list) == 0:
            return filtered_df.iloc[0:0]

        if search_keyword:
            search_cols = [col for col in Config.SEARCH_TARGET_COLS if col in filtered_df.columns]
            if search_cols:
                mask = pd.Series(False, index=filtered_df.index)
                for col in search_cols:
                    mask |= filtered_df[col].astype(str).str.contains(search_keyword, case=False, na=False)
                filtered_df = filtered_df[mask]

        if sort_by and sort_by in filtered_df.columns:
            if sort_by == "번호":
                filtered_df["_sort_helper"] = pd.to_numeric(filtered_df[sort_by], errors='coerce')
                filtered_df = filtered_df.sort_values(by="_sort_helper", ascending=ascending)
                filtered_df = filtered_df.drop(columns=["_sort_helper"])
            else:
                filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

        return filtered_df

    # -----------------------------------------------------
    # Update Functions
    # -----------------------------------------------------
    def update_production_schedule(self, req_no, date_str):
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            self.df.loc[mask, "출고예정일"] = date_str
            self.df.loc[mask, "Status"] = "생산중"
            self._add_log("일정 수립", f"번호[{req_no}] 예정일({date_str}) 등록 및 생산시작")
            return self.save_to_excel()
        return False, "데이터를 찾을 수 없습니다."

    def update_production_complete(self, entry_data_list, out_date, memo):
        updated_indices = []
        for entry in entry_data_list:
            idx = entry["index"]
            self.df.loc[idx, "시리얼번호"] = entry["serial"]
            self.df.loc[idx, "렌즈업체"] = entry["lens"]
            self.df.loc[idx, "출고일"] = out_date
            self.df.loc[idx, "생산팀 메모"] = memo
            self.df.loc[idx, "Status"] = "완료"
            updated_indices.append(str(self.df.loc[idx, "번호"]))

        req_numbers = ",".join(sorted(list(set(updated_indices))))
        self._add_log("생산 완료", f"번호[{req_numbers}] 출고일({out_date}) 처리 완료.")
        return self.save_to_excel()

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
            return self.save_to_excel()
        return False, "삭제할 데이터를 찾을 수 없습니다."