import os
import sys
import json
import time
import re
import subprocess
import threading
import requests
from telegram_notifier import send_telegram_message

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

class FactoryController:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.proc_streamlit = None
        self.proc_cloudflared = None
        self.is_running = False

    def extract_cloudflare_url(self):
        if not self.proc_cloudflared: return None
        url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        cf_url = None
        while True:
            line = self.proc_cloudflared.stderr.readline()
            if not line: break
            match = url_regex.search(line)
            if match:
                cf_url = match.group(0)
                break
                
        # Continua a svuotare il buffer per evitare che Cloudflare si blocchi con il pipe pieno!
        def drain():
            try:
                while self.proc_cloudflared and self.proc_cloudflared.poll() is None:
                    self.proc_cloudflared.stderr.readline()
            except: pass
            
        threading.Thread(target=drain, daemon=True).start()
        return cf_url

    def start_engine(self):
        if self.is_running:
            return
            
        print("Avvio componenti...")
        python_exe = sys.executable
        streamlit_path = os.path.join(BASE_DIR, "app.py")
        self.proc_streamlit = subprocess.Popen([python_exe, "-m", "streamlit", "run", streamlit_path, "--server.headless", "true"], cwd=BASE_DIR)
        
        cloudflared_exe = os.path.join(BASE_DIR, "cloudflared.exe")
        if os.path.exists(cloudflared_exe):
            self.proc_cloudflared = subprocess.Popen([cloudflared_exe, "tunnel", "--url", "http://localhost:8501"], 
                                                stderr=subprocess.PIPE, text=True, cwd=BASE_DIR)
            cf_url = self.extract_cloudflare_url()
            if cf_url:
                msg = f"✅ *Factory Accesa!*\n\nLa dashboard è online:\n{cf_url}"
                send_telegram_message(self.token, self.chat_id, msg)
                
        self.is_running = True
        self.send_keyboard()

    def stop_engine(self):
        if not self.is_running:
            return
            
        if self.proc_streamlit: self.proc_streamlit.kill()
        if self.proc_cloudflared: self.proc_cloudflared.kill()
        self.proc_streamlit = None
        self.proc_cloudflared = None
        self.is_running = False
        
        requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", 
                      json={"chat_id": self.chat_id, "text": "🛑 Server Arrestato. Il PC è acceso, ma la Factory è offline e non consuma risorse."})
        self.send_keyboard()

    def send_keyboard(self):
        if self.is_running:
            kb = {"keyboard": [[{"text": "📊 Stato Lavori"}, {"text": "🛑 Spegni Factory"}]], "resize_keyboard": True}
            text_msg = "Pannello di controllo:"
        else:
            kb = {"keyboard": [[{"text": "🟢 Accendi Factory"}]], "resize_keyboard": True}
            text_msg = "La Factory è attualmente in Standby."
            
        requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", 
                      json={"chat_id": self.chat_id, "text": text_msg, "reply_markup": kb})

    def poll(self):
        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={offset}&timeout=30"
                resp = requests.get(url, timeout=40).json()
                if resp.get("ok"):
                    for result in resp.get("result", []):
                        offset = result["update_id"] + 1
                        text = result.get("message", {}).get("text", "")
                        cid = str(result.get("message", {}).get("chat", {}).get("id", ""))
                        
                        if cid != self.chat_id: continue
                        
                        if text == "/start":
                            self.send_keyboard()
                        elif text == "🟢 Accendi Factory" or text == "/accendi":
                            requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json={"chat_id": self.chat_id, "text": "Avvio in corso, attendere..."})
                            self.start_engine()
                        elif text == "🛑 Spegni Factory" or text == "/spegni":
                            self.stop_engine()
                        elif text == "📊 Stato Lavori":
                            if not self.is_running:
                                requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json={"chat_id": self.chat_id, "text": "La Factory è SPENTA. Accendila prima di controllare i lavori."})
                                continue
                                
                            status_file = os.path.join(BASE_DIR, "temp", "status.json")
                            msg_text = "Nessun lavoro in corso al momento."
                            if os.path.exists(status_file):
                                try:
                                    with open(status_file, "r", encoding="utf-8") as f: s = json.load(f)
                                    msg_text = f"🔄 *Lavoro in esecuzione*\nModalità: {s.get('mode', '?')}\nProgresso: {s.get('pct', 0)}%\nFase: {s.get('msg', '')}"
                                except: pass
                            requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json={"chat_id": self.chat_id, "text": msg_text, "parse_mode": "Markdown"})
            except Exception as e:
                time.sleep(5)

def main():
    print("Avvio Factory Daemon Controller...")
    config = get_config()
    token = config.get("tg_token")
    chat_id = config.get("tg_chat_id")
    
    if token and chat_id:
        controller = FactoryController(token, chat_id)
        controller.start_engine()
        controller.poll()
    else:
        print("Credenziali mancanti. Impossibile avviare il Controller Telegram.")

if __name__ == "__main__":
    main()
