import requests

token = "8823767699:AAH6jYjpDYud5sYlnw0Bh-4W9rdF5YSQ7nI"
chat_id = "6810865157"

msg = "🎉 *Sistema Antigravity Connesso!*\n\nLe credenziali sono state iniettate con successo nel nucleo. Il tuo Bot è ora operativo al 100%.\n\nQuando avvierai il PC, riceverai qui il link Cloudflare."

requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
              json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
