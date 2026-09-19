import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
import calendar
import jpholiday

# ページ設定（幅広モード）
st.set_page_config(page_title="週間天気ダッシュボード", layout="wide")
# --- サイドバーに日時と常時表示カレンダーを追加（日本時間） ---
st.sidebar.header("カレンダー・時計")
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
st.sidebar.write(f"現在日時: {now.strftime('%Y年%m月%d日 %H:%M')}")

st.sidebar.subheader("今月のカレンダー")

# カレンダーのデータを取得して自作のHTMLテーブルを作成
cal_matrix = calendar.monthcalendar(now.year, now.month)
html_table = '<table class="month" style="width: 100%; border-collapse: collapse; text-align: center; font-size: 14px;">'
html_table += '<tr><th style="color: #ff4b4b; padding: 4px;">Sun</th><th style="padding: 4px;">Mon</th><th style="padding: 4px;">Tue</th><th style="padding: 4px;">Wed</th><th style="padding: 4px;">Thu</th><th style="padding: 4px;">Fri</th><th style="color: #2980b9; padding: 4px;">Sat</th></tr>'

for week in cal_matrix:
    html_table += '<tr>'
    for i, day in enumerate(week):
        if day == 0:
            html_table += '<td style="padding: 4px;"></td>'
        else:
            # どの日付か判定するためのお皿を用意
            current_date = datetime(now.year, now.month, day).date()
            style = "padding: 4px;"
            
            # 日曜日(i==0) または 祝日の場合 -> 赤色
            if i == 0 or jpholiday.is_holiday(current_date):
                style += " color: #ff4b4b; font-weight: bold;"
            # 土曜日(i==6)の場合 -> 青色
            elif i == 6:
                style += " color: #2980b9; font-weight: bold;"
                
            html_table += f'<td style="{style}">{day}</td>'
    html_table += '</tr>'
html_table += '</table>'

st.sidebar.markdown(html_table, unsafe_allow_html=True)
st.sidebar.markdown(styled_html, unsafe_allow_html=True)
def get_weather_info(code):
    if code == 0: return "☀️ 晴れ"
    elif code in [1, 2, 3]: return "⛅ 曇り"
    elif code in [45, 48]: return "🌫️ 霧"
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]: return "☔ 雨"
    elif code in [71, 73, 75, 77, 85, 86]: return "⛄ 雪"
    elif code in [95, 96, 99]: return "⛈️ 雷雨"
    else: return "❓ 不明"

HEADERS = {'User-Agent': 'MyWeeklyWeatherWeb/1.0'}

def get_coordinates(city_name):
    safe_name = urllib.parse.quote(city_name)
    url = f"https://nominatim.openstreetmap.org/search?q={safe_name}&format=json&limit=1"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            if len(data) > 0:
                result = data[0]
                return float(result["lat"]), float(result["lon"]), None
            return None, None, "地名が見つかりません"
    except Exception as e:
        return None, None, f"エラー: {e}"

def fetch_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode()), None
    except Exception as e:
        return None, f"エラー: {e}"

st.title("週間天気ダッシュボード")

# 検索フォーム
col1, col2 = st.columns([3, 1])
with col1:
    city_name = st.text_input("地名を入力", value="東京", label_visibility="collapsed")
with col2:
    search_clicked = st.button("検索", use_container_width=True)

if city_name:
    lat, lon, geo_err = get_coordinates(city_name)
    if lat is None:
        st.error(f"【エラー】{geo_err}")
    else:
        data, weather_err = fetch_weather(lat, lon)
        if not data:
            st.error(f"【エラー】{weather_err}")
        else:
            st.subheader(f"「{city_name}」の7日間天気予報")
            
            # 7日分を横並びにするカラムを作成
            cols = st.columns(7)
            daily = data["daily"]
            weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
            
            for i in range(7):
                date_str = daily["time"][i]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                weekday_idx = date_obj.weekday()
                
                # 曜日の色分け用HTML（StreamlitではMarkdown+HTMLで色付け可能）
                if jpholiday.is_holiday(date_obj.date()) or weekday_idx == 6:
                    color = "red"
                elif weekday_idx == 5:
                    color = "blue"
                else:
                    color = "black"
                    
                display_date = f"<span style='color:{color}; font-weight:bold;'>{date_obj.strftime('%m/%d')}({weekdays_jp[weekday_idx]})</span>"
                
                w_code = daily["weathercode"][i]
                max_temp = daily["temperature_2m_max"][i]
                min_temp = daily["temperature_2m_min"][i]
                emoji_text = get_weather_info(w_code)
                
                # 各カラムに情報を書き込む
                with cols[i]:
                    st.markdown(display_date, unsafe_allow_html=True)
                    st.markdown(f"### {emoji_text}")
                    st.metric(label="最高", value=f"{max_temp}℃")
                    st.metric(label="最低", value=f"{min_temp}℃")
