import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# CODICI PERSONALI
TELEGRAM_TOKEN = "8823767699:AAH6jYjpDYud5sYlnw0Bh-4W9rdF5YSQ7nI"
GITHUB_TOKEN = "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"
GITHUB_REPO = "Ale11-tobi/video-factory"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Bot Centrale attivato!\n\n"
        "Questo bot comunica direttamente con GitHub Actions, che a sua volta accenderà le GPU di Kaggle per te.\n\n"
        "Scrivi `Genera: [testo]` per avviare l'elaborazione a PC spento.\n"
        "Scrivi `/accendi` per svegliare la vetrina del sito se si è addormentata."
    )

async def accendi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Invio la 'sveglia' al sito su Hugging Face...")
    url = "https://huggingface.co/spaces/02Ale11x/ales_video_editor"
    try:
        requests.get(url, timeout=5)
        await update.message.reply_text(f"✅ Sito sveglio e operativo!\n\nAprilo qui: {url}")
    except requests.exceptions.Timeout:
        await update.message.reply_text(f"✅ Sveglia inviata con successo! Il server ci metterà 1-2 minuti ad avviarsi del tutto.\n\nTra poco sarà online qui: {url}")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore di rete: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id
    
    if not text.lower().startswith("genera:"):
        return

    script_text = text[7:].strip()
    await update.message.reply_text("🚀 Richiesta inviata! Sto contattando GitHub per svegliare Kaggle...")

    # Chiamata API ufficiale di GitHub (Consentita da PythonAnywhere!)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    data = {
        "event_type": "trigger_kaggle",
        "client_payload": {
            "text": script_text,
            "chat_id": str(chat_id)
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 204:
            kaggle_link = "https://www.kaggle.com/code/alessandroiovine/video-factory-run/log"
            await update.message.reply_text(
                "✅ GitHub ha ricevuto il segnale! Il server Kaggle è ufficialmente partito.\n\n"
                f"👀 **Puoi spiare il server e vedere la percentuale di caricamento in diretta qui:**\n{kaggle_link}\n\n"
                "Attendi il video finito in questa chat tra circa 15-20 minuti!"
            )
        else:
            await update.message.reply_text(f"❌ Errore da GitHub ({resp.status_code}): {resp.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore di connessione: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("accendi", accendi))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot avviato! In ascolto per inviare segnali a GitHub...")
    app.run_polling()

if __name__ == "__main__":
    main()
