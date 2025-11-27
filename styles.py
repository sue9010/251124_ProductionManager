import customtkinter as ctk

# ==========================================
# [Color System] (Light, Dark) Tuples
# ==========================================
COLORS = {
    "primary": ("#1565C0", "#3B8ED0"), 
    "primary_hover": ("#0D47A1", "#36719F"),
    "danger": ("#C62828", "#E04F5F"),
    "danger_hover": ("#B71C1C", "#D32F2F"),
    "success": ("#2E7D32", "#2CC985"),
    "warning": ("#EF6C00", "#D35400"),
    "text": ("#212121", "#FFFFFF"),
    "text_dim": ("#616161", "#AAAAAA"),
    "bg_dark": ("#F5F5F5", "#2b2b2b"),
    "bg_medium": ("#FFFFFF", "#333333"),
    "bg_light": ("#E0E0E0", "#555555"),
    "bg_light_hover": ("#BDBDBD", "#333333"),
    "border": ("#9E9E9E", "#444444"),
    "transparent": "transparent"
}

# [핵심 수정] 폰트 패밀리 이름을 변수로 분리
# 여기에 "Pretendard"라고 적으면 모든 파일에 적용됩니다.
FONT_FAMILY = "Pretendard" 

FONTS = {
    "main": (FONT_FAMILY, 12),
    "main_bold": (FONT_FAMILY, 12, "bold"),
    "header": (FONT_FAMILY, 14, "bold"),
    "title": (FONT_FAMILY, 16, "bold"),
    "small": (FONT_FAMILY, 10),
}

def get_color_str(key):
    color_val = COLORS.get(key)
    if not isinstance(color_val, tuple):
        return color_val
    mode = ctk.get_appearance_mode()
    if mode == "Light":
        return color_val[0]
    else:
        return color_val[1]