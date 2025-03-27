import streamlit as st

#サイドバーの状態を保持
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'
#サイドバーの状態を切り替え
def toggle_sidebar():
    if st.session_state.sidebar_state == 'expanded':
        st.session_state.sidebar_state = 'collapsed'
    else:
        st.session_state.sidebar_state = 'expanded'


import googlemaps
import requests
import json
from openai import OpenAI
import folium
from datetime import datetime
from streamlit_folium import st_folium
#DBへの接続、関数呼び出し
from database import insert_route
#csv吐き出す関数の呼び出し
from database import export_to_csv

#環境変数の読み込み----------------------------------------
import os
from dotenv import load_dotenv
from datetime import datetime
# #サイドバーを開いた状態で表示
# st.set_page_config(initial_sidebar_state='expanded')
#サイドバーの状態を保持
# if 'sidebar_state' not in st.session_state:
#     st.session_state.sidebar_state = 'expanded'
# #サイドバーの状態を切り替え
# def toggle_sidebar():
#     if st.session_state.sidebar_state == 'expanded':
#         st.session_state.sidebar_state = 'collapsed'
#     else:
#         st.session_state.sidebar_state = 'expanded'
# 環境変数を読み込む
load_dotenv('.env')
# Google Maps APIキー
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
# NAVITIME APIキー
NAVITIME_API_KEY = os.getenv("NAVITIME_API_KEY")
#天気APIキー
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
#PERPLEXITYAPIキー
YOUR_API_KEY = os.getenv("PERPLEXITY_API_KEY")

client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")
#--------------------------------------------------------
# UI/UX設計 サイドバーの設計 タイトル--------------------------------------------------------------------------------

# Streamlit でのフロントエンドUI
#スタイル変更定義
primaryColor = "#DDA0DD"
backgroundColor = "#FFF0F5"
secondaryBackgroundColor = "#F8F8FF"
textColor = "#483D8B"
font = "Palatino"

#カスタムCSS
st.markdown(
    f"""
    <style>
        /* タイトルの色を変更 */
        .stApp h1 {{
            color: {textColor};
            font-family: {font}, serif;
        }}

        /* サイドバーの背景色 */
        [data-testid="stSidebar"] {{
            background-color: {secondaryBackgroundColor} !important;
        }}

        /* 全体の背景色 */
        .stApp {{
            background-color: {backgroundColor} !important;
        }}

        /* ボタンのデザイン */
        .stButton>button {{
            background-color: {primaryColor} !important;
            color: white !important;
            border-radius: 10px !important;
        }}

    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.title("ルート提案アプリ")
#ユーザー名
user_name = st.sidebar.text_input('ユーザー名を入力してください（例）いわちゃん')
# 出発地と到着地の入力フォーム
start_address = st.sidebar.text_input("出発地", "浜松町駅").strip()
goal_address = st.sidebar.text_input("到着地", "新宿駅").strip()
# 出発時間と到着時間の選択
time_option = st.sidebar.radio("時間を選択", ["出発時間", "到着時間"])
start_time, goal_time = None, None  # デフォルト値は None
if time_option == "出発時間":
    start_date = st.sidebar.date_input("出発日", datetime.today())
    input_time = st.sidebar.text_input("出発時刻 (形式: HH:MM:SS (例)14:00発の場合、14:00:00)", "").strip()
    if input_time:
        try:
            datetime.strptime(input_time, "%H:%M:%S")
            start_time = f"{start_date}T{input_time}"
        except ValueError:
            st.sidebar.error("時刻の形式が正しくありません。形式はHH:MM:SSです。")
            start_time = None
elif time_option == "到着時間":
    goal_date = st.sidebar.date_input("到着日", datetime.today())
    input_time = st.sidebar.text_input("到着時刻 (形式: HH:MM:SS(例)14:00着の場合、14:00:00)", "").strip()
    if input_time:
        try:
            datetime.strptime(input_time, "%H:%M:%S")
            goal_time = f"{goal_date}T{input_time}"
        except ValueError:
            st.sidebar.error("時刻の形式が正しくありません。形式はHH:MM:SSです。")
            goal_time = None
# 機能Ａ　検索ボタン（ここのボタンを押すと検索ボタンを押した後の処理に飛び、サイドバーを閉じる）
with st.sidebar.form("route_search_form"):
        submitted = st.form_submit_button("検索する",on_click=toggle_sidebar)

#--------------------------------------------------------------------------------------------------------
#経度・緯度取得_geo coding---------------------------------------------------------------------------------
def get_lat_lon(address):
    try:
        result = gmaps.geocode(address, language="ja")
        if result:
            lat = result[0]["geometry"]["location"]["lat"]
            lon = result[0]["geometry"]["location"]["lng"]
            return lat, lon
    except Exception as e:
        st.error(f"エラー: {e}")
    return None, None
start_lat, start_lon = get_lat_lon(start_address)
goal_lat, goal_lon = get_lat_lon(goal_address)
#--------------------------------------------------------------------------------------------------------

# 天気情報を取得する処理-------------------------------------------------------------------------------------
def get_weather(lat, lon):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat}, {lon}&days=1&lang=ja"
    try:
        response_weather = requests.get(url)
        if response_weather.status_code != 200:
            return None
        return response_weather.json()
    except requests.exceptions.RequestException as e:
        st.error(f"天気情報の取得に失敗しました: {e}")
        return None
# 天気情報からアドバイスを生成する処理--------------------------------------------------------------------------
def give_advice(forecast, input_time):
    input_hour = datetime.strptime(input_time, "%H:%M:%S").hour
    upcoming_hours = [hour for hour in forecast if input_hour <= datetime.strptime(hour["time"], "%Y-%m-%d %H:%M").hour < input_hour + 3]
    if not upcoming_hours:
        return "天気データが取得できませんでした。"
    need_umbrella = any(hour["chance_of_rain"] > 50 for hour in upcoming_hours)
    avg_temp = sum(hour["temp_c"] for hour in upcoming_hours) / len(upcoming_hours)
    advice = ""
    if need_umbrella:
        advice += "傘を持って行ったほうが良いかも。\n"
    else:
        advice += "傘は必要ないかな。\n"
    if avg_temp < 10:
        advice += "寒いので暖かい服を着ましょう。<br>今日も頑張っていってらっしゃい！\n"
    elif avg_temp < 20:
        advice += "少し肌寒いので軽い上着を着るのが良いでしょう。<br>今日も頑張っていってらっしゃい！\n"
    else:
        advice += "暖かいので軽装で大丈夫です。<br>今日も頑張っていってらっしゃい！\n"
    return advice
#----------------------------------------------------------------------------------------------------------

#Route取得する処理-------------------------------------------------------------------------------------------
if not start_lat or not goal_lat:
    st.error("住所を正しく入力してください。")
else:
    # ルート検索用の関数
    def search_routes(start_lat, start_lon, goal_lat, goal_lon, start_time, goal_time):
        root_url = "https://navitime-route-totalnavi.p.rapidapi.com/route_transit"
        headers = {
            "X-RapidAPI-Key": NAVITIME_API_KEY,
            "X-RapidAPI-Host": "navitime-route-totalnavi.p.rapidapi.com"
        }
        # パラメータを組み立てる（start_time か goal_time のどちらかのみ）
        params = {
            "start": f"{start_lat},{start_lon}",
            "goal": f"{goal_lat},{goal_lon}",
            "coord_unit": "degree",
            "datum": "wgs84",
            "order": "time_optimized",
            "term": "1440",
            "limit": "5",
            "shape": "true",
        }
        if start_time:
            params["start_time"] = start_time
        elif goal_time:
            params["goal_time"] = goal_time
        else:
            st.error("出発時間または到着時間を入力してください。")
            return None
        try:
            response = requests.get(root_url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"APIエラー: {response.status_code}")
                st.write(response.text)
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"通信エラー: {e}")
            return None
#---------------------------------------------------------------------------------------

#jsonResponseから最適なルートを5つ取り出す関数------------------------------------------------
def extract_route_info(response_json, top_n=5):
    routes = response_json.get("items", [])[:top_n]
    extracted_routes = []
    for route in routes:
        sections = route.get("sections", [])
        stations = [s for s in sections if s.get("type") == "point" and "station" in s.get("node_types", [])]
        if not stations:
            print("データがありません")
            continue
        # 出発時間と到着時間
        start_time = (route.get("summary", {}).get("move", {}).get("from_time", ""))
        goal_time = (route.get("summary", {}).get("move", {}).get("to_time", ""))
        # 出発駅・到着駅を取得
        start_station = stations[0].get("name", "")
        goal_station = stations[-1].get("name", "")
        # 乗換駅の取得
        transfer_stations = [s.get("name", "") for s in stations[1:-1]]
        # 所要時間（分）
        duration = route.get("summary", {}).get("move", {}).get("time", "")
        # 費用（円）
        fare = route.get("summary", {}).get("move", {}).get("fare", {}).get("unit_0", "")
        fare = int(fare)
        extracted_routes.append({
            "出発時刻": start_time,
            "到着時刻": goal_time,
            "出発駅": start_station,
            "到着駅": goal_station,
            "乗換駅": transfer_stations,
            "所要時間": duration,
            "費用": fare
        })
    return extracted_routes
#--------------------------------------------------------------------------------------------
destination = goal_address
information = "コンセント使用可能な仕事ができる場所"
pieces = "5箇所"
however = "コンセントが使える場所がカウンター席かテーブル席か分かるようにして、お店の住所も表示してください"
# Perplexity API 呼び出し関数
def query_perplexity(destination, information, pieces, however):
    # API に渡すメッセージの定義（システムとユーザーメッセージ）
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{destination} 周辺徒歩5分圏内の、{information}を{pieces}教えてください。ただし、{however}"
            ),
        },
    ]
    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=messages,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"エラー: {str(e)}"
result = query_perplexity(destination, information, pieces, however)

#UI/UX設計------------------------------------------------------------------------------------
# 機能Ａ　検索ボタン
# with st.sidebar.form("route_search_form"):
#     submitted = st.form_submit_button("検索する")
#検索ボタンが押された後の処理
if submitted:
        response_json = search_routes(start_lat, start_lon, goal_lat, goal_lon, start_time, goal_time) #経度緯度を取得

        # 目的地の天気情報を取得
        weather_info = get_weather(goal_lat, goal_lon)
        data = get_weather(goal_lat, goal_lon)
        forecast = data["forecast"]["forecastday"][0]["hour"]
        if weather_info:
            weather_desc = weather_info["current"]["condition"]["text"]
            temp = weather_info["current"]["temp_c"]
            st.subheader("☀️目的地の天気☔️")
            st.info(f"{weather_desc}, 気温: {temp}°C")
        # アドバイスの表示
        advice = give_advice(forecast, input_time).replace("<br>", "")
        st.info(f"{advice}")

#ルートの取得
        st.subheader("🚉 電車ルート 🚉")
        if response_json and "items" in response_json:
            best_routes = extract_route_info(response_json)
            for idx, route in enumerate(best_routes):
                with st.container():
                    st.markdown(f"## ルート {idx+1}")
            # 2カラムレイアウト
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown("🚆 **出発駅**")
                    st.info(f"{route.get('出発駅', 'データなし')} 駅")
                    st.markdown("🎯 **到着駅**")
                    st.info(f"{route.get('到着駅', 'データなし')} 駅")
                with col2:
                    st.markdown("🔄 **乗換駅**")
                    transfers = ", ".join(route.get('乗換駅', ['データなし']))
                    st.success(f"{transfers}" if transfers else "なし")
                    st.markdown("⏳ **所要時間**")
                    st.warning(f"{route.get('所要時間', 'データなし')} 分")
                    st.markdown("💰 **費用**")
                    st.error(f"{route.get('費用', 'データなし')} 円")

                    st.divider()  # ルート間に区切り線を入れる
                
        #データベースへの登録------------------------------
        #ユーザー名（将来的には社員情報と接続）
        user_name = user_name
        #日付（出発日付からデータに合わせて修正して取得）
        date = start_time
        #ルート情報をデータベースに登録
        if best_routes:
            try:
                for route in best_routes:
                    insert_route(
                        user_name=user_name,
                        date=date,
                        goal_address=goal_address,
                        start_station=route["出発駅"],
                        goal_station=route["到着駅"],
                        transfer_stations=route["乗換駅"],
                        fare=route["費用"],
                        duration=route["所要時間"]
                    )
                    st.success("ルート情報をデータベースに登録しました。")
            except Exception as e:
                st.error(f"データベース登録エラー: {e}")
        else:
            st.write("登録するルートがありません。")
            # CSVに出力
            # ここのボタンを押すとCSVに出力
            # with st.form("route_search_form"):
            #     submitted = st.form_submit_button("出力")
            #     export_to_csv("route_export.csv")

        # 目的地のワークスペース情報
        st.subheader("☕️ワークスペース ＆ コンセント情報🔌")
        st.info(result)
            

            # folium_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)
            # #ルートの座標を地図に描画
            # for shape in route.get("shapes", []):
            #     if isinstance(shape, dict) and 'coordinates' in shape:
            #         folium.PolyLine(locations=shape["coordinates"], color="blue", weight=3, opacity=1).add_to(folium_map)
            # #地図の表示
            # st.title("選択したルートの地図")
            # st_folium(folium_map)