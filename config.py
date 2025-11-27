import os


# ==========================================
# [Config] 상수 및 기본 설정값 관리
# ==========================================
class Config:
    # ---------------------------------------------------------
    # [앱 설정 파일 경로] 
    # 개인화 설정(테마, 최근 경로 등)은 사용자 로컬 PC에 저장합니다.
    # ---------------------------------------------------------
    
    # 1. 사용자 홈 디렉토리 구하기 (예: C:\Users\Name)
    USER_HOME = os.path.expanduser("~")
    
    # 2. 앱 전용 폴더 이름 정의
    APP_DIR_NAME = ".ProductionManager"
    
    # 3. 설정 폴더 경로 (예: C:\Users\Name\.ProductionManager)
    APP_DIR = os.path.join(USER_HOME, APP_DIR_NAME)
    
    # 4. 폴더가 없으면 생성
    if not os.path.exists(APP_DIR):
        try:
            os.makedirs(APP_DIR)
        except OSError as e:
            print(f"설정 폴더 생성 실패: {e}")

    # 5. 설정 파일 전체 경로 (로컬 유지)
    CONFIG_FILENAME = os.path.join(APP_DIR, "config.json")
    
    # 6. 애플리케이션 버전
    APP_VERSION = "1.2.0"
    
    # ---------------------------------------------------------
    # [업무용 기본 경로 설정]
    # ---------------------------------------------------------
    
    # 기본 엑셀 파일 경로 (네트워크 공유 폴더)
    DEFAULT_EXCEL_PATH = r"\\cox_biz\생산-영업\생산요청.xlsx"
    
    # 기본 첨부 파일 저장 경로 (네트워크 공유 폴더)
    DEFAULT_ATTACHMENT_DIR = r"\\cox_biz\생산-영업\생산요청 관련 파일(도면 등)"
    
    # (참고) 네트워크 경로에 폴더가 없으면 생성 시도
    if not os.path.exists(DEFAULT_ATTACHMENT_DIR):
        try:
            # 네트워크 경로 접근 권한이 있을 경우에만 생성됨
            os.makedirs(DEFAULT_ATTACHMENT_DIR)
        except OSError:
            pass # 접근 권한이 없거나 경로가 잘못된 경우 무시 (나중에 저장 시 에러 처리됨)

    # ---------------------------------------------------------
    # [시트 및 컬럼 설정]
    # ---------------------------------------------------------
    
    # [시트 이름 정의]
    SHEET_DATA = "Data"
    SHEET_LOG = "Log"
    SHEET_MEMO = "Memos"
    SHEET_MEMO_LOG = "Memo Log" 

    # 엑셀 헤더 정의 (A열 ~ P열)
    COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "기타요청사항", "업체별 특이사항", "출고요청일", 
        "출고예정일", "출고일", "시리얼번호", "렌즈업체", 
        "생산팀 메모", "Status", "파일경로", "대기사유"
    ]
    
    # 로그 시트 헤더 정의
    LOG_COLUMNS = ["일시", "작업자", "구분", "상세내용"]

    # [수정] 메모 시트 헤더 정의 ("확인" 컬럼 추가)
    MEMO_COLUMNS = ["번호", "일시", "작업자", "PC정보", "내용", "확인"]
    
    # 메모 로그 시트 헤더 정의
    MEMO_LOG_COLUMNS = ["일시", "작업자", "구분", "요청번호", "내용"]

    # 화면에 보여줄 컬럼
    DISPLAY_COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "출고요청일", "출고예정일", "Status"
    ]
    
    # 검색 대상 컬럼
    SEARCH_TARGET_COLS = ["번호", "업체명", "모델명", "상세", "시리얼번호"]