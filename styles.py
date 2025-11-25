"""Shared style definitions for the Production Manager app."""

COLORS = {
    "primary": "#3B8ED0",
    "danger": "#E04F5F",
    "success": "#2CC985",
    "text": "#FFFFFF",
    "bg_dark": "#2b2b2b",
}

FONTS = {
    "default": ("Malgun Gothic", 12),
    "header": ("Malgun Gothic", 16, "bold"),
}

BTN_PRIMARY = {
    "fg_color": COLORS["primary"],
    "text_color": COLORS["text"],
    "corner_radius": 6,
}

BTN_DANGER = {
    "fg_color": COLORS["danger"],
    "text_color": COLORS["text"],
    "corner_radius": 6,
}
