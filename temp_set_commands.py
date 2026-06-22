import requests

TOKEN = "8823767699:AAH6jYjpDYud5sYlnw0Bh-4W9rdF5YSQ7nI"
url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
data = {
    "commands": [
        {"command": "accendi", "description": "Sveglia il sito Hugging Face"}
    ]
}
resp = requests.post(url, json=data)
print(resp.json())
