import os
import sys
import json
import shutil
import logging
import random
import requests
import yt_dlp
import librosa
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioDesign:
    """
    Modulo 5: Audio Design & Music.
    Gestisce il download della musica (yt-dlp), l'analisi ritmica dei kick (librosa)
    e l'approvvigionamento in cache degli Effetti Sonori (Freesound API).
    """
    def __init__(self, music_archive: str = "local_archive/music",
                 sfx_archive: str = "local_archive/sfx",
                 temp_path: str = "temp"):
        
        self.music_archive = music_archive
        self.sfx_archive = sfx_archive
        self.temp_path = temp_path
        
        os.makedirs(self.music_archive, exist_ok=True)
        os.makedirs(self.sfx_archive, exist_ok=True)
        os.makedirs(self.temp_path, exist_ok=True)

    def fetch_background_music(self, playlist_url: str) -> str:
        """
        Controlla l'archivio. Se serve, scarica tracce da YouTube e crea 
        l'hardlink in temp/bg_music.wav.
        """
        logger.info("Verifica brani musicali nel local_archive...")
        local_tracks = [f for f in os.listdir(self.music_archive) if f.endswith(".wav")]
        
        if not local_tracks and playlist_url:
            logger.info("Archivio vuoto. Avvio scaricamento YT in alta qualità (convertito in .wav)...")
            BASE_DIR = os.path.dirname(os.path.dirname(__file__))
            ffmpeg_exe = os.path.join(BASE_DIR, "venv", "Scripts", "ffmpeg.exe")
            if not os.path.exists(ffmpeg_exe): ffmpeg_exe = "ffmpeg"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.music_archive, '%(title)s.%(ext)s'),
                'ffmpeg_location': ffmpeg_exe,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                # Limitiamo a 3 canzoni per velocizzare l'MVP
                'playlist_items': '1-3',
                'quiet': False,
                'no_warnings': True
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([playlist_url])
                local_tracks = [f for f in os.listdir(self.music_archive) if f.endswith(".wav")]
            except Exception as e:
                logger.error(f"Errore yt-dlp: {e}")
                
        if not local_tracks:
            raise FileNotFoundError("Nessuna traccia musicale disponibile e download fallito.")
            
        # Per ora scegliamo una traccia random dalla libreria locale
        selected_track = random.choice(local_tracks)
        logger.info(f"Music Track selezionata: {selected_track}")
        
        source_path = os.path.join(self.music_archive, selected_track)
        dest_path = os.path.join(self.temp_path, "bg_music.wav")
        
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.link(source_path, dest_path)
        except OSError:
            shutil.copy2(source_path, dest_path)
            
        return dest_path

    def analyze_beats(self, audio_path: str = "temp/bg_music.wav", output_json: str = "temp/music_beats.json") -> List[float]:
        """
        Usa librosa per rilevare gli 'onset' (Kick drum / bass drops).
        Questo array temporale piloterà lo snapping dei tagli video nel Modulo 6.
        """
        logger.info(f"Avvio analisi ritmica Librosa su: {audio_path}")
        try:
            # sr=22050 velocizza l'elaborazione mantenendo ottima precisione per il tracking dei beat
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Rilevamento envelope energetico e marker di onset
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            # Parametri tunati per catturare colpi secchi ed evitare micro-battiti inutili
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, wait=25, pre_max=20, post_max=20, pre_avg=100, post_avg=100, delta=0.2)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            
            beats = [round(float(t), 3) for t in onset_times]
            
            os.makedirs(os.path.dirname(output_json), exist_ok=True)
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(beats, f, indent=4)
                
            logger.info(f"Trovati {len(beats)} beat rilevanti. Array salvato in: {output_json}")
            return beats
        except Exception as e:
            logger.error(f"Errore critico durante librosa beat tracking: {e}")
            raise

    def _fetch_freesound_sfx(self, trigger_name: str) -> Optional[str]:
        """Scaricamento fallback API-Free tramite yt-dlp da YouTube"""
        logger.info(f"API-Free: Cerco SFX '{trigger_name}' su YouTube...")
        filename_base = trigger_name.replace(" ", "_")
        filename_wav = f"{filename_base}.wav"
        
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        ffmpeg_exe = os.path.join(BASE_DIR, "venv", "Scripts", "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe): ffmpeg_exe = "ffmpeg"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.sfx_archive, f"{filename_base}.%(ext)s"),
            'ffmpeg_location': ffmpeg_exe,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'match_filter': yt_dlp.utils.match_filter_func("duration < 15"),
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch1:{trigger_name} sound effect short"])
            return filename_wav
        except Exception as e:
            logger.error(f"Errore download SFX da YouTube: {e}")
            return None

    def process_scene_sfx(self, director_cut_path: str = "temp/director_cut.json"):
        """
        Analizza le scene, preleva/scarica gli SFX richiesti e crea i link in temp/.
        """
        if not os.path.exists(director_cut_path):
            logger.error("File director_cut.json mancante! Esegui prima il Modulo 1.")
            return
            
        with open(director_cut_path, "r", encoding="utf-8") as f:
            director_cut = json.load(f)
            
        for scene in director_cut.get("scenes", []):
            trigger = scene.get("sfx_trigger")
            scene_id = scene.get("id")
            
            if trigger and str(trigger).lower() != "null":
                trigger_clean = trigger.lower().strip()
                
                # Cerca in cache
                local_files = [f for f in os.listdir(self.sfx_archive) if trigger_clean in f.lower()]
                selected_sfx = None
                
                if local_files:
                    selected_sfx = random.choice(local_files) # Varia i suoni uguali se presenti più hit
                    logger.info(f"Cache SFX HIT: {trigger_clean} -> {selected_sfx}")
                else:
                    logger.info(f"Cache SFX MISS: {trigger_clean}. Avvio download API...")
                    selected_sfx = self._fetch_freesound_sfx(trigger_clean)
                    
                if selected_sfx:
                    source_path = os.path.join(self.sfx_archive, selected_sfx)
                    ext = os.path.splitext(selected_sfx)[1]
                    dest_filename = f"scene_{scene_id}_sfx_{trigger_clean}{ext}"
                    dest_path = os.path.join(self.temp_path, dest_filename)
                    
                    try:
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        os.link(source_path, dest_path)
                    except OSError:
                        shutil.copy2(source_path, dest_path)
                        
                    logger.info(f"Link SFX per scena {scene_id} pronto in {dest_path}")

# --- ESEMPIO D'USO ---
# if __name__ == "__main__":
#     audio = AudioDesign(freesound_api_key="TUA_API_KEY")
#     audio.fetch_background_music("URL_PLAYLIST")
#     beats = audio.analyze_beats()
#     audio.process_scene_sfx()
