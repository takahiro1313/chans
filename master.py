import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# データベース接続
dbname = "Route.db"

# サイドバーの状態を保持
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

# サイドバーの状態を切り替え
def toggle_sidebar():
    if st.session_state.sidebar_state == 'expanded':
        st.session_state.sidebar_state = 'collapsed'
    else:
        st.session_state.sidebar_state = 'expanded'

# サイドバー設定に基づきページを更新
st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)

def get_all_user_data():
    """全ユーザーのデータを取得"""
    conn = sqlite3.connect(dbname)
    query = "SELECT user_name, date, duration, fare FROM Route"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Streamlit でのフロントエンドUI
# スタイル変更定義
primaryColor = "#00FFB0"
backgroundColor = "#1E1E1E"
secondaryBackgroundColor = "#31333F"
textColor = "#FFFFFF"
font = "sans serif"

# カスタムCSS
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

        /* テキストの色 */
        .stApp, .stMarkdown, .stTextInput {{
            color: {textColor} !important;
            font-family: {font}, serif;
        }}

        /* ボタンのデザイン */
        .stButton>button {{
            background-color: {primaryColor} !important;
            color: white !important;
            border-radius: 10px !important;
        }}

        /* 警告メッセージの背景 */
        .stAlert {{
            background-color: #FFD700 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("営業管理 ダッシュボード")

# 全ユーザーのデータ取得
df = get_all_user_data()

if not df.empty:
    st.subheader("全ユーザーのデータ")

    # 日付をdatetime型に変換
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["user_name", "date"])

    # ユーザーごとの累積データを計算
    df["cumulative_fare"] = df.groupby('user_name')['fare'].cumsum()
    df["cumulative_duration"] = df.groupby('user_name')['duration'].cumsum()

    # ユーザーごとの交通費と移動時間の合計を計算
    user_totals = df.groupby('user_name')[['fare', 'duration']].sum().reset_index()

    # ユーザーごとのグラフ作成
    fig_fare = px.bar(user_totals, x="user_name", y="fare", title="ユーザーごとの交通費", labels={"fare": "交通費"})
    fig_duration = px.bar(user_totals, x="user_name", y="duration", title="ユーザーごとの移動時間", labels={"duration": "移動時間"})

    # 総合データの円グラフ
    total_fare = df["fare"].sum()
    total_duration = df["duration"].sum()

    pie_chart_data = pd.DataFrame({
        "Category": ["交通費", "移動時間"],
        "Value": [total_fare, total_duration]
    })

    fig_pie = px.pie(pie_chart_data, values='Value', names='Category', title="総合データ", color='Category', 
                     color_discrete_map={"交通費": "#00FFB0", "移動時間": "#FF6347"})

    # グラフ表示
    st.plotly_chart(fig_fare)
    st.plotly_chart(fig_duration)
    st.plotly_chart(fig_pie)

else:
    st.warning("データが見つかりません")



# import streamlit as st
# import sqlite3
# import pandas as pd
# import plotly.express as px

# # データベース接続
# dbname = "Route.db"

# # サイドバーの状態を保持
# if 'sidebar_state' not in st.session_state:
#     st.session_state.sidebar_state = 'expanded'

# # サイドバーの状態を切り替え
# def toggle_sidebar():
#     if st.session_state.sidebar_state == 'expanded':
#         st.session_state.sidebar_state = 'collapsed'
#     else:
#         st.session_state.sidebar_state = 'expanded'

# # サイドバー設定に基づきページを更新
# st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)

# def get_user_data(user_name):
#     """ユーザーのデータを取得"""
#     conn = sqlite3.connect(dbname)
#     query = "SELECT date, duration, fare FROM Route WHERE user_name = ?"
#     df = pd.read_sql_query(query, conn, params=(user_name,))
#     conn.close()
#     return df

# # Streamlit でのフロントエンドUI
# # スタイル変更定義
# primaryColor = "#00FFB0"
# backgroundColor = "#1E1E1E"
# secondaryBackgroundColor = "#31333F"
# textColor = "#FFFFFF"
# font = "sans serif"

# # カスタムCSS
# st.markdown(
#     f"""
#     <style>
#         /* タイトルの色を変更 */
#         .stApp h1 {{
#             color: {textColor};
#             font-family: {font}, serif;
#         }}

#         /* サイドバーの背景色 */
#         [data-testid="stSidebar"] {{
#             background-color: {secondaryBackgroundColor} !important;
#         }}

#         /* 全体の背景色 */
#         .stApp {{
#             background-color: {backgroundColor} !important;
#         }}

#         /* テキストの色 */
#         .stApp, .stMarkdown, .stTextInput {{
#             color: {textColor} !important;
#             font-family: {font}, serif;
#         }}

#         /* ボタンのデザイン */
#         .stButton>button {{
#             background-color: {primaryColor} !important;
#             color: white !important;
#             border-radius: 10px !important;
#         }}

#         /* 警告メッセージの背景 */
#         .stAlert {{
#             background-color: #FFD700 !important;
#         }}
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# st.title("営業管理 ダッシュボード")

# # ユーザー名の入力
# user_name = st.sidebar.text_input("ユーザー名を入力してください")

# if user_name:
#     # ユーザーデータ取得
#     df = get_user_data(user_name)
    
#     if not df.empty:
#         st.subheader(f"**{user_name}** さんのデータ")

#         # 日付をdatetime型に変換
#         df["date"] = pd.to_datetime(df["date"])
#         df = df.sort_values("date")

#         # **日付ごとの累積データ
#         df["cumulative_fare"] = df["fare"].cumsum()
#         df["cumulative_duration"] = df["duration"].cumsum()

#         # グラフ作成
#         fig_fare = px.bar(df, x="date", y="fare", title="交通費の推移", labels={"fare": "交通費"}, color="fare", 
#                           color_continuous_scale="Viridis")
#         fig_duration = px.bar(df, x="date", y="duration", title="移動時間の推移", labels={"duration": "移動時間"}, color="duration", 
#                               color_continuous_scale="Cividis")

#         # 円グラフの作成例
#         total_fare = df["fare"].sum()
#         total_duration = df["duration"].sum()

#         pie_chart_data = pd.DataFrame({
#             "Category": ["交通費", "移動時間"],
#             "Value": [total_fare, total_duration]
#         })

#         fig_pie = px.pie(pie_chart_data, values='Value', names='Category', title="総合データ", color='Category', 
#                          color_discrete_map={"交通費": "#00FFB0", "移動時間": "#FF6347"})

#         # グラフ表示
#         st.plotly_chart(fig_fare)
#         st.plotly_chart(fig_duration)
#         st.plotly_chart(fig_pie)

#     else:
#         st.warning("対象ユーザーのデータが見つかりません、ユーザー名を確認してください")