import streamlit as st
import asyncio
import os
import sys
import io
import json
import logging
from main import process_mode_a, process_mode_b_c
from core.telegram_notifier import send_telegram_message

# Configurazione Streamlit (DEVE ESSERE LA PRIMA CHIAMATA)
st.set_page_config(page_title="Antigravity Factory", page_icon="🎬", layout="wide")

# CSS Personalizzato per Dark Mode Estrema
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        background-image: radial-gradient(circle at top right, rgba(55,0,179,0.15), transparent 40%),
                          radial-gradient(circle at bottom left, rgba(187,134,252,0.15), transparent 40%);
        color: #c9d1d9;
    }
    .stButton>button {
        background: linear-gradient(135deg, #bb86fc 0%, #3700b3 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(187, 134, 252, 0.4);
    }
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        background-color: rgba(22, 27, 34, 0.8);
        color: #e6edf3;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        backdrop-filter: blur(10px);
        transition: border 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>textarea:focus {
        border: 1px solid #bb86fc;
        box-shadow: 0 0 10px rgba(187, 134, 252, 0.2);
    }
    .css-1d391kg {
        background: rgba(22, 27, 34, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 2.5rem;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe, #f093fb, #f5576c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: -1px;
    }
    h2, h3 {
        color: #e6edf3;
        font-weight: 600;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(13, 17, 23, 0.95);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
    }
    
    /* Ottimizzazione Mobile (iPhone 16 Pro Max e simili) */
    @media (max-width: 450px) {
        .css-1d391kg { padding: 1.2rem; }
        h1 { font-size: 1.6rem; margin-bottom: 1rem; }
        h2 { font-size: 1.3rem; }
        .stButton>button { width: 100%; padding: 0.8rem; font-size: 1rem; border-radius: 8px; }
        [data-testid="stSidebar"] { width: 100% !important; }
    }
    </style>
""", unsafe_allow_html=True)

# Gestione Configurazione
CONFIG_FILE = "config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"tg_token": "", "tg_chat_id": ""}

def save_config(token, chat_id):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"tg_token": token, "tg_chat_id": chat_id}, f)

config = load_config()

class StreamlitLogHandler(logging.Handler):
    def __init__(self, log_placeholder):
        super().__init__()
        self.log_placeholder = log_placeholder
        self.log_text = ""

    def emit(self, record):
        msg = self.format(record)
        self.log_text += msg + "\n"
        # Mantieni solo le ultime righe per evitare lag
        lines = self.log_text.split('\n')
        if len(lines) > 100:
            self.log_text = '\n'.join(lines[-100:])
        self.log_placeholder.code(self.log_text, language='bash')

st.title("🎬 Zero-Touch Content Factory")

# Sidebar
st.sidebar.title("Impostazioni")
mode = st.sidebar.radio("Seleziona Modalità Operativa", [
    "📝 Mode A: Da Testo a Video", 
    "📹 Mode B: Auto-Editor Vlog", 
    "🎙️ Mode C: Podcast Faceless"
])

if "Mode A" in mode:
    st.sidebar.info("**Come funziona:** Hai solo un copione testuale. L'IA genererà una voce ultra-realistica, aggiungerà un avatar e coprirà le frasi chiave con video stock (B-Roll).")
elif "Mode B" in mode:
    st.sidebar.info("**Come funziona:** Carica un video grezzo in cui parli in camera. L'IA analizzerà il parlato e inserirà video stock pertinenti sopra la tua faccia nei momenti più adatti.")
elif "Mode C" in mode:
    st.sidebar.info("**Come funziona:** Carica solo una traccia audio (la tua voce). L'IA creerà un video visivamente dinamico coprendo l'intero audio con video di stock, musica e sottotitoli.")

format_ratio = st.sidebar.selectbox("Formato Video", ["9:16 (Shorts/Reels/TikTok)", "16:9 (YouTube)"])
format_val = "9:16" if "9:16" in format_ratio else "16:9"

st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Espansioni (Opzionale)")
with st.sidebar.expander("Configura Telegram Bot", expanded=False):
    st.markdown("Ricevi il video finale direttamente sul telefono.")
    tg_token = st.text_input("Bot Token", type="password", value=config.get("tg_token", ""), help="Generato da @BotFather")
    tg_chat_id = st.text_input("Chat ID", value=config.get("tg_chat_id", ""), help="Ottienilo da @userinfobot")
    
    if tg_token != config.get("tg_token") or tg_chat_id != config.get("tg_chat_id"):
        save_config(tg_token, tg_chat_id)

def update_status(msg):
    st.session_state['status_msg'] = msg

if 'status_msg' not in st.session_state:
    st.session_state['status_msg'] = "In attesa..."

if "Mode A" in mode:
    st.subheader("Mode A: Testo ➔ Video Completo")
    st.markdown("Incolla qui il tuo script. Usa le parentesi quadre `[ ]` per indicare all'IA cosa mostrare a schermo.")
    script_text = st.text_area("", height=250, placeholder="Es: Sapevi che... [scienziato al microscopio]")
    
    if st.button("🚀 Genera Video", use_container_width=True):
        if not script_text.strip():
            st.error("Inserisci un testo valido!")
        else:
            with st.status("Avvio Generazione...", expanded=True) as status:
                progress_bar = st.progress(0, text="Avvio pipeline...")
                log_expander = st.expander("Log di Sistema", expanded=True)
                st_log = log_expander.empty()
                
                logger = logging.getLogger()
                sl_handler = StreamlitLogHandler(st_log)
                sl_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S'))
                logger.addHandler(sl_handler)
                
                def local_progress(msg, pct=0):
                    status.update(label=f"{pct}% - {msg}")
                    progress_bar.progress(pct, text=msg)
                    try:
                        os.makedirs("temp", exist_ok=True)
                        with open("temp/status.json", "w", encoding="utf-8") as f:
                            json.dump({"pct": pct, "msg": msg, "mode": "A"}, f)
                    except: pass
                
                try:
                    final_path = asyncio.run(process_mode_a(script_text, format_val, local_progress, tg_token, tg_chat_id))
                    status.update(label="✅ Video Generato con Successo!", state="complete", expanded=False)
                    st.success("Montaggio completato!")
                    st.video(final_path)
                except Exception as e:
                    logger.error(f"Errore critico: {e}")
                    status.update(label="Errore durante la generazione", state="error", expanded=True)
                    st.error(f"Errore durante la generazione: {e}")
                    if tg_token and tg_chat_id:
                        send_telegram_message(tg_token, tg_chat_id, f"❌ *Allarme dalla Factory!* ❌\n\nLa generazione Mode A è fallita a causa di un errore:\n\n`{str(e)}`")
                finally:
                    logger.removeHandler(sl_handler)
                    try: os.remove("temp/status.json") # Pulisce lo stato
                    except: pass

else:
    mode_letter = "B" if "Mode B" in mode else "C"
    st.subheader(f"Mode {mode_letter}: Raw Media Auto-Editor")
    uploaded_file = st.file_uploader(f"Carica file RAW ({'Video' if mode_letter == 'B' else 'Audio'})", type=['mp4', 'mov', 'wav', 'mp3'])
    
    if uploaded_file and st.button("🚀 Genera Video", use_container_width=True):
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        raw_path = os.path.join(temp_dir, f"uploaded_raw_{uploaded_file.name}")
        with open(raw_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        with st.status("Elaborazione file multimediale in corso...", expanded=True) as status:
            progress_bar = st.progress(0, text="Avvio pipeline...")
            log_expander = st.expander("Log di Sistema", expanded=True)
            st_log = log_expander.empty()
            
            logger = logging.getLogger()
            sl_handler = StreamlitLogHandler(st_log)
            sl_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S'))
            logger.addHandler(sl_handler)
            
            def local_progress(msg, pct=0):
                status.update(label=f"{pct}% - {msg}")
                progress_bar.progress(pct, text=msg)
                try:
                    os.makedirs("temp", exist_ok=True)
                    with open("temp/status.json", "w", encoding="utf-8") as f:
                        json.dump({"pct": pct, "msg": msg, "mode": mode_letter}, f)
                except: pass
                
            try:
                final_path = asyncio.run(process_mode_b_c(mode_letter, raw_path, format_val, local_progress, tg_token, tg_chat_id))
                status.update(label="✅ Video Generato con Successo!", state="complete", expanded=False)
                st.success("Montaggio completato!")
                st.video(final_path)
            except Exception as e:
                logger.error(f"Errore critico: {e}")
                status.update(label="Errore durante la generazione", state="error", expanded=True)
                st.error(f"Errore durante la elaborazione: {e}")
                if tg_token and tg_chat_id:
                    send_telegram_message(tg_token, tg_chat_id, f"❌ *Allarme dalla Factory!* ❌\n\nLa generazione Mode {mode_letter} è fallita a causa di un errore:\n\n`{str(e)}`")
            finally:
                logger.removeHandler(sl_handler)
                try: os.remove("temp/status.json") # Pulisce lo stato
                except: pass
