import os


# ==========================================
# [Config] 상수 및 기본 설정값 관리
# ==========================================
class Config:
    # ---------------------------------------------------------
    # [앱 설정 파일 경로] 
    # ---------------------------------------------------------
    USER_HOME = os.path.expanduser("~")
    APP_DIR_NAME = ".ProductionManager"
    APP_DIR = os.path.join(USER_HOME, APP_DIR_NAME)
    
    if not os.path.exists(APP_DIR):
        try:
            os.makedirs(APP_DIR)
        except OSError as e:
            print(f"설정 폴더 생성 실패: {e}")

    CONFIG_FILENAME = os.path.join(APP_DIR, "config.json")
    APP_VERSION = "1.3.9" # 버전 업 (Dev Mode 추가)
    
    # [보안] 개발자 모드 비밀번호 (실무에 맞게 변경하세요)
    DEV_PASSWORD = "admin" 

    # ---------------------------------------------------------
    # [업무용 기본 경로 설정]
    # ---------------------------------------------------------
    DEFAULT_EXCEL_PATH = r"\\cox_biz\생산-영업\생산요청.xlsx"
    DEFAULT_ATTACHMENT_DIR = r"\\cox_biz\생산-영업\생산요청 관련 파일(도면 등)"
    
    if not os.path.exists(DEFAULT_ATTACHMENT_DIR):
        try:
            os.makedirs(DEFAULT_ATTACHMENT_DIR)
        except OSError:
            pass 

    # ---------------------------------------------------------
    # [시트 및 컬럼 설정]
    # ---------------------------------------------------------
    
    # [시트 이름 정의]
    SHEET_DATA = "Data"
    SHEET_LOG = "Log"
    SHEET_MEMO = "Memos"
    SHEET_MEMO_LOG = "Memo Log"
    SHEET_SERIAL = "Serial_Data" 

    # 엑셀 헤더 정의 (Data 시트)
    COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "기타요청사항", "업체별 특이사항", "출고요청일", 
        "출고예정일", "출고일", "시리얼번호", "렌즈업체", 
        "생산팀 메모", "Status", "파일경로", "대기사유"
    ]
    
    # [신규] 시리얼 데이터 시트 헤더
    SERIAL_COLUMNS = ["요청번호", "순번", "모델명", "시리얼번호", "렌즈업체", "비고"]

    # 로그 관련
    LOG_COLUMNS = ["일시", "작업자", "구분", "상세내용"]
    MEMO_COLUMNS = ["번호", "일시", "작업자", "PC정보", "내용", "확인"]
    MEMO_LOG_COLUMNS = ["일시", "작업자", "구분", "요청번호", "내용"]

    # 화면 표시 설정
    DISPLAY_COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "출고요청일", "출고예정일", "Status"
    ]
    
    SEARCH_TARGET_COLS = ["번호", "업체명", "모델명", "상세", "시리얼번호"]