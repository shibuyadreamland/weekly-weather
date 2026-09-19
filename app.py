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

# --- サイドバーに日時（秒付き動的時計）と切り替え可能なカレンダーを追加（日本時間） ---
st.sidebar.header("カレンダー・時計")
JST = timezone(timedelta(hours=+9), 'JST')

# 秒数をリアルタイム更新するためのプレースホルダー（空きスペース）
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
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.button("◀ 前月", use_container_width=True):
        st.session_state.cal_month -= 1
        if st.session_state.cal_month < 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
with col_s2:
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


# --- メイン画面の処理（天気予報：API制限を回避する内蔵座標方式） ---
st.title("週間天気ダッシュボード")

def get_weather_info(code):
    if code == 0: return "☀️ 晴れ"
    elif code in [1, 2, 3]: return "🌤️ 曇り"
    elif code in [45, 48]: return "🌫️ 霧"
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]: return "☔ 雨"
    elif code in [71, 73, 75, 77, 85, 86]: return "🌨️ 雪"
    elif code in [95, 96, 99]: return "⛈️ 雷雨"
    else: return "❓ 不明"

HEADERS = {'User-Agent': 'MyWeeklyWeatherWeb/1.0'}

CITY_COORDS = {
    "東京": (35.6895, 139.6917),
    "横浜": (35.4437, 139.6380),
    "大阪": (34.6937, 135.5022),
    "名古屋": (35.1815, 136.9066),
    "札幌": (43.0618, 141.3543),
    "福岡": (33.5902, 130.4017),
    "京都": (35.0116, 135.7681),
    "神戸": (34.6901, 135.1956),
    "広島": (34.3853, 132.4553),
    "仙台": (38.2682, 140.8694)
}

def get_coordinates(city_name):
    clean_name = city_name.strip()
    if clean_name in CITY_COORDS:
        return CITY_COORDS[clean_name][0], CITY_COORDS[clean_name][1], None
    else:
        return None, None, "登録されていない地名です（東京、横浜、大阪、名古屋、札幌、福岡、京都、神戸、広島、仙台からお選びください）"

@st.cache_data(ttl=3600)
def fetch_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode()), None
    except Exception as e:
        return None, f"エラー: {e}"

if 'target_city' not in st.session_state:
    st.session_state.target_city = "東京"

col_m1, col_m2 = st.columns([3, 1])
with col_m1:
    input_city = st.text_input("地名を入力", value=st.session_state.target_city, label_visibility="collapsed")
with col_m2:
    if st.button("検索", use_container_width=True):
        st.session_state.target_city = input_city
        st.rerun()

if st.session_state.target_city:
    lat, lon, geo_err = get_coordinates(st.session_state.target_city)
    if lat is None:
        st.error(f"【エラー】 {geo_err}")
    else:
        data, weather_err = fetch_weather(lat, lon)
        if data is not None:
            st.subheader(f"「{st.session_state.target_city}」の週間天気予報")
            daily = data.get("daily", {})
            times = daily.get("time", [])
            codes = daily.get("weathercode", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            
            cols = st.columns(len(times))
            for i, t in enumerate(times):
                with cols[i]:
                    st.markdown(f"**{t}**")
                    st.write(get_weather_info(codes[i]))
                    st.markdown(f"最高: {tmax[i]}°C")
                    st.markdown(f"最低: {tmin[i]}°C")
        else:
            st.error(f"【エラー】 {weather_err}")

# 秒数をリアルタイムで更新し続けるループ処理
while True:
    now = datetime.now(JST)
    clock_placeholder.write(f"現在日時: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    time.sleep(1)
