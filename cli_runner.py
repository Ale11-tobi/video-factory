import sys
import json
import asyncio
from main import process_mode_a
from core.telegram_notifier import send_telegram_video

async def run_cli():
    # Legge il testo da un file passato come argomento
    if len(sys.argv) < 2:
        print("Uso: python cli_runner.py input_text.txt")
        sys.exit(1)
        
    input_file = sys.argv[1]
    with open(input_file, "r", encoding="utf-8") as f:
        testo = f.read()
        
    print(f"Inizio elaborazione testo lungo {len(testo)} caratteri...")
    
    try:
        final_video = await process_mode_a(testo, progress_callback=lambda msg, prog: print(f"[{prog}%] {msg}"))
        print(f"Video generato con successo in: {final_video}")
        
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                token = config.get("telegram_bot_token")
                chat_id = config.get("telegram_chat_id")
                if token and chat_id:
                    print("Invio del video su Telegram...")
                    send_telegram_video(token, chat_id, final_video)
        except Exception as e:
            print("Nessun invio Telegram (config assente o errore):", e)
            
    except Exception as e:
        print("Errore critico durante l'elaborazione:", e)

if __name__ == "__main__":
    asyncio.run(run_cli())
