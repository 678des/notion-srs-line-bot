#一番知識レベルが低いやつ探して、それ送る。

from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import libsql_client
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest,
    TextMessage, QuickReply, QuickReplyItem, PostbackAction
)
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

conn = libsql_client.create_client_sync(
    url=os.environ["TURSO_DATABASE_URL"].strip(),
    auth_token=os.environ["TURSO_AUTH_TOKEN"].strip()
)

def get_lowest_knowledge_item():
    result = conn.execute("""
        SELECT id, title, body FROM items
        ORDER BY knowledge_level ASC, last_reviewed_at ASC
        LIMIT 1
    """)
    return result.rows[0] if result.rows else None



def send_review_message(item_id, title, body):
    text = f"📘 {title}\n\n{body}"

    quick_reply = QuickReply(items=[
        QuickReplyItem(action=PostbackAction(label="理解できた", data=f"item_id={item_id}&result=理解できた", display_text="理解できた")),
        QuickReplyItem(action=PostbackAction(label="曖昧", data=f"item_id={item_id}&result=曖昧", display_text="曖昧")),
        QuickReplyItem(action=PostbackAction(label="理解できなかった", data=f"item_id={item_id}&result=理解できなかった", display_text="理解できなかった")),
    ])

    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=LINE_USER_ID,
                messages=[TextMessage(text=text, quick_reply=quick_reply)]
            )
        )

item = get_lowest_knowledge_item()
if item:
    item_id, title, body = item
    send_review_message(item_id, title, body)
    print(f"送信完了: {title}")
else:
    print("送信対象のアイテムがありません")

conn.close()