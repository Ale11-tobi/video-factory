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
    
    # Tentiamo di caricare le credenziali
    token = None
    chat_id = None
    gh_token = None
    gist_id = None
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            token = config.get("telegram_bot_token")
            chat_id = config.get("telegram_chat_id")
            gh_token = config.get("github_token")
            gist_id = config.get("gist_id")
    except:
        pass

    import time
    start_time = time.time()
    
    def update_gist(msg, prog, eta, video_url=""):
        if not gh_token or not gist_id: return
        gist_url = f"https://api.github.com/gists/{gist_id}"
        headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"}
        data = {
            "files": {
                "progress.json": {
                    "content": json.dumps({"status": msg, "progress": prog, "eta": eta, "video_url": video_url})
                }
            }
        }
        try: requests.patch(gist_url, headers=headers, json=data, timeout=5)
        except: pass

    def progress_handler(msg, prog):
        print(f"[{prog}%] {msg}")
        
        elapsed = time.time() - start_time
        eta_str = "Calcolo in corso..."
        if prog > 0 and prog < 100:
            total_est = (elapsed / prog) * 100
            rem_sec = total_est - elapsed
            m, s = divmod(int(rem_sec), 60)
            eta_str = f"~{m} min e {s} sec"
        elif prog == 100:
            eta_str = "Completato!"
            
        update_gist(msg, prog, eta_str)
            
        if token and chat_id:
            msg_with_eta = f"{msg}\n⏳ ETA: {eta_str}" if prog < 100 else msg
            send_telegram_progress(token, chat_id, msg_with_eta, prog)

    try:
        if token and chat_id:
            send_telegram_progress(token, chat_id, "Inizio calcoli sulla GPU T4 di Kaggle...", 0)
            
        final_video = await process_mode_a(testo, progress_callback=progress_handler, frontend_options=frontend_options)
        print(f"Video generato con successo in: {final_video}")
        
        if token and chat_id:
            print("Invio del video su Telegram...")
            video_url = send_telegram_video(token, chat_id, final_video)
            if video_url and video_url != "SENT_NO_URL":
                update_gist("Completato! Video pronto per il download.", 100, "Finito!", video_url)
            
    except Exception as e:
        print("Errore critico durante l'elaborazione:", e)
        if token and chat_id:
            send_telegram_progress(token, chat_id, f"ERRORE CRITICO: {e}", 0)

if __name__ == "__main__":
    asyncio.run(run_cli())
