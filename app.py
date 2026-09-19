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
st.set_page_config(page_title="天気ダッシュボード", layout="wide")

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


# --- メイン画面の処理（天気予報：世界中対応 ＆ 時間ごとの変化表示） ---
st.title("天気ダッシュボード")

def get_weather_info(code):
    if code == 0: return "☀️ 快晴"
    elif code == 1: return "🌤️ 概ね晴れ"
    elif code == 2: return "⛅ 晴時々曇"
    elif code == 3: return "☁️ 曇り"
    elif code in [45, 48]: return "🌫️ 霧・濃霧"
    elif code in [51, 53, 55]: return "🌧️ 霧雨"
    elif code in [56, 57]: return "🧊 凍結性霧雨"
    elif code == 61: return "☔ 弱雨"
    elif code == 63: return "☔ 雨"
    elif code == 65: return "🌧️ 強い雨"
    elif code in [66, 67]: return "❄️ 凍結性降雨"
    elif code == 71: return "🌨️ 弱雪"
    elif code == 73: return "❄️ 雪"
    elif code == 75: return "❄️ 強い雪"
    elif code == 77: return "❄️ 霧雪"
    elif code in [80, 81]: return "🌦️ にわか雨"
    elif code == 82: return "🌧️ 激しいにわか雨"
    elif code in [85, 86]: return "🌨️ にわか雪"
    elif code == 95: return "⚡ 雷雨"
    elif code in [96, 99]: return "⛈️ 激しい雷雨"
    else: return "❓ 不明"

HEADERS = {'User-Agent': 'MyWeeklyWeatherWeb/1.0'}

@st.cache_data(ttl=3600)
def get_coordinates(city_name):
    safename = urllib.parse.quote(city_name)
    url = f"https://nominatim.openstreetmap.org/search?q={safename}&format=json&limit=1"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            if len(data) > 0:
                result = data[0]
                return float(result["lat"]), float(result["lon"]), None
        return None, None, "地名が見つかりませんでした。別の表記でお試しください。"
    except Exception as e:
        return None, None, f"エラー: {e}"

@st.cache_data(ttl=3600)
def fetch_weather(lat, lon):
    # 週間天気(daily)に加え、時間ごと(hourly)の天気コード、気温、降水確率を取得
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&hourly=temperature_2m,weathercode,precipitation_probability&timezone=Asia%2FTokyo"
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
    input_city = st.text_input("世界中の地名を入力", value=st.session_state.target_city, label_visibility="collapsed")
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
            st.subheader(f"「{st.session_state.target_city}」の天気予報")
            
            # タブを使って「週間予報」と「時間ごとの予報」を切り替えられるようにする
            tab1, tab2 = st.tabs(["📅 週間天気予報", "⏱️ 時間ごとの天気変化（24時間）"])
            
            with tab1:
                daily = data.get("daily", {})
                times = daily.get("time", [])
                codes = daily.get("weathercode", [])
                tmax = daily.get("temperature_2m_max", [])
                tmin = daily.get("temperature_2m_min", [])
                
                cols = st.columns(len(times))
                for i, t in enumerate(times):
                    with cols[i]:
                        date_obj = datetime.strptime(t, "%Y-%m-%d")
                        wd = ["(日)", "(月)", "(火)", "(水)", "(木)", "(金)", "(土)"][date_obj.isoweekday() % 7]
                        st.markdown(f"**{t} {wd}**")
                        st.write(get_weather_info(codes[i]))
                        st.markdown(f"最高: {tmax[i]}°C")
                        st.markdown(f"最低: {tmin[i]}°C")
            
            with tab2:
                st.write("直近24時間の天気・気温・降水確率の推移です。")
                hourly = data.get("hourly", {})
                h_times = hourly.get("time", [])[:24]
                h_codes = hourly.get("weathercode", [])[:24]
                h_temps = hourly.get("temperature_2m", [])[:24]
                h_pops = hourly.get("precipitation_probability", [])[:24]
                
                # 見やすいようにスクロール可能な横並び、または表形式で表示
                h_cols = st.columns(min(len(h_times), 8))
                for i, ht in enumerate(h_times):
                    # 最初の8時間分をピックアップしてカード形式で表示
                    col_idx = i % len(h_cols)
                    if i > 0 and col_idx == 0:
                        # 9時間目以降の改行表現など
                        pass
                    
                    dt_str = datetime.fromisoformat(ht).strftime('%m/%d %H時')
                    with h_cols[col_idx]:
                        st.markdown(f"**{dt_str}**")
                        st.write(get_weather_info(h_codes[i]))
                        st.markdown(f"気温: {h_temps[i]}°C")
                        st.markdown(f"降水: {h_pops[i]}%")
                        st.markdown("---")
        else:
            st.error(f"【エラー】 {weather_err}")

# 秒数をリアルタイムで更新し続けるループ処理
while True:
    now = datetime.now(JST)
    clock_placeholder.write(f"現在日時: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    time.sleep(1)
