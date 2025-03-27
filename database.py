import sqlite3
import datetime
import csv
# import pandas as pd
# from models import Route

#DBへの接続（DBファイルがない場合は新規作成）
dbname = 'Route.db'
conn=sqlite3.connect(dbname)
c = conn.cursor()

# executeメソッドでSQL文を実行する（すでに存在する場合は作成しない）
c.execute('''
    CREATE TABLE IF NOT EXISTS Route (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        date TEXT,
        goal_address TEXT,
        start_station TEXT,
        goal_station TEXT,
        transfer_stations TEXT,
        fare INTEGER,
        duration INTEGER
    )
''')

#DBへの変更保存
conn.commit()
#DB接続を閉じる
conn.close()

#ルート情報をデータベースに保存するための関数を定義
def insert_route(user_name, date, goal_address, start_station, goal_station, transfer_stations, fare, duration):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    
    # 取得したデータを挿入
    c.execute('''
        INSERT INTO Route (user_name, date, goal_address, start_station, goal_station, transfer_stations, fare, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_name, date, goal_address, start_station, goal_station, ", ".join(transfer_stations), fare, duration))

    #DBへの変更保存
    conn.commit()
    #DB接続を閉じる
    conn.close()

# ユーザーが交通費清算時アプリに読み込ませるためのCSV出力する関数
def export_to_csv(csv_filename="routes.csv"):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    
    # データを取得(SQL文実行)
    c.execute("SELECT * FROM Route")
    rows = c.fetchall()
    
    # カラム名を取得
    column_names = [description[0] for description in c.description]

    # CSVファイルに書き出し
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # ヘッダーを書き込む
        writer.writerow(column_names)
        
        # データを書き込む
        writer.writerows(rows)

    #DB接続を閉じて、完了確認
    conn.close()
    print(f"データを {csv_filename} にエクスポートしました。")