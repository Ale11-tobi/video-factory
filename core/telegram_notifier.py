import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_video(token: str, chat_id: str, video_path: str, caption: str = "🎬 Ecco il tuo video generato dalla Zero-Touch Factory!") -> bool:
    """Invia un video MP4 a un Chat ID di Telegram."""
    if not token or not chat_id:
        logger.warning("Telegram Bot Token o Chat ID mancanti. Notifica ignorata.")
        return False
        
    if not os.path.exists(video_path):
        logger.error(f"Video non trovato per l'invio su Telegram: {video_path}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendVideo"
    
    logger.info(f"Invio video su Telegram a {chat_id} in corso... (potrebbe richiedere qualche minuto a seconda del peso)")
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {'chat_id': chat_id, 'caption': caption}
            
            response = requests.post(url, data=data, files=files)
            
        if response.status_code == 200:
            logger.info("✅ Video inviato con successo su Telegram!")
            # Estrazione URL diretto per il sito web
            try:
                res_data = response.json()
                file_id = res_data["result"]["video"]["file_id"]
                file_req = requests.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
                file_path = file_req.json()["result"]["file_path"]
                direct_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                return direct_url
            except Exception as e:
                logger.error(f"Errore estrazione URL Telegram: {e}")
                return "SENT_NO_URL"
        else:
            logger.error(f"❌ Errore API Telegram [{response.status_code}]: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Errore critico durante l'invio su Telegram: {e}")
        return False

def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Invia un messaggio testuale a un Chat ID di Telegram (utile per gli errori)."""
    if not token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            logger.info("✅ Messaggio di alert inviato con successo su Telegram!")
            return True
        else:
            logger.error(f"❌ Errore API Telegram [{response.status_code}]: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore critico durante l'invio messaggio su Telegram: {e}")
        return False
