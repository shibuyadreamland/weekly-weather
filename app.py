import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
import calendar
from calendar import Calendar
import jpholiday
import time

# ページ設定（幅広モード）
st.set_page_config(page_title="週間天気ダッシュボード", layout="wide")

# --- サイドバーに日時（秒付き）と常時表示カレンダーを追加（日本時間） ---
st.sidebar.header("カレンダー・時計")
JST = timezone(timedelta(hours=+9), 'JST')

# 時計をリアルタイム表示するための空きスペース（プレースホルダー）を作る
clock_placeholder = st.sidebar.empty()

# セッションステート（状態管理）を使って表示する年・月を記憶する
if 'cal_year' not in st.session_state:
    now_init = datetime.now(JST)
    st.session_state.cal_year = now_init.year
if 'cal_month' not in st.session_state:
    now_init = datetime.now(JST)
    st.session_state.cal_month = now_init.month

st.sidebar.subheader("カレンダー")

# ボタンの文字が途切れないように左右に配置
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("◀ 前月", use_container_width=True):
        st.session_state.cal_month -= 1
        if st.session_state.cal_month < 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
with col2:
    if st.button("次月 ▶", use_container_width=True):
        st.session_state.cal_month += 1
        if st.session_state.cal_month > 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1

# 現在表示している年月を見出しとして表示
st.sidebar.markdown(f"<p style='text-align: center; font-weight: bold; font-size: 16px; margin: 10px 0;'>{st.session_state.cal_year}年 {st.session_state.cal_month}月</p>", unsafe_allow_html=True)

# 選択された年月に合わせてカレンダーを生成（前後月の日付を含む）
cal = Calendar(firstweekday=calendar.SUNDAY)
month_weeks = cal.monthdatescalendar(st.session_state.cal_year, st.session_state.cal_month)

html_table = '<table class="month" style="width: 100%; border-collapse: collapse; text-align: center; font-size: 14px;">'
html_table += '<tr><th style="color: #ff4b4b; padding: 4px;">Sun</th><th style="padding: 4px;">Mon</th><th style="padding: 4px;">Tue</th><th style="padding: 4px;">Wed</th><th style="padding: 4px;">Thu</th><th style="padding: 4px;">Fri</th><th style="color: #2980b9; padding: 4px;">Sat</th></tr>'

for week in month_weeks:
    html_table += '<tr>'
    for i, d in enumerate(week):
        style = "padding: 4px;"
        is_current_month = (d.month == st.session_state.cal_month)
        
        if is_current_month:
            if i == 0 or jpholiday.is_holiday(d):
                style += " color: #ff4b4b; font-weight: bold;"
            elif i == 6:
                style += " color: #2980b9; font-weight: bold;"
        else:
            style += " color: #d3d3d3;"
            
        html_table += f'<td style="{style}">{d.day}</td>'
    html_table += '</tr>'
html_table += '</table>'

st.sidebar.markdown(html_table, unsafe_allow_html=True)

# メイン画面の処理（天気予報など）
st.title("週間天気ダッシュボード")

# 検索フォームなどのコードが続く場合はここに記述
# （※もし元のコードがある場合はそのまま下部に残してください）

# 最後に、時計の表示を1秒ごとに更新し続ける処理
while True:
    now = datetime.now(JST)
    clock_placeholder.write(f"現在日時: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    time.sleep(1)
