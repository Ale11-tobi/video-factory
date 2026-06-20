import sys
import json
import asyncio
import requests
from main import process_mode_a
from core.telegram_notifier import send_telegram_video

def send_telegram_progress(token, chat_id, msg, prog):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        # Aggiungiamo un'icona in base al progresso per abbellirlo
        icon = "🔄"
        if prog >= 100: icon = "✅"
        elif prog > 80: icon = "🎬"
        elif prog > 50: icon = "🧑"
        elif prog > 20: icon = "🔊"
        
        requests.post(url, json={"chat_id": chat_id, "text": f"{icon} [{prog}%] Kaggle: {msg}"})
    except:
        pass # Ignoriamo errori se manca la connessione temporaneamente

async def run_cli():
    # Legge il testo da un file passato come argomento
    if len(sys.argv) < 2:
        print("Uso: python cli_runner.py input_text.txt")
        sys.exit(1)
        
    input_file = sys.argv[1]
    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    # --- PARSER CONFIGURAZIONI AVANZATE FRONTEND ---
    import re
    config_match = re.search(r"\[ADVANCED_CONFIG\](.*?)\[/ADVANCED_CONFIG\]", raw_text, re.DOTALL)
    
    frontend_options = {}
    testo = raw_text
    if config_match:
        config_str = config_match.group(1).strip()
        testo = raw_text.replace(config_match.group(0), "").strip()
        for line in config_str.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                frontend_options[key.strip()] = val.strip()
                
    print(f"Opzioni Frontend Ricevute: {frontend_options}")
    print(f"Inizio elaborazione testo pulito lungo {len(testo)} caratteri...")
    
    # Tentiamo di caricare le credenziali Telegram
    token = None
    chat_id = None
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            token = config.get("telegram_bot_token")
            chat_id = config.get("telegram_chat_id")
    except:
        pass

    def progress_handler(msg, prog):
        print(f"[{prog}%] {msg}")
        if token and chat_id:
            send_telegram_progress(token, chat_id, msg, prog)

    try:
        if token and chat_id:
            send_telegram_progress(token, chat_id, "Inizio calcoli sulla GPU T4 di Kaggle...", 0)
            
        final_video = await process_mode_a(testo, progress_callback=progress_handler, frontend_options=frontend_options)
        print(f"Video generato con successo in: {final_video}")
        
        if token and chat_id:
            print("Invio del video su Telegram...")
            send_telegram_video(token, chat_id, final_video)
            
    except Exception as e:
        print("Errore critico durante l'elaborazione:", e)
        if token and chat_id:
            send_telegram_progress(token, chat_id, f"ERRORE CRITICO: {e}", 0)

if __name__ == "__main__":
    asyncio.run(run_cli())
