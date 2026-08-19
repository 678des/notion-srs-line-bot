from flask import Flask, request
import sqlite3
from urllib.parse import parse_qs
import libsql_client
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
    
conn = libsql_client.create_client_sync(
    url=os.environ["TURSO_DATABASE_URL"].strip(),
    auth_token=os.environ["TURSO_AUTH_TOKEN"].strip()
)

def update_knowledge_level(current_level, result):
    if result == "理解できた":
        return min(current_level + 1, 4)
    elif result == "理解できなかった":
        return 1
    else:
        return current_level

@app.route("/webhook", methods=["POST"])
def webhook():
    print("★1: リクエスト受信", flush=True)
    body = request.get_json()
    print("★2: JSON取得完了", body, flush=True)

    for event in body.get("events", []):
        
        if event["type"] == "postback":
            print("★3: postbackイベント検出", flush=True)
            data = parse_qs(event["postback"]["data"])
            item_id = int(data["item_id"][0])
            result = data["result"][0]
            print(f"★4: item_id={item_id}, result={result}", flush=True)

            db_result = conn.execute("SELECT knowledge_level FROM items WHERE id = ?", (item_id,))
            print("★5: SELECT実行完了", flush=True)
            row = db_result.rows[0] if db_result.rows else None
            print("★6: 現在のレベル:", row, flush=True)
            if row:
                new_level = update_knowledge_level(row[0], result)
                print("★7: 新しいレベル:", new_level, flush=True)
                conn.execute("""
                    UPDATE items
                    SET knowledge_level = ?, last_reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_level, item_id))
                print("★8: UPDATE実行完了", flush=True)
            else:
                print("★NG: rowがNoneでした(該当IDが見つからない)", flush=True)
    return "OK", 200

@app.route("/debug-turso")
def debug_turso():
    import time
    start = time.time()
    try:
        result = conn.execute("SELECT 1")
        elapsed = time.time() - start
        return f"成功: {result} (かかった時間: {elapsed:.2f}秒)"
    except Exception as e:
        elapsed = time.time() - start
        return f"エラー: {e} (かかった時間: {elapsed:.2f}秒)"
        
if __name__ == "__main__":
    app.run(port=5000)