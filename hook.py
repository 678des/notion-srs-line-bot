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
    body = request.get_json()

    for event in body.get("events", []):
        if event["type"] == "postback":
            data = parse_qs(event["postback"]["data"])
            item_id = int(data["item_id"][0])
            result = data["result"][0]

            db_result = conn.execute("SELECT knowledge_level FROM items WHERE id = ?", (item_id,))
            row = db_result.rows[0] if db_result.rows else None
            if row:
                new_level = update_knowledge_level(row[0], result)
                conn.execute("""
                    UPDATE items
                    SET knowledge_level = ?, last_reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_level, item_id))
    return "OK", 200


if __name__ == "__main__":
    app.run(port=5000)