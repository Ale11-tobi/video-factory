import os
import json
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# I TUOI CODICI PERSONALI (INSERITI AUTOMATICAMENTE DA ANTIGRAVITY)
TELEGRAM_TOKEN = "8823767699:AAH6jYjpDYud5sYlnw0Bh-4W9rdF5YSQ7nI"

# CREDENZIALI KAGGLE
os.environ["KAGGLE_API_TOKEN"] = "KGAT_b783dce44352ed4aa318e0161a1d880a"
os.environ["KAGGLE_USERNAME"] = "alessandroiovine"
KAGGLE_USERNAME = "alessandroiovine"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Benvenuto nel tuo Bot Automazione Video!\n\n"
        "Scrivi `Genera: [il tuo testo]` e inviami il messaggio per far accendere i server Kaggle in automatico e iniziare la generazione del video."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id
    
    if not text.lower().startswith("genera:"):
        return

    script_text = text[7:].strip()
    await update.message.reply_text("🚀 Richiesta ricevuta! Sto accendendo i server Kaggle e inviando il codice. Riceverai il video qui quando sarà pronto (ci vorranno circa 15-20 minuti).")

    # Creiamo la cartella per l'upload su Kaggle
    deploy_dir = "kaggle_deploy"
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Salviamo il testo in un file
    with open(f"{deploy_dir}/input_text.txt", "w", encoding="utf-8") as f:
        f.write(script_text)
        
    # Creiamo il file di configurazione con il Chat ID per farglielo sapere
    with open(f"{deploy_dir}/config.json", "w", encoding="utf-8") as f:
        json.dump({
            "telegram_bot_token": TELEGRAM_TOKEN,
            "telegram_chat_id": str(chat_id)
        }, f)

    # Creiamo lo script Python che girerà su Kaggle
    kaggle_script = f"""import os
import subprocess

# Cloniamo il codice aggiornato da GitHub
os.system("git clone https://github.com/Ale11-tobi/video-factory.git")
os.chdir("video-factory")

# Copiamo i file input_text.txt e config.json che abbiamo caricato con questo script
os.system("cp ../input_text.txt .")
os.system("cp ../config.json .")

# Installiamo le dipendenze
os.system("sed -i '/TTS/d' requirements.txt") # Rimuoviamo TTS incompatibile
os.system("pip install -r requirements.txt")

# Facciamo partire il runner a riga di comando
os.system("python cli_runner.py input_text.txt")
"""
    with open(f"{deploy_dir}/run_video.py", "w", encoding="utf-8") as f:
        f.write(kaggle_script)

    # Creiamo i metadati per Kaggle
    metadata = {
      "id": f"{KAGGLE_USERNAME}/video-factory-run",
      "title": "Video Factory Run",
      "code_file": "run_video.py",
      "language": "python",
      "kernel_type": "script",
      "is_private": "true",
      "enable_gpu": "true",
      "enable_internet": "true",
      "dataset_sources": [],
      "competition_sources": [],
      "kernel_sources": []
    }
    with open(f"{deploy_dir}/kernel-metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Eseguiamo l'API di Kaggle per avviare il processo
    try:
        result = subprocess.run(["kaggle", "kernels", "push", "-p", deploy_dir], capture_output=True, text=True)
        if result.returncode == 0:
            await update.message.reply_text("✅ I server Cloud sono partiti con successo! Monitoro l'esecuzione...")
        else:
            await update.message.reply_text(f"❌ Errore nell'avvio dei server Kaggle:\n{result.stderr}")
    except FileNotFoundError:
        await update.message.reply_text("❌ L'API di Kaggle non è installata su questo server (PythonAnywhere). Assicurati di installarla e configurare kaggle.json.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot avviato! In ascolto...")
    app.run_polling()

if __name__ == "__main__":
    main()
