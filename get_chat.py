import requests
import sys

token = "8823767699:AAH6jYjpDYud5sYlnw0Bh-4W9rdF5YSQ7nI"
try:
    resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates").json()
    if resp.get("ok") and len(resp.get("result", [])) > 0:
        for res in resp["result"]:
            if "message" in res and "chat" in res["message"]:
                print("CHAT_ID=" + str(res["message"]["chat"]["id"]))
                sys.exit(0)
    print("NO_MESSAGES_FOUND")
except Exception as e:
    print("ERROR:", e)
