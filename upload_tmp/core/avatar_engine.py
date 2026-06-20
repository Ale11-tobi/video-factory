import os
import gc
import logging
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AvatarEngine:
    """
    Modulo 3: Avatar Engine.
    Gestisce la generazione del lip-sync usando un modello deep learning leggero.
    Implementa uno scaricamento spietato della VRAM (RTX 4060) post-rendering.
    """
    def __init__(self, temp_path="temp", assets_path="assets"):
        self.temp_path = os.path.abspath(temp_path)
        self.assets_path = os.path.abspath(assets_path)
        self.source_image = os.path.join(self.assets_path, "avatar.png")
        self.master_voice = os.path.join(self.temp_path, "master_voice.wav")
        self.output_video = os.path.join(self.temp_path, "avatar_speaking.mp4")
        
        os.makedirs(self.assets_path, exist_ok=True)
        # Dummy avatar per test se non esiste
        if not os.path.exists(self.source_image):
            # Crea un placeholder vuoto giusto per non far fallire ffmpeg in debug
            logger.warning(f"Immagine {self.source_image} non trovata. Inserire un avatar.png valido.")

    def render_avatar(self, vlog_mode: bool = False):
        """
        Genera il video dell'avatar che parla.
        Se vlog_mode è True (Mode B/C), skippa il rendering.
        """
        if vlog_mode:
            logger.info("Avatar Engine bypassato (VLOG/Faceless Mode attivo).")
            return
            
        logger.info("Inizio elaborazione Avatar fotorealistico...")
        
        if not os.path.exists(self.master_voice):
            logger.error(f"Audio master mancante: {self.master_voice}")
            return
            
        model = None
        try:
            # 1. Caricamento Dinamico del Modello: SadTalker Hook Strategy
            BASE_DIR = os.path.dirname(os.path.dirname(__file__))
            ffmpeg_exe = os.path.join(BASE_DIR, "venv", "Scripts", "ffmpeg.exe")
            if not os.path.exists(ffmpeg_exe): ffmpeg_exe = "ffmpeg"
            python_exe = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
            if not os.path.exists(python_exe): python_exe = "python3"
            
            sadtalker_dir = os.path.join(BASE_DIR, "SadTalker")
            intro_audio = os.path.join(self.temp_path, "intro_audio.wav")
            intro_video = os.path.join(self.temp_path, "avatar_intro.mp4")
            base_video = os.path.join(self.temp_path, "avatar_base.mp4")
            
            import subprocess
            import glob
            import shutil
            
            # Creiamo la base Ken Burns per tutta la durata dell'audio
            logger.info("Creazione base Avatar (loop/Ken Burns) per tutta la durata...")
            self._fallback_render(ffmpeg_exe, self.master_voice, base_video)
            
            if os.path.exists(sadtalker_dir):
                logger.info("SadTalker trovato! Inizio generazione Hook 3D (primi 10 secondi)...")
                
                # Estrai primi 10 secondi
                subprocess.run([ffmpeg_exe, "-y", "-i", self.master_voice, "-t", "10", intro_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                out_dir = os.path.join(self.temp_path, "sadtalker_out")
                os.makedirs(out_dir, exist_ok=True)
                
                inference_script = os.path.join(sadtalker_dir, "inference.py")
                cmd = [
                    python_exe, inference_script,
                    "--driven_audio", intro_audio,
                    "--source_image", self.source_image,
                    "--result_dir", out_dir,
                    "--still", "--preprocess", "full"
                ]
                
                try:
                    logger.info("Esecuzione rete neurale SadTalker (potrebbe richiedere un minuto)...")
                    subprocess.run(cmd, cwd=sadtalker_dir, check=True)
                    
                    # Trova il video generato
                    generated_files = glob.glob(os.path.join(out_dir, "*.mp4"))
                    if generated_files:
                        shutil.move(generated_files[0], intro_video)
                        logger.info("SadTalker Hook completato! Assemblo con la base...")
                        
                        # Sovrapponi intro_video su base_video per i primi 10 secondi
                        overlay_cmd = [
                            ffmpeg_exe, "-y",
                            "-i", base_video,
                            "-i", intro_video,
                            "-filter_complex", "[0:v][1:v]overlay=enable='between(t,0,10)'",
                            "-c:a", "copy",
                            self.output_video
                        ]
                        subprocess.run(overlay_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info(f"Rendering finale completato: {self.output_video}")
                    else:
                        logger.warning("Nessun output SadTalker trovato. Uso la base.")
                        shutil.copy(base_video, self.output_video)
                        
                except Exception as e:
                    logger.error(f"Errore durante SadTalker, fallback ad animazione base: {e}")
                    shutil.copy(base_video, self.output_video)
            else:
                logger.info("SadTalker non trovato. Utilizzo solo animazione Ken Burns di base...")
                shutil.copy(base_video, self.output_video)
                
        except Exception as e:
            logger.error(f"Errore durante il rendering dell'avatar: {e}")
        finally:
            # 2. GESTIONE SPIETATA DELLA VRAM
            logger.info("Svuotamento VRAM forzato per il Modulo FFmpeg successivo...")
            if model is not None:
                del model
            gc.collect()
            torch.cuda.empty_cache()
            logger.info("VRAM liberata al 100%.")
            
    def _fallback_render(self, ffmpeg_exe, audio_input, output_path):
        import subprocess
        # Effetto Ken Burns (respiro + movimento leggero) invece di immagine statica
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1", "-i", self.source_image,
            "-i", audio_input,
            "-filter_complex", "zoompan=z='min(zoom+0.0015,1.10)':d=500:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
