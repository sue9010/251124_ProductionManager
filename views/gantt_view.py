import platform
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk
import matplotlib.dates as mdates
# Matplotlib 관련 임포트
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rc
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from styles import COLORS, FONTS


class GanttView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 한글 폰트 설정 (Matplotlib)
        self._setup_font()

        self.create_widgets()
        
        # 초기 데이터 로드
        self.refresh_data()

    def _setup_font(self):
        """OS에 따른 Matplotlib 한글 폰트 설정"""
        system_name = platform.system()
        if system_name == 'Windows':
            plt.rcParams['font.family'] = 'Malgun Gothic'
        elif system_name == 'Darwin': # Mac
            plt.rcParams['font.family'] = 'AppleGothic'
        else:
            plt.rcParams['font.family'] = 'NanumGothic'
        plt.rcParams['axes.unicode_minus'] = False

    def create_widgets(self):
        # 1. 상단 툴바
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(toolbar, text="📈 Gantt Chart", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(
            toolbar, text="🔄 새로고침", width=80, height=32,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            command=self.refresh_data
        ).pack(side="right")

        # 2. 차트 영역 (여기에 캔버스가 들어감)
        self.chart_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 빈 캔버스 자리 표시
        self.canvas = None

    def refresh_data(self):
        """데이터를 로드하고 차트를 다시 그립니다."""
        df = self.dm.df
        if df.empty:
            self._show_empty_msg("표시할 데이터가 없습니다.")
            return

        # 데이터 전처리: 날짜 변환 및 필터링
        processed_df = self._process_data_for_gantt(df)
        
        if processed_df.empty:
            self._show_empty_msg("일정 정보가 있는 데이터가 없습니다.\n(출고요청일/예정일 필요)")
            return

        self._draw_gantt_chart(processed_df)

    def _process_data_for_gantt(self, df):
        """간트 차트용 데이터 가공"""
        # 1. 사본 생성
        temp_df = df.copy()
        
        # 2. 날짜 형식 변환 (에러 시 NaT)
        temp_df['start_date'] = pd.to_datetime(temp_df['출고요청일'], errors='coerce')
        temp_df['end_date'] = pd.to_datetime(temp_df['출고예정일'], errors='coerce')
        
        # 3. 유효한 데이터 필터링
        # 시작일은 필수, 종료일이 없으면 오늘 날짜(진행중) 또는 시작일(점)로 대체 고려
        # 여기서는 시작일이 있는 데이터만 사용
        temp_df = temp_df.dropna(subset=['start_date'])
        
        # 4. 종료일 처리: 종료일이 없으면 -> 시작일 + 1일 (최소 길이)
        # 완료된 건은 출고일이 있다면 그걸 써야겠지만, 일단 예정일 우선
        mask_no_end = temp_df['end_date'].isna()
        temp_df.loc[mask_no_end, 'end_date'] = temp_df.loc[mask_no_end, 'start_date'] + timedelta(days=1)
        
        # 5. 기간 계산 (matplotlib barh용 width)
        temp_df['duration'] = (temp_df['end_date'] - temp_df['start_date']).dt.days
        # 최소 1일 보장
        temp_df.loc[temp_df['duration'] <= 0, 'duration'] = 1
        
        # 6. Y축 라벨 생성 (업체명 + 모델명)
        temp_df['label'] = temp_df.apply(lambda x: f"[{x['업체명']}] {x['모델명']}", axis=1)
        
        # 7. 정렬 (날짜순 -> 차트에서는 위에서부터 그려지므로 역순 필요할 수 있음)
        temp_df = temp_df.sort_values(by='start_date', ascending=False) # 늦은 날짜가 위로? 보통 빠른게 위로 가려면 ascending=False로 해서 barh 0번부터..
        # Matplotlib barh는 밑에서부터 그림 -> 빠른 날짜가 위로 오게 하려면:
        # sort ascending=False (늦은게 먼저 나옴 -> 밑에 깔림 -> 빠른게 위에?) 
        # 헷갈리므로 일단 날짜순 정렬하고 인덱스 리셋
        
        # 너무 많은 데이터는 차트가 복잡해지므로 최근 20개 또는 진행중인 것만 필터링 권장
        # 여기서는 '완료' 제외하고 '진행중/대기/중지' 위주로 30개만 자름
        active_df = temp_df[~temp_df['Status'].isin(['완료'])].head(30)
        
        return active_df

    def _draw_gantt_chart(self, df):
        """Matplotlib을 이용해 차트 그리기"""
        # 기존 캔버스 제거
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        # --- 스타일 설정 ---
        bg_color = COLORS["bg_dark"]
        text_color = COLORS["text"]
        
        # Figure 생성
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # --- 데이터 매핑 ---
        y_labels = df['label'].tolist()
        start_dates = mdates.date2num(df['start_date'])
        durations = df['duration'].tolist()
        colors = self._get_colors_by_status(df['Status'])
        
        # Y축 위치
        y_pos = range(len(y_labels))
        
        # --- 막대 그리기 (Barh) ---
        bars = ax.barh(y_pos, durations, left=start_dates, height=0.6, align='center', color=colors, edgecolor=COLORS["bg_dark"])
        
        # --- 축 설정 ---
        # X축: 날짜 포맷
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3)) # 3일 간격
        
        # Y축: 항목 라벨
        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels, color=text_color, fontsize=10)
        
        # 그리드 및 테두리
        ax.grid(True, axis='x', linestyle='--', alpha=0.3, color=COLORS["text_dim"])
        ax.spines['bottom'].set_color(COLORS["text_dim"])
        ax.spines['top'].set_color(bg_color)
        ax.spines['left'].set_color(bg_color)
        ax.spines['right'].set_color(bg_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        # 제목
        ax.set_title(f"생산 일정 현황 (진행 중 {len(df)}건)", color=text_color, fontsize=14, pad=15)
        
        # 레이아웃 조정
        plt.tight_layout()

        # --- Tkinter 캔버스에 통합 ---
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _get_colors_by_status(self, status_series):
        """상태별 막대 색상 리스트 반환"""
        color_map = []
        for status in status_series:
            s = str(status).strip()
            if s == "생산중": color_map.append(COLORS["success"]) # 초록
            elif s == "대기": color_map.append(COLORS["warning"]) # 주황
            elif s in ["Hold", "작업 중지"]: color_map.append(COLORS["danger"]) # 빨강
            elif s == "완료": color_map.append(COLORS["text_dim"]) # 회색
            else: color_map.append(COLORS["primary"]) # 파랑 (접수 등)
        return color_map

    def _show_empty_msg(self, msg):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        
        # 메시지 라벨 표시
        for w in self.chart_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.chart_frame, text=msg, font=FONTS["header"], text_color=COLORS["text_dim"]).pack(expand=True)