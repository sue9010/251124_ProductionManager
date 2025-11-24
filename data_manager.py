import json
import os
from datetime import datetime

import pandas as pd

from config import Config


class DataManager:
    def __init__(self):
        self.df = pd.DataFrame()
        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS) # 로그 데이터프레임 초기화
        self.current_excel_path = Config.DEFAULT_EXCEL_PATH
        self.load_config()

    def load_config(self):
        """config.json 파일 로드"""
        if os.path.exists(Config.CONFIG_FILENAME):
            try:
                with open(Config.CONFIG_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_excel_path = data.get("excel_path", Config.DEFAULT_EXCEL_PATH)
            except Exception as e:
                print(f"설정 로드 실패: {e}")

    def save_config(self, new_path):
        """config.json 파일 저장"""
        self.current_excel_path = new_path
        with open(Config.CONFIG_FILENAME, "w", encoding="utf-8") as f:
            json.dump({"excel_path": new_path}, f, ensure_ascii=False, indent=4)

    def load_data(self):
        """엑셀 파일에서 데이터 및 로그 로드"""
        if os.path.exists(self.current_excel_path):
            try:
                # 엑셀 파일 객체 로드
                xls = pd.ExcelFile(self.current_excel_path)
                
                # 1. 생산 데이터 시트 로드
                if Config.SHEET_DATA in xls.sheet_names:
                    self.df = pd.read_excel(xls, Config.SHEET_DATA)
                else:
                    # 시트 이름이 다를 경우 첫 번째 시트를 읽음
                    self.df = pd.read_excel(xls, 0)

                # 컬럼 매핑 보정 (기존 파일의 컬럼 수가 Config와 다를 수 있음)
                # Config에 정의된 컬럼 이름으로 덮어쓰되, 부족한 부분은 유지하고 넘침은 자름
                current_cols_len = len(self.df.columns)
                config_cols_len = len(Config.COLUMNS)

                if current_cols_len >= config_cols_len:
                    # 엑셀 컬럼이 더 많거나 같으면 Config 길이만큼 잘라서 이름 매핑
                    self.df.columns = list(Config.COLUMNS) + list(self.df.columns[config_cols_len:])
                    self.df = self.df.iloc[:, :config_cols_len] # 필요한 만큼만 자르기
                else:
                    # 엑셀 컬럼이 더 적으면 있는 만큼만 이름 매핑
                    self.df.columns = Config.COLUMNS[:current_cols_len]
                
                # 2. 로그 시트 로드 (없으면 빈 DataFrame 생성)
                if Config.SHEET_LOG in xls.sheet_names:
                    self.log_df = pd.read_excel(xls, Config.SHEET_LOG)
                else:
                    self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS)

                self._preprocess_data()
                return True, os.path.basename(self.current_excel_path)
            
            except Exception as e:
                print(f"파일 로드 중 오류: {e}")
                return False, str(e)
        else:
            return False, self.current_excel_path

    def create_dummy_data(self):
        """테스트용 더미 데이터 생성"""
        data = {
            "번호": [1, 2, 3, 4, 5, 6, 7],
            "업체명": ["삼성전자", "LG화학", "SK하이닉스", "네이버", "카카오", "현대차", "기아"],
            "모델명": ["COX-A100", "COX-B200", "COX-C300", "COX-A100", "COX-D500", "COX-E600", "COX-F700"],
            "상세": ["기본형", "고급형", "방수형", "기본형", "산업용", "차량용", "항공용"],
            "수량": [10, 5, 20, 15, 8, 30, 12],
            "기타요청사항": ["빠른배송", None, "포장주의", None, "검수철저", "", ""],
            "업체별 특이사항": ["VIP", "신규", None, "VIP", None, "", ""],
            "출고요청일": ["2023-11-01", "2023-11-05", "2023-11-10", "2023-11-12", "2023-11-20", "2023-11-25", "2023-11-30"],
            "출고예정일": [None, "2023-11-15", None, None, None, "2023-12-01", None],
            "출고일": [None, None, None, None, None, None, None],
            "시리얼번호": [None, None, None, None, None, None, None],
            "렌즈업체": [None, None, None, None, None, None, None],
            "생산팀 메모": [None, None, None, None, None, None, None],
            "Status": ["생산 접수", "생산중", "대기", "완료", "출고", "생산 접수", "생산중"],
            "파일경로": [None]*7,
            "대기사유": [None, None, "부품 지연", None, None, None, None]
        }
        self.df = pd.DataFrame(data)
        self.log_df = pd.DataFrame(columns=Config.LOG_COLUMNS) # 더미 로그 초기화
        self._preprocess_data()

    def _preprocess_data(self):
        """데이터 내부 전처리"""
        if self.df.empty:
            return

        # 1. Config에 정의된 컬럼이 없으면 생성 (예: P열 '대기사유'가 엑셀에 없던 경우)
        for col in Config.COLUMNS:
            if col not in self.df.columns:
                self.df[col] = '-'

        # 2. 날짜 포맷팅
        for date_col in ["출고요청일", "출고예정일", "출고일"]:
            if date_col in self.df.columns:
                 self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce', format='mixed').dt.strftime('%Y-%m-%d')

        self.df = self.df.fillna('-')

    def save_to_excel(self):
        """데이터와 로그를 엑셀 파일에 함께 저장"""
        # 저장 전 컬럼 순서 강제 정렬 (Config 순서대로)
        existing_cols = [c for c in Config.COLUMNS if c in self.df.columns]
        output_df = self.df[existing_cols]

        with pd.ExcelWriter(self.current_excel_path, engine="openpyxl") as writer:
            output_df.to_excel(writer, sheet_name=Config.SHEET_DATA, index=False)
            self.log_df.to_excel(writer, sheet_name=Config.SHEET_LOG, index=False)
        
        self.load_data() # 저장 후 재로드하여 상태 동기화

    # -----------------------------------------------------
    # [New] Logging System
    # -----------------------------------------------------
    def _add_log(self, action, details):
        """로그 기록 추가 (내부 호출용)"""
        try:
            # 윈도우 사용자명 가져오기
            user = os.getlogin()
        except:
            user = os.environ.get('USERNAME', 'Unknown')

        new_entry = {
            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업자": user,
            "구분": action,
            "상세내용": details
        }
        
        # 로그 DataFrame에 추가 (concat 사용)
        self.log_df = pd.concat([self.log_df, pd.DataFrame([new_entry])], ignore_index=True)

    # -----------------------------------------------------
    # Business Logic (with Logging)
    # -----------------------------------------------------
    def get_status_list(self):
        if "Status" in self.df.columns:
            return sorted(self.df["Status"].astype(str).unique().tolist())
        return []

    def get_filtered_data(self, status_filter_list=None, search_keyword="", sort_by=None, ascending=True):
        """
        [수정] 정렬 기능 추가
        sort_by: 정렬할 컬럼명
        ascending: True(오름차순), False(내림차순)
        """
        if self.df.empty: return self.df
        filtered_df = self.df.copy()

        # 1. 필터링
        if status_filter_list is not None and len(status_filter_list) > 0:
            filtered_df = filtered_df[filtered_df["Status"].astype(str).isin(status_filter_list)]
        elif status_filter_list is not None and len(status_filter_list) == 0:
            return filtered_df.iloc[0:0]

        # 2. 검색
        if search_keyword:
            search_cols = [col for col in Config.SEARCH_TARGET_COLS if col in filtered_df.columns]
            if search_cols:
                mask = pd.Series(False, index=filtered_df.index)
                for col in search_cols:
                    mask |= filtered_df[col].astype(str).str.contains(search_keyword, case=False, na=False)
                filtered_df = filtered_df[mask]

        # 3. [추가] 정렬
        if sort_by and sort_by in filtered_df.columns:
            # 번호 컬럼은 숫자형으로 변환 후 정렬 시도 (문자열로 되어있을 경우를 대비)
            if sort_by == "번호":
                # 임시 컬럼 생성하여 숫자 변환 후 정렬
                filtered_df["_sort_helper"] = pd.to_numeric(filtered_df[sort_by], errors='coerce')
                filtered_df = filtered_df.sort_values(by="_sort_helper", ascending=ascending)
                filtered_df = filtered_df.drop(columns=["_sort_helper"])
            else:
                filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

        return filtered_df

    def update_production_schedule(self, req_no, date_str):
        """생산 일정 업데이트 (Log 추가)"""
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            self.df.loc[mask, "출고예정일"] = date_str
            self.df.loc[mask, "Status"] = "생산중"
            
            # [Log]
            self._add_log("일정 수립", f"번호[{req_no}] 예정일({date_str}) 등록 및 생산시작")
            
            self.save_to_excel()
            return True
        return False

    def update_production_complete(self, entry_data_list, out_date, memo):
        """생산 완료 업데이트 (Log 추가)"""
        updated_indices = []
        for entry in entry_data_list:
            idx = entry["index"]
            self.df.loc[idx, "시리얼번호"] = entry["serial"]
            self.df.loc[idx, "렌즈업체"] = entry["lens"]
            self.df.loc[idx, "출고일"] = out_date
            self.df.loc[idx, "생산팀 메모"] = memo
            self.df.loc[idx, "Status"] = "완료"
            updated_indices.append(str(self.df.loc[idx, "번호"]))

        # [Log]
        req_numbers = ",".join(sorted(list(set(updated_indices))))
        self._add_log("생산 완료", f"번호[{req_numbers}] 출고일({out_date}) 처리 완료. (품목수: {len(entry_data_list)})")
        
        self.save_to_excel()

    def update_expected_date(self, req_no, new_date):
        """출고예정일 수정 (Log 추가)"""
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            # 변경 전 값 가져오기 (로그용)
            old_date = self.df.loc[mask, "출고예정일"].iloc[0]
            
            self.df.loc[mask, "출고예정일"] = new_date
            
            # [Log]
            self._add_log("일정 변경", f"번호[{req_no}] 예정일 변경 ({old_date} -> {new_date})")
            
            self.save_to_excel()
            return True
        return False

    # -----------------------------------------------------
    # [New] Hold 관련 기능 추가
    # -----------------------------------------------------
    def update_status_to_hold(self, req_no):
        """상태를 Hold로 변경"""
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            old_status = self.df.loc[mask, "Status"].iloc[0]
            self.df.loc[mask, "Status"] = "Hold"
            
            # [Log]
            self._add_log("Hold 설정", f"번호[{req_no}] 상태 변경 ({old_status} -> Hold)")
            
            self.save_to_excel()
            return True
        return False

    def update_status_resume(self, req_no):
        """Hold 상태를 생산중으로 변경 (재개)"""
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            self.df.loc[mask, "Status"] = "생산중"
            
            # [Log]
            self._add_log("생산 재개", f"번호[{req_no}] Hold -> 생산중 변경")
            
            self.save_to_excel()
            return True
        return False

    # -----------------------------------------------------
    # [Updated] 생산대기 기능 (사유 입력 추가)
    # -----------------------------------------------------
    def update_status_to_waiting(self, req_no, reason):
        """상태를 '대기'로 변경하고 대기 사유를 저장"""
        mask = self.df["번호"].astype(str) == str(req_no)
        if mask.any():
            old_status = self.df.loc[mask, "Status"].iloc[0]
            self.df.loc[mask, "Status"] = "대기"
            self.df.loc[mask, "대기사유"] = reason  # 사유 저장
            
            # [Log]
            self._add_log("대기 설정", f"번호[{req_no}] 상태 변경 ({old_status} -> 대기) / 사유: {reason}")
            
            self.save_to_excel()
            return True
        return False