import streamlit as st
import requests
import json
import os
import base64

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Antigravity Studio", page_icon="🛸", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS SPAZIALE (Glassmorphism & Neon) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700;900&display=swap');
    
    .stApp {
        font-family: 'Outfit', sans-serif;
        background-color: #050505;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(108, 92, 231, 0.15), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(0, 210, 211, 0.15), transparent 25%);
        color: #dfe6e9;
    }
    
    /* Titoli Neon */
    h1 {
        background: linear-gradient(to right, #00d2d3, #6c5ce7, #ff7675);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Box stile Vetro (Glassmorphism) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255, 255, 255, 0.03);
        padding: 10px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: #a4b0be;
        font-weight: 500;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(108, 92, 231, 0.2) !important;
        color: #fff !important;
        border: 1px solid rgba(108, 92, 231, 0.5) !important;
        box-shadow: 0 0 15px rgba(108, 92, 231, 0.3);
    }
    
    /* Ingressi di testo e Dropdown */
    .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div {
        background-color: rgba(30, 39, 46, 0.6) !important;
        color: #fff !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        font-family: 'Outfit', sans-serif;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>textarea:focus {
        border-color: #00d2d3 !important;
        box-shadow: 0 0 10px rgba(0, 210, 211, 0.3) !important;
    }
    
    /* Pulsantone Magico */
    .stButton>button {
        background: linear-gradient(45deg, #6c5ce7, #00d2d3);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 1rem 2rem;
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        width: 100%;
        transition: all 0.4s ease;
        box-shadow: 0 10px 20px rgba(108, 92, 231, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 15px 30px rgba(0, 210, 211, 0.6);
    }
    
    /* File Uploader */
    [data-testid="stFileUploadDropzone"] {
        background: rgba(255,255,255,0.02);
        border: 2px dashed rgba(108, 92, 231, 0.5);
        border-radius: 15px;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background: rgba(108, 92, 231, 0.1);
        border-color: #00d2d3;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SEGRETI E CONFIGURAZIONI ---
GITHUB_TOKEN = "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"
GITHUB_REPO = "Ale11-tobi/video-factory"
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"tg_chat_id": ""}

def save_config(chat_id):
    with open(CONFIG_FILE, "w") as f: json.dump({"tg_chat_id": chat_id}, f)

config = load_config()

# --- 4. HEADER ---
st.markdown("<h1>🛸 Antigravity Studio</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a4b0be; font-size: 1.2rem;'>Il primo motore Generativo Cloud-Native 100% Gratuito</p>", unsafe_allow_html=True)
st.write("")

# --- 5. TABS PRINCIPALI ---
tab_regia, tab_avatar, tab_3d, tab_asset = st.tabs([
    "🎬 Regia & Sceneggiatura", 
    "👤 Avatar & Motion", 
    "🦖 Generatore 3D (Sperimentale)", 
    "🗂️ Upload Asset Personali"
])

# VARIABILI DI STATO
if 'user_text' not in st.session_state: st.session_state.user_text = ""

# --- TAB 1: REGIA ---
with tab_regia:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1. La tua Sceneggiatura")
        st.session_state.user_text = st.text_area("Cosa vuoi raccontare oggi?", height=250, placeholder="Incolla qui il tuo script, oppure lascia che l'IA lo inventi partendo da una tua idea...")
    
    with col2:
        st.subheader("2. Setup di Base")
        mode = st.selectbox("Modalità Operativa", ["📝 Mode A: Da Testo a Video", "📹 Mode B: Auto-Editor (Vlog)", "🎙️ Mode C: Podcast Faceless"])
        format_ratio = st.selectbox("Formato", ["📱 9:16 (Shorts/TikTok)", "🖥️ 16:9 (YouTube/TV)"])
        
        st.subheader("3. Estetica & Stile")
        style = st.selectbox("Direzione Artistica (B-Roll)", [
            "🎥 Cinematico (Pellicola 35mm)",
            "🏛️ Storico / Documentario",
            "🚀 Fantascienza / Cyberpunk",
            "🖌️ Illustrazione Animata",
            "🌍 Realistico 4K"
        ])
        subs_mega = st.toggle("Attiva Sottotitoli Mega-Corretti (IA Avanzata)", value=True)

# --- TAB 2: AVATAR ---
with tab_avatar:
    st.subheader("Personalizzazione del Volto")
    st.info("Attualmente il motore open-source anima perfettamente il labiale e le espressioni facciali. Le animazioni complesse del corpo arriveranno nei prossimi update gratuiti.")
    
    col3, col4 = st.columns(2)
    with col3:
        avatar_img = st.file_uploader("Trascina qui l'immagine del tuo Avatar (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if avatar_img:
            st.success("Immagine caricata in memoria!")
            st.image(avatar_img, width=150)
            
    with col4:
        avatar_prompt = st.text_area("Istruzioni Avanzate per l'Animazione", placeholder="Es. Muovi la bocca a tempo, espressione sorpresa al secondo 10, muovi la mano (sperimentale)...", height=150)

# --- TAB 3: GENERATORE 3D ---
with tab_3d:
    st.subheader("Motore di Animazione 3D (Stile Geopop)")
    st.warning("⚠️ L'intelligenza Artificiale Open-Source attuale farà del suo meglio per avvicinarsi alla qualità Maya/Blender. Il motore cercherà le migliori clip stock 3D o ne genererà di simili.")
    
    enable_3d = st.toggle("🌟 Genera Animazioni 3D Scientifiche/Educative", value=False)
    
    if enable_3d:
        smart_3d = st.toggle("🧠 Generazione 3D Intelligente (Memoria e Riutilizzo Asset)", value=True, help="L'IA capirà dove inserire il 3D e riutilizzerà i render se il soggetto si ripete, risparmiando memoria.")
        prompt_3d = st.text_area("Descrivi nel dettaglio l'animazione 3D desiderata:", placeholder="Es. Un modello 3D della terra che si spacca a metà mostrando il nucleo incandescente, risoluzione altissima, stile geopop...")
        pos_3d = st.selectbox("Posizionamento nel video", ["A metà video", "All'inizio", "Alla fine come conclusione"])
    else:
        smart_3d = False

# --- TAB 4: ASSET ---
with tab_asset:
    st.subheader("Libreria Personale")
    st.write("Vuoi usare un video 3D o un'animazione che hai già sul PC? Caricala qui e chiedi all'IA di inserirla.")
    custom_video = st.file_uploader("Carica Video/Clip Personali (MP4)", type=['mp4', 'mov'])
    if custom_video:
        custom_instructions = st.text_input("Istruzioni:", placeholder="Es. Inserisci questa clip quando dico la parola 'Vulcano'")

st.markdown("---")

# --- PANNELLO LATERALE E AVVIO ---
st.sidebar.title("🚀 Console di Lancio")
st.sidebar.markdown("Il sito è la vetrina. Kaggle è il motore.")

tg_chat_id = st.sidebar.text_input("🔑 Il tuo Chat ID Telegram", value=config.get("tg_chat_id", ""), help="Serve per mandarti le notifiche live e il video finito.")
if tg_chat_id != config.get("tg_chat_id"):
    save_config(tg_chat_id)

if st.button("🔥 ACCENDI I MOTORI CLOUD E GENERA 🔥"):
    if not st.session_state.user_text:
        st.error("Inserisci una sceneggiatura nella Tab 1 (Regia)!")
    elif not tg_chat_id:
        st.error("Inserisci il tuo Chat ID nella barra laterale sinistra!")
    else:
        with st.spinner("Invio delle coordinate satellitari a GitHub Actions e Kaggle..."):
            
            # Prepariamo un pacchetto "Intelligente" da passare a Kaggle nel payload testuale
            # (In futuro cli_runner.py leggerà queste opzioni. Per ora le ignoriamo o le mettiamo nel prompt testuale)
            
            advanced_payload = f"""
[ADVANCED_CONFIG]
Mode: {mode}
Format: {format_ratio}
Style: {style}
MegaSubs: {subs_mega}
Avatar_Prompt: {avatar_prompt if 'avatar_prompt' in locals() else 'None'}
Use_3D: {enable_3d if 'enable_3d' in locals() else False}
Smart_3D: {smart_3d if 'smart_3d' in locals() else False}
Prompt_3D: {prompt_3d if 'enable_3d' in locals() and enable_3d else 'None'}
[/ADVANCED_CONFIG]

{st.session_state.user_text}
"""
            
            url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {GITHUB_TOKEN}"
            }
            data = {
                "event_type": "trigger_kaggle",
                "client_payload": {
                    "text": advanced_payload,
                    "chat_id": tg_chat_id
                }
            }
            
            try:
                resp = requests.post(url, headers=headers, json=data)
                if resp.status_code == 204:
                    st.success("✅ CONNESSIONE STABILITA! I server Kaggle si sono accesi.")
                    st.info("📱 Controlla Telegram! Stai per ricevere gli aggiornamenti in tempo reale.")
                    st.markdown("[👀 Guarda la Console di Kaggle in Diretta](https://www.kaggle.com/code/alessandroiovine/video-factory-run/log)")
                    st.balloons()
                else:
                    st.error(f"❌ Errore Backend ({resp.status_code}): {resp.text}")
            except Exception as e:
                st.error(f"❌ Errore di Rete: {e}")
