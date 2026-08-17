import hashlib
import sqlite3
from notion_client import Client
import os
from dotenv import load_dotenv
load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])
#DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

conn = sqlite3.connect("knowledge.db")
cur = conn.cursor()
# id DB自体の要素を識別するためのID(db)
# notion_page_id (notion)
# title ページタイトル(notion)
# body ページ内容(notion)
# content_hash titleとbodyをハッシュにしたもの (db)
# notion_last_edited (notion)
# last_reviewed_at Lineで最近いつ復習したか(db)
# created_at (db)
cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    notion_page_id TEXT UNIQUE NOT NULL,
    title TEXT,
    body TEXT,
    content_hash TEXT,
    notion_last_edited TEXT,
    knowledge_level INTEGER DEFAULT 1,
    last_reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def make_hash(title, body):
    return hashlib.md5((title + body).encode()).hexdigest()

response = notion.data_sources.query(
    data_source_id=os.environ["DATA_SOURCE_ID"],
    filter={
        "property": "種類",
        "select": {"equals": "知識"}
    }
)
def get_page_content(page_id):
    blocks = notion.blocks.children.list(block_id=page_id)
    texts = []
    for block in blocks["results"]:
        block_type = block["type"]
        # 段落・見出しなど、rich_textを持つブロックからテキストを抽出
        if block_type in block and "rich_text" in block[block_type]:
            for rt in block[block_type]["rich_text"]:
                texts.append(rt["plain_text"])
    return "\n".join(texts)

for page in response["results"]:
    title_prop = page["properties"]["内容"]["title"]
    title = title_prop[0]["plain_text"] if title_prop else "(無題)"
    page_id = page["id"]
    body = get_page_content(page_id)
    content_hash = make_hash(title, body)

    # すでに存在するか確認
    cur.execute("SELECT content_hash, knowledge_level FROM items WHERE notion_page_id = ?", (page_id,))
    existing = cur.fetchone()

    if existing is None:
        # 新規追加
        print("新規追加します",title)
        cur.execute("""
            INSERT INTO items (notion_page_id, title, body, content_hash, notion_last_edited, knowledge_level)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (page_id, title, body, content_hash, page["last_edited_time"]))

    elif existing[0] != content_hash:
        # 内容が変わっていたら知識度を1にダウン(前回決めたルール)
        print("内容が変わっていました",title)
        cur.execute("""
            UPDATE items
            SET title = ?, body = ?, content_hash = ?, notion_last_edited = ?, knowledge_level = 1
            WHERE notion_page_id = ?
        """, (title, body, content_hash, page["last_edited_time"], page_id))

    else:
        # 変更なし、何もしない
        print("変更なしです",title)
        pass

conn.commit()
conn.close()