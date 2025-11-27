import platform
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rc
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# [수정] FONT_FAMILY 추가
from styles import COLORS, FONT_FAMILY, FONTS, get_color_str


class GanttView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self._setup_font()

        self.create_widgets()
        
        self.refresh_data()

    def _setup_font(self):
        """OS에 따른 Matplotlib 한글 폰트 설정"""
        # [핵심] 우리가 설정한 FONT_FAMILY(Pretendard)를 최우선으로 적용
        plt.rcParams['font.family'] = FONT_FAMILY
        plt.rcParams['axes.unicode_minus'] = False

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(toolbar, text="📈 Gantt Chart (생산중)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(
            toolbar, text="🔄 새로고침", width=80, height=32,text_color=COLORS["text"],
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
            command=self.refresh_data, font=FONTS["main"]
        ).pack(side="right")

        self.chart_scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.chart_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.chart_content = ctk.CTkFrame(self.chart_scroll_frame, fg_color="transparent")
        self.chart_content.pack(fill="both", expand=True)
        
        self.canvas = None

    def refresh_data(self):
        df = self.dm.df
        
        if df is None or df.empty:
            self._show_empty_msg("데이터가 없습니다.\n좌측 하단의 [데이터 로드] 버튼을 눌러 파일을 불러오세요.")
            return

        processed_df = self._process_data_for_gantt(df)
        
        if processed_df.empty:
            self._show_empty_msg("표시할 '생산중' 데이터가 없습니다.")
            return

        self._draw_gantt_chart(processed_df)

    def _process_data_for_gantt(self, df):
        temp_df = df.copy()
        
        temp_df['start_date'] = pd.to_datetime(temp_df['출고요청일'], errors='coerce')
        temp_df['end_date'] = pd.to_datetime(temp_df['출고예정일'], errors='coerce')
        
        temp_df['Status'] = temp_df['Status'].astype(str).str.strip()
        
        mask_producing = temp_df['Status'] == '생산중'
        mask_dates = temp_df['start_date'].notna()
        
        active_df = temp_df[mask_producing & mask_dates].copy()
        
        if active_df.empty:
            return active_df

        mask_no_end = active_df['end_date'].isna()
        active_df.loc[mask_no_end, 'end_date'] = active_df.loc[mask_no_end, 'start_date']

        active_df['duration'] = (active_df['end_date'] - active_df['start_date']).dt.days
        active_df.loc[active_df['duration'] <= 0, 'duration'] = 1
        
        active_df['label'] = active_df.apply(lambda x: f"No.{x['번호']} [{x['업체명']}]", axis=1)
        
        try:
            active_df['sort_helper'] = pd.to_numeric(active_df['번호'])
        except:
            active_df['sort_helper'] = active_df['번호'].astype(str)
            
        active_df = active_df.sort_values(by='sort_helper', ascending=False)
        
        return active_df

    def _draw_gantt_chart(self, df):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        for w in self.chart_content.winfo_children(): w.destroy()

        bg_color = get_color_str("bg_dark")
        text_color = get_color_str("text")
        
        ITEM_HEIGHT_INCH = 0.5
        MIN_ITEMS = 10 
        
        item_count = len(df)
        display_count = max(item_count, MIN_ITEMS)
        fig_height = 2 + (display_count * ITEM_HEIGHT_INCH)
        
        fig, ax = plt.subplots(figsize=(10, fig_height), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        y_labels = df['label'].tolist()
        start_dates = mdates.date2num(df['start_date'])
        durations = df['duration'].tolist()
        
        color = get_color_str("success")
        
        y_pos = range(len(y_labels))
        
        ax.barh(y_pos, durations, left=start_dates, height=0.4, align='center', color=color, edgecolor=bg_color)
        
        min_date = df['start_date'].min()
        max_date = df['end_date'].max()
        interval = 1
        if pd.notna(min_date) and pd.notna(max_date):
            total_days = (max_date - min_date).days
            MAX_TICKS = 15
            if total_days > MAX_TICKS:
                interval = int(total_days / MAX_TICKS) + 1
        
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels, color=text_color, fontsize=10)
        
        ax.set_ylim(-0.5, display_count - 0.5)

        grid_color = get_color_str("text_dim")
        
        ax.grid(True, axis='x', linestyle='--', alpha=0.3, color=grid_color)
        ax.spines['bottom'].set_color(grid_color)
        ax.spines['top'].set_color(bg_color)
        ax.spines['left'].set_color(bg_color)
        ax.spines['right'].set_color(bg_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        ax.set_title(f"생산 진행 현황 (총 {len(df)}건)", color=text_color, fontsize=14, pad=15)
        
        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_content)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _show_empty_msg(self, msg):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        
        for w in self.chart_content.winfo_children(): w.destroy()
        
        msg_frame = ctk.CTkFrame(self.chart_content, fg_color="transparent")
        msg_frame.pack(expand=True, fill="both", pady=50)
        
        ctk.CTkLabel(msg_frame, text="⚠️", font=("Emoji", 48)).pack(pady=(0, 10))
        ctk.CTkLabel(msg_frame, text=msg, font=FONTS["header"], text_color=COLORS["text_dim"]).pack()