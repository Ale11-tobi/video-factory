import os
import shutil
import logging
import requests
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BRollManager:
    """
    Modulo 4: B-Roll & Smart Caching.
    Gestisce la ricerca, il download, l'archiviazione locale e la logica anti-ripetizione 
    delle clip video tramite le API di Pexels.
    """
    def __init__(self, pexels_api_key: str, archive_path: str = "local_archive/broll", temp_path: str = "temp"):
        if not pexels_api_key:
            raise ValueError("Pexels API Key non fornita.")
        self.api_key = pexels_api_key
        self.archive_path = archive_path
        self.temp_path = temp_path
        
        # Memory Buffer: Traccia i timestamp di utilizzo di ogni clip. Formato: {"nome_file.mp4": 12.5}
        self.usage_history: Dict[str, float] = {}
        
        os.makedirs(self.archive_path, exist_ok=True)
        os.makedirs(self.temp_path, exist_ok=True)

    def _normalize_prompt(self, prompt: str) -> str:
        """Pulisce la stringa per usarla come prefisso del nome file."""
        return "".join(c if c.isalnum() else "_" for c in prompt.strip().lower())

    def _get_local_candidates(self, normalized_prompt: str) -> list:
        """Ottiene tutte le clip presenti in cache che matchano il prompt."""
        candidates = []
        for filename in os.listdir(self.archive_path):
            if filename.startswith(normalized_prompt) and filename.endswith(".mp4"):
                candidates.append(filename)
        return candidates

    def _fetch_from_pexels(self, prompt: str, normalized_prompt: str) -> Optional[str]:
        """Esegue la chiamata API, scarica la clip verticale in HD/4K e la salva nel local_archive."""
        logger.info(f"Ricerca su Pexels API per: '{prompt}'...")
        headers = {"Authorization": self.api_key}
        params = {
            "query": prompt,
            "orientation": "portrait", # Tassativo per TikTok/Reels
            "size": "large",           # Preferiamo video ad alta risoluzione
            "per_page": 5              # Recuperiamo 5 opzioni per pescare la migliore
        }
        
        try:
            response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("videos"):
                logger.warning(f"Nessun video trovato su Pexels per il prompt '{prompt}'.")
                return None
            
            for video in data["videos"]:
                video_files = video.get("video_files", [])
                # Ordina decrescente per altezza garantendo il miglior file HD/4K portrait
                video_files.sort(key=lambda x: x.get("height", 0), reverse=True)
                
                for vf in video_files:
                    if vf.get("link"):
                        download_url = vf["link"]
                        
                        # Generazione nome file per la cache (es: hacker_typing_dark_1.mp4)
                        existing_count = len(self._get_local_candidates(normalized_prompt))
                        new_filename = f"{normalized_prompt}_{existing_count + 1}.mp4"
                        save_path = os.path.join(self.archive_path, new_filename)
                        
                        logger.info(f"Download clip in corso: {new_filename}...")
                        vid_resp = requests.get(download_url, stream=True)
                        vid_resp.raise_for_status()
                        
                        with open(save_path, "wb") as f:
                            for chunk in vid_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                                
                        logger.info(f"Download completato: {new_filename}")
                        return new_filename
                        
            return None
            
        except Exception as e:
            logger.error(f"Errore fatale nell'API Pexels: {e}")
            return None

    def process_scene_broll(self, scene_id: int, prompt: str, current_timeline_sec: float) -> Optional[str]:
        """
        Cuore del Modulo: Risolve la richiesta di B-Roll con Cache + Buffer anti-ripetizione.
        Restituisce il path finale per l'Assembly Engine.
        """
        if not prompt or prompt.lower() == "null":
            return None
            
        normalized_prompt = self._normalize_prompt(prompt)
        candidates = self._get_local_candidates(normalized_prompt)
        selected_filename = None
        
        # 1. SMART CACHING & MEMORY BUFFER
        # Verifichiamo se esiste una clip in archivio che non viola i 15 secondi di girato
        for candidate in candidates:
            last_used_sec = self.usage_history.get(candidate, -999.0)
            if (current_timeline_sec - last_used_sec) >= 15.0:
                selected_filename = candidate
                logger.info(f"Cache HIT [Valido]: '{prompt}' -> {selected_filename} (Usato ultima volta a {last_used_sec}s)")
                break
            else:
                logger.info(f"Cache SKIP [Violazione 15s Buffer]: '{prompt}' -> {candidate}")
                
        # 2. FALLBACK API
        if not selected_filename:
            logger.info(f"Cache MISS (o nessun video valido). Richiesta API Pexels per '{prompt}'.")
            selected_filename = self._fetch_from_pexels(prompt, normalized_prompt)
            
        if not selected_filename:
            logger.error(f"Impossibile generare un B-Roll per la scena {scene_id} ({prompt}).")
            return None
            
        # 3. REGISTRAZIONE NEL BUFFER E PREPARAZIONE TEMP
        # Aggiorniamo la memoria con l'istante attuale
        self.usage_history[selected_filename] = current_timeline_sec
        
        source_path = os.path.join(self.archive_path, selected_filename)
        dest_filename = f"scene_{scene_id}_broll.mp4"
        dest_path = os.path.join(self.temp_path, dest_filename)
        
        # Ottimizzazione I/O disco: Creiamo un hardlink fisico. 
        # Risparmia spazio e tempo zero. Fallback su shutil.copy2 se il filesystem non lo supporta.
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.link(source_path, dest_path)
            logger.info(f"Hardlink creato in temp: {dest_filename}")
        except OSError:
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copia fisica creata in temp: {dest_filename}")
            
        return dest_path

# --- TEST LOCALE ---
if __name__ == "__main__":
    # Test esecuzione isolata
    API_KEY = os.environ.get("PEXELS_API_KEY", "INSERISCI_TUA_API")
    manager = BRollManager(pexels_api_key=API_KEY, archive_path="local_archive/broll", temp_path="temp")
    
    # Simulazione Timeline
    print("Scena 1 (t=0.0):")
    manager.process_scene_broll(scene_id=1, prompt="hacker typing dark", current_timeline_sec=0.0)
    
    # Stessa query, ma prima dei 15 secondi -> Scatterà il fallback API!
    print("\nScena 2 (t=8.0):")
    manager.process_scene_broll(scene_id=2, prompt="hacker typing dark", current_timeline_sec=8.0)
    
    # Stessa query dopo i 15 secondi -> Scatterà un Cache Hit del video scaricato per la scena 1!
    print("\nScena 3 (t=20.0):")
    manager.process_scene_broll(scene_id=3, prompt="hacker typing dark", current_timeline_sec=20.0)
