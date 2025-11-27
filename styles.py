# styles.py
import customtkinter as ctk

# ==========================================
# [Color System] (Light, Dark) Tuples
# ==========================================
# 라이트 모드(Light): 가독성을 위해 명도가 낮고 채도가 높은 '진한' 색상을 사용합니다.
# 다크 모드(Dark): 눈의 피로를 줄이기 위해 명도가 높고 채도가 낮은 '파스텔' 톤을 사용합니다.
COLORS = {
    # 1. 브랜드/메인 색상 (활성 버튼, 주요 텍스트)
    # Light: 신뢰감 있는 진한 로얄 블루 / Dark: 밝고 산뜻한 스카이 블루
    "primary": ("#1565C0", "#3B8ED0"), 
    "primary_hover": ("#0D47A1", "#36719F"),
    
    # 2. 상태 표시 색상
    # 위험 (중지, 삭제) - Light: 강렬한 레드 / Dark: 부드러운 코랄 레드
    "danger": ("#C62828", "#E04F5F"),
    "danger_hover": ("#B71C1C", "#D32F2F"),
    
    # 성공 (완료, 진행) - Light: 짙은 포레스트 그린 / Dark: 밝은 에메랄드 그린
    "success": ("#2E7D32", "#2CC985"),
    
    # 경고 (대기) - Light: 진한 오렌지 / Dark: 밝은 귤색
    "warning": ("#EF6C00", "#D35400"),
    
    # 3. 텍스트 색상
    # 기본 텍스트 - Light: 완전 검정보다는 짙은 차콜 (#212121) / Dark: 흰색 (#FFFFFF)
    "text": ("#212121", "#FFFFFF"),
    
    # 보조 텍스트 (설명, 날짜) - Light: 중간 회색 / Dark: 연한 회색
    "text_dim": ("#616161", "#AAAAAA"),
    
    # 4. 배경 색상
    # bg_dark: 앱의 기본 배경 (가장 뒤)
    # Light: 아주 연한 웜그레이/쿨그레이 톤 (#F5F5F5) - 흰색과 구분됨 / Dark: 어두운 회색 (#2b2b2b)
    "bg_dark": ("#F5F5F5", "#2b2b2b"),
    
    # bg_medium: 카드, 리스트, 컨테이너 배경
    # Light: 순수 흰색 (#FFFFFF) - 그림자나 테두리로 구분 / Dark: 중간 회색 (#333333)
    "bg_medium": ("#FFFFFF", "#333333"),
    
    # bg_light: 입력창, 비활성 버튼, 보조 영역
    # Light: 연한 회색 (#E0E0E0) / Dark: 밝은 회색 (#555555)
    "bg_light": ("#E0E0E0", "#555555"),
    "bg_light_hover": ("#BDBDBD", "#333333"),
    
    # 5. 테두리 및 구분선
    # Light: 명확한 구분을 위한 진한 회색 실선 / Dark: 은은한 회색 실선
    "border": ("#9E9E9E", "#444444"),
    
    "transparent": "transparent"
}

FONTS = {
    "main": ("Malgun Gothic", 12),
    "main_bold": ("Malgun Gothic", 12, "bold"),
    "header": ("Malgun Gothic", 14, "bold"),
    "title": ("Malgun Gothic", 16, "bold"),
    "small": ("Malgun Gothic", 10),
}

def get_color_str(key):
    """
    Standard Tkinter(ttk)나 Matplotlib 처럼
    튜플 색상(("Light", "Dark"))을 이해하지 못하는 라이브러리를 위해
    현재 모드에 맞는 단일 Hex String 색상을 반환합니다.
    """
    color_val = COLORS.get(key)
    
    # 튜플이 아니면 그대로 반환
    if not isinstance(color_val, tuple):
        return color_val
        
    mode = ctk.get_appearance_mode()
    if mode == "Light":
        return color_val[0]
    else:
        return color_val[1]