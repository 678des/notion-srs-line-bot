from flask import Flask, request
import sqlite3
from urllib.parse import parse_qs

app = Flask(__name__)

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

            conn = sqlite3.connect("knowledge.db")
            cur = conn.cursor()
            cur.execute("SELECT knowledge_level FROM items WHERE id = ?", (item_id,))
            row = cur.fetchone()
            if row:
                new_level = update_knowledge_level(row[0], result)
                cur.execute("""
                    UPDATE items
                    SET knowledge_level = ?, last_reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_level, item_id))
                conn.commit()
            conn.close()

    return "OK", 200


app.run(port=5000)