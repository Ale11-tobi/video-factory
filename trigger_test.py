import requests
url = "https://api.github.com/repos/Ale11-tobi/video-factory/dispatches"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": "token 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"
}
data = {
    "event_type": "trigger_kaggle",
    "client_payload": {
        "text": "Test di connessione",
        "chat_id": "6810865157"
    }
}
resp = requests.post(url, headers=headers, json=data)
print(f"Status: {resp.status_code}")
if resp.text:
    print(resp.text)
