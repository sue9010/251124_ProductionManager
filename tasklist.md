# 📋 COX Production Manager v2.0 - Refined Master Plan (상세 구현 지시서)

---

## 🎨 Phase 0: 기초 공사 (Foundation)

**목표:** 하드코딩된 스타일을 제거하고, 공통 모듈을 만들어 코드 중복을 줄입니다.

---

### 0.1. `styles.py` 파일 생성 및 적용 (상세)

#### 0.1.1 파일 생성

프로젝트 루트에 `styles.py`를 생성한 후 아래 코드를 그대로 작성합니다.

```python
# styles.py
COLORS = {
    "primary": "#3B8ED0",        # 메인 파랑 (생산접수, 활성 버튼)
    "primary_hover": "#36719F",  # 메인 파랑 호버
    "danger": "#E04F5F",         # 위험/강조 빨강 (Hold, 삭제)
    "danger_hover": "#D32F2F",   # 빨강 호버
    "success": "#2CC985",        # 성공/완료 초록 (완료, 테두리)
    "warning": "#D35400",        # 경고 주황 (대기)
    "text": "#FFFFFF",           # 기본 텍스트
    "text_dim": "#AAAAAA",       # 비활성 텍스트
    "bg_dark": "#2b2b2b",        # 어두운 배경 (메인, 트리뷰)
    "bg_medium": "#333333",      # 중간 배경 (카드, 리스트 아이템)
    "bg_light": "#555555",       # 밝은 배경 (일반 버튼)
    "bg_light_hover": "#333333", # 일반 버튼 호버
    "border": "#444444",         # 테두리
    "transparent": "transparent"
}

FONTS = {
    "main": ("Malgun Gothic", 12),
    "main_bold": ("Malgun Gothic", 12, "bold"),
    "header": ("Malgun Gothic", 14, "bold"),
    "title": ("Malgun Gothic", 16, "bold"),
    "small": ("Malgun Gothic", 10),
}
```

---

#### 0.1.2 `main.py` 적용

**Import 추가**
`from styles import COLORS, FONTS`

**헤더 버튼 (설정, 달력, 검색)**

* `fg_color="#555555"` → `COLORS["bg_light"]`
* `hover_color="#333333"` → `COLORS["bg_light_hover"]`

**데이터 읽어오기 버튼**

* `fg_color="#3B8ED0"` → `COLORS["primary"]`
* `hover_color="#36719F"` → `COLORS["primary_hover"]`

**구분선 (Frame)**

* `fg_color="#444444"` → `COLORS["border"]`

**필터 버튼 로직 (`update_filter_buttons_visuals`)**

* `active_color = "#3B8ED0"` → `COLORS["primary"]`
* `text_color_active = "white"` → `COLORS["text"]`
* `inactive_fg = "transparent"` → `COLORS["transparent"]`
* `inactive_border = "#555555"` → `COLORS["bg_light"]` 또는 `COLORS["border"]`
* `text_color_inactive = "#AAAAAA"` → `COLORS["text_dim"]`

**Hold 버튼 활성 색상**

* `#E04F5F` → `COLORS["danger"]`

**대기 버튼 활성 색상**

* `#3B8ED0` → `COLORS["primary"]` (또는 `COLORS["warning"]`으로 변경 고려)

**Treeview 스타일 (`style_treeview`)**

* `background / fieldbackground: #2b2b2b` → `COLORS["bg_dark"]`
* `Heading foreground: #3B8ED0` → `COLORS["primary"]`
* `Heading active background: #333333` → `COLORS["bg_medium"]`

---

#### 0.1.4 "Hold" 단어를 "중지"로 변경

**목표**: 프로그램 전반에 걸쳐 사용되는 'Hold'라는 단어를 명시적인 '중지'로 변경하여 의미를 명확히 합니다.

**적용 파일 및 변경 내용**:

*   `styles.py`: 주석 내 `(Hold, 삭제)` → `(중지, 삭제)`
*   `main.py`:
    *   `filter_states` 딕셔너리 키 `Hold` → `중지`
    *   버튼 텍스트 `text="Hold"` → `text="중지"`
    *   `update_filter_buttons_visuals` 함수 내 `if status == "Hold"` → `if status == "중지"`
    *   `reset_default_filters` 함수 내 `self.filter_states["Hold"] = False` → `self.filter_states["중지"] = False`
    *   `on_double_click` 함수 내 `elif status == "Hold"` → `elif status == "중지"`
*   `data_manager.py`:
    *   `update_status_to_hold` 함수 내 `Status` 컬럼 값 `Hold` → `중지`
    *   로그 메시지 `Hold 설정` → `중지 설정`, `Hold -> 생산중` → `중지 -> 생산중`
*   `calendar_view.py`:
    *   `sidebar_frame` 라벨 텍스트 `🛑 Hold 목록` → `🛑 중지 목록`
    *   `update_sidebar` 함수 내 `status_series == 'Hold'` → `status_series == '중지'`
    *   `update_calendar` 함수 내 `~status_series.isin(['Hold', '대기', '완료'])` → `~status_series.isin(['중지', '대기', '완료'])`
    *   `stop_drag` 함수 내 `is_hold_list` 관련 메시지 `Hold 이동 실패` → `중지 이동 실패`
*   `popups/base_popup.py`:
    *   주석 내 `Hold 또는 생산재개` → `중지 또는 생산재개`
    *   `current_status == "Hold"` → `current_status == "중지"`
    *   `messagebox.askyesno("Hold 설정"` → `messagebox.askyesno("중지 설정"`
    *   버튼 텍스트 `text="Hold"` → `text="중지"`
*   `popups/schedule_popup.py`:
    *   `current_status == "Hold"` → `current_status == "중지"`
    *   `title` 설정 시 `Hold 해제` → `중지 해제`
    *   `title_text` 설정 시 `생산 재개 (Hold 해제)` → `생산 재개 (중지 해제)`
    *   `elif self.current_status != "Hold"` → `elif self.current_status != "중지"`
*   `popups/complete_popup.py`: 주석 내 `Hold 버튼` → `중지 버튼`
*   `popups/view_popup.py`: 주석 내 `Hold 버튼` → `중지 버튼`

---


#### 0.1.3 `calendar_view.py` 적용

**Import 추가**
`from styles import COLORS, FONTS`

**헤더 버튼 (이전/다음)**

* 이전 버튼 `hover_color="#D32F2F"` → `COLORS["danger_hover"]`
* 다음 버튼 `hover_color="#1976D2"` → `COLORS["primary_hover"]` (비슷한 파랑 사용)

**새로고침 버튼**

* `fg_color="#555555"` → `COLORS["bg_light"]`

**사이드바/메인 프레임**

* `fg_color="#2b2b2b"` → `COLORS["bg_dark"]`

**Hold / Waiting 목록 프레임**

* `fg_color="#333333"` → `COLORS["bg_medium"]`

**사이드바 라벨 텍스트 색상**

* Hold 목록 제목: `#E04F5F` → `COLORS["danger"]`
* 대기 목록 제목: `#D35400` → `COLORS["warning"]`

**업체명 라벨 (리스트 아이템)**

* `text_color="#3B8ED0"` → `COLORS["primary"]`

**달력 셀**

* 오늘 날짜 테두리: `#2CC985` → `COLORS["success"]`
* 오늘 날짜 배경: `#333333` → `COLORS["bg_medium"]`
* 테두리 색상: `#444444` → `COLORS["border"]`

---

### 0.2. `base_popup.py` 생성 (팝업 표준화)

> **주의:** 기존 `popups` 폴더(또는 모듈) 내의 파일들을 확인하고, 성격이 유사한 팝업만 상속 구조로 변경합니다. `SettingsPopup`은 구조가 상이하므로 **예외**로 두고, 단지 `styles.py`의 색상/폰트만 적용합니다.

#### 0.2.1 파일 생성

* `base_popup.py` 파일을 생성합니다.

#### 0.2.2 `StandardPopup` 클래스 정의

* `ctk.CTkToplevel`을 상속받는 `StandardPopup` 클래스를 작성합니다.

#### 0.2.3 초기화 메서드(`__init__`) 상세 구현

**인자**

* `parent`
* `title`
* `width`
* `height` (필요 시 기본값 포함)

**구현 단계**

1. `super().__init__(parent)` 호출하여 부모 클래스 초기화
2. `self.title(title)` : 윈도우 제목 설정
3. `self.geometry(f"{width}x{height}")` : 윈도우 크기 설정
4. `self.resizable(width=False, height=False)` : 창 크기 조절 비활성화
5. `self.transient(parent)` : 팝업을 부모 창의 종속 윈도우로 설정 (부모 최소화 시 함께 최소화)
6. `self.lift()` : 팝업을 화면 맨 앞으로 가져오기

#### 0.2.4 Standard Layout 메서드: `setup_standard_layout()`

아래와 같은 공통 레이아웃 구성 메서드를 구현합니다.

* **Header Frame**: 팝업 제목 및 강조 라벨 (`setup_header(title)`)
* **Info Frame**: 주요 정보(업체명, 모델명 등) 표시 영역 (`setup_info(info_dict)`)
* **Content/List Frame**: 입력 폼 또는 데이터 리스트 영역
* **Footer Frame**: 저장/닫기 버튼 영역 (`setup_footer(buttons_list)`)

#### 0.2.5 적용 대상 (리팩토링)

아래 팝업들은 `StandardPopup`을 상속받도록 리팩토링합니다.

* `SchedulePopup` (생산 일정 수립)
* `CompletePopup` (생산 완료 처리)
* `ViewPopup` (상세 조회)

#### 0.2.6 예외 대상

* `SettingsPopup`: 기존 `CTkToplevel` 유지 (단, `styles.py`의 색상/폰트는 적용)

---

### 0.3. `toast_manager.py` 생성 (알림 고도화)

#### 0.3.1 파일 생성

* `toast_manager.py` 파일을 생성하고 아래 코드를 작성합니다.

```python
import customtkinter as ctk
from styles import COLORS, FONTS


class ToastNotification(ctk.CTkToplevel):
    def __init__(self, parent, title, message, kind="success"):
        super().__init__(parent)

        # 1. 색상 설정
        color_map = {
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "danger": COLORS["danger"],
            "info": COLORS["primary"],
        }
        accent_color = color_map.get(kind, COLORS["primary"])

        # 2. 창 설정 (테두리 없음, 최상위, 투명 시작)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)

        # 3. 레이아웃 구성
        self.frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_dark"],
            border_width=1,
            border_color=accent_color,
        )
        self.frame.pack(fill="both", expand=True)

        # 좌측 컬러 바
        self.bar = ctk.CTkFrame(
            self.frame,
            width=10,
            fg_color=accent_color,
            corner_radius=0,
        )
        self.bar.pack(side="left", fill="y")

        # 내용 표시
        self.content = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.content.pack(side="left", padx=15, pady=10, fill="both", expand=True)

        ctk.CTkLabel(
            self.content,
            text=title,
            font=FONTS["main_bold"],
            text_color=COLORS["text"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            self.content,
            text=message,
            font=FONTS["small"],
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(fill="x")

        # 4. 위치 계산 (화면 우측 하단)
        self.update_idletasks()
        width = 300
        height = 80
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 60
        self.geometry(f"{width}x{height}+{x}+{y}")

        # 5. 애니메이션 시작
        self.animate_show()

    def animate_show(self):
        """페이드 인 효과"""
        for i in range(0, 11):
            self.after(i * 20, lambda a=i / 10: self.attributes("-alpha", a))
        self.after(3000, self.animate_hide)  # 3초 후 사라짐

    def animate_hide(self):
        """페이드 아웃 효과 후 제거"""
        for i in range(0, 11):
            self.after(i * 30, lambda a=(10 - i) / 10: self.attributes("-alpha", a))
        self.after(350, self.destroy)
```

#### 0.3.2 `main.py` 적용

**Import 추가**

* `main.py` 상단에 다음을 추가합니다.

```python
from toast_manager import ToastNotification
```

**함수 수정**
`load_data_btn_click` 메서드 내 `messagebox.showinfo` 호출 부분을 토스트 알림으로 교체합니다.

```python
# 기존 코드
# messagebox.showinfo("성공", f"데이터를 불러왔습니다.\n({path_name})")

# 변경 코드
ToastNotification(self, "데이터 로드 완료", f"파일: {path_name}", kind="success")
```
