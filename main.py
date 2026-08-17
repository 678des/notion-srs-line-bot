import subprocess
import sys

print("=== Notion同期を開始 ===")
subprocess.run([sys.executable, "day_sync.py"], check=True)
print("=== Notion同期 完了 ===")

print("=== LINE通知を開始 ===")
subprocess.run([sys.executable, "push_msg.py"], check=True)
print("=== LINE通知 完了 ===")