import os


# ==========================================
# [Config] 상수 및 기본 설정값 관리
# ==========================================
class Config:
    # ---------------------------------------------------------
    # [경로 설정 변경] 
    # 실행 파일 위치가 아닌, 사용자 홈 디렉토리(C:\Users\Name)에 저장
    # ---------------------------------------------------------
    
    # 1. 사용자 홈 디렉토리 구하기 (예: C:\Users\sue)
    USER_HOME = os.path.expanduser("~")
    
    # 2. 앱 전용 폴더 이름 정의
    APP_DIR_NAME = ".ProductionManager"
    
    # 3. 실제 폴더 경로 조합 (예: C:\Users\sue\.ProductionManager)
    APP_DIR = os.path.join(USER_HOME, APP_DIR_NAME)
    
    # 4. 폴더가 없으면 생성 (이 코드가 실행될 때 폴더를 만듦)
    if not os.path.exists(APP_DIR):
        try:
            os.makedirs(APP_DIR)
        except OSError as e:
            print(f"설정 폴더 생성 실패: {e}")

    # 5. 설정 파일 전체 경로 (예: C:\Users\sue\.ProductionManager\config.json)
    CONFIG_FILENAME = os.path.join(APP_DIR, "config.json")
    
    # 6. 애플리케이션 버전
    APP_VERSION = "1.0.0"
    
    # ---------------------------------------------------------
    # [기타 설정]
    # ---------------------------------------------------------
    
    # 기본 엑셀 파일 경로 (최초 실행 시 사용될 기본값)
    DEFAULT_EXCEL_PATH = r"\\cox_biz\business\2024-2025\생산요청.xlsx"
    
    # [시트 이름 정의]
    SHEET_DATA = "Data"
    SHEET_LOG = "Log"

    # 엑셀 헤더 정의 (A열 ~ P열)
    # [수정] "대기사유" (P열) 추가
    COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "기타요청사항", "업체별 특이사항", "출고요청일", 
        "출고예정일", "출고일", "시리얼번호", "렌즈업체", 
        "생산팀 메모", "Status", "파일경로", "대기사유"
    ]
    
    # 로그 시트 헤더 정의
    LOG_COLUMNS = ["일시", "작업자", "구분", "상세내용"]

    # 화면에 보여줄 컬럼
    DISPLAY_COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "출고요청일", "출고예정일", "Status"
    ]
    
    # 검색 대상 컬럼
    SEARCH_TARGET_COLS = ["번호", "업체명", "모델명", "상세", "시리얼번호"]