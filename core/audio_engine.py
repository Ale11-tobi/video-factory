import os
import json
import asyncio
import logging
import edge_tts
from faster_whisper import WhisperModel

try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioEngine:
    """
    Modulo 2: Audio & TTS.
    Genera la voce tramite XTTSv2 (qualità super eccellente) con fallback su edge-tts.
    Utilizza faster-whisper per estrarre i timestamp esatti per il lip-sync e i sottotitoli.
    """
    def __init__(self, whisper_model_size: str = "tiny", device: str = "cuda"):
        """
        Inizializza il motore Whisper.
        Su RTX 4060 (8GB VRAM) il modello "tiny" o "base" è perfetto ed esegue l'inferenza
        in pochi secondi. compute_type="float16" riduce l'impronta in VRAM del 50%.
        Se non trova CUDA, esegue il fallback su CPU con int8.
        """
        try:
            compute_type = "float16" if device == "cuda" else "int8"
            logger.info(f"Caricamento faster-whisper (modello: {whisper_model_size}, device: {device}, compute: {compute_type})...")
            self.whisper_model = WhisperModel(whisper_model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logger.warning(f"Errore caricamento CUDA per Whisper, fallback su CPU... Dettagli: {e}")
            self.whisper_model = WhisperModel(whisper_model_size, device="cpu", compute_type="int8")
            
        self.xtts_model = None
        if XTTS_AVAILABLE:
            try:
                logger.info("Caricamento modello XTTSv2 in corso (richiede VRAM)...")
                # XTTS scaricherà in automatico i pesi se non presenti (~2GB)
                self.xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            except Exception as e:
                logger.error(f"Impossibile caricare XTTSv2, fallback a edge-tts: {e}")
                self.xtts_model = None

    async def generate_tts(self, text: str, output_path: str = "temp/master_voice.wav", voice: str = "it-IT-DiegoNeural") -> str:
        """
        Genera l'audio utilizzando XTTSv2. Se non è installato, usa edge-tts.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if self.xtts_model is not None:
            logger.info("Generazione vocale con XTTSv2 (Qualità Ultra)...")
            ref_voice_path = "models/reference_voice.wav"
            os.makedirs("models", exist_ok=True)
            
            # Se non abbiamo una voce di riferimento umana, ne creiamo una perfetta con edge-tts da clonare!
            if not os.path.exists(ref_voice_path):
                logger.info("Creazione voce di riferimento per la clonazione XTTS...")
                ref_text = "Ciao, questa è la mia voce naturale. Sono pronto per iniziare la registrazione del video spaziale."
                comm = edge_tts.Communicate(ref_text, voice)
                await comm.save(ref_voice_path)
                
            try:
                self.xtts_model.tts_to_file(text=text, speaker_wav=ref_voice_path, language="it", file_path=output_path)
                logger.info(f"Traccia vocale XTTS salvata con successo in: {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"Errore generazione XTTS: {e}. Fallback su edge-tts...")
                
        logger.info(f"Generazione traccia vocale con edge-tts (Voce: {voice})...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        logger.info(f"Traccia vocale salvata con successo in: {output_path}")
        return output_path

    def extract_word_timestamps(self, audio_path: str, output_json_path: str = "temp/word_timestamps.json") -> list:
        """
        Analizza l'audio con faster-whisper estraendo i timestamp precisi per ogni parola.
        """
        logger.info(f"Estrazione word-level timestamps da {audio_path}...")
        
        # forced language "it" velocizza l'elaborazione evitando il lang-detect
        segments, info = self.whisper_model.transcribe(
            audio_path, 
            word_timestamps=True, 
            language="it"
        )
        
        words_data = []
        # segments è un generatore, iterandolo avviamo l'inferenza effettiva
        for segment in segments:
            for word in segment.words:
                words_data.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3)
                })
                
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(words_data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Estratte {len(words_data)} parole. JSON salvato in: {output_json_path}")
        return words_data

    async def process_full_audio_pipeline(self, script_text: str, audio_output: str = "temp/master_voice.wav", json_output: str = "temp/word_timestamps.json", voice: str = "it-IT-DiegoNeural"):
        """
        Orchestra il flusso completo: 1. TTS -> 2. Timestamps.
        """
        await self.generate_tts(script_text, audio_output, voice)
        # Esegue la trascrizione Whisper in parallelo bloccante (va bene perché Whisper libera VRAM velocemente)
        timestamps = self.extract_word_timestamps(audio_output, json_output)
        return timestamps

# --- TEST LOCALE ---
if __name__ == "__main__":
    async def main():
        engine = AudioEngine(whisper_model_size="tiny", device="cuda")
        testo = "Questo è un test del Modulo 2. Verifichiamo il lip sync parola per parola."
        
        try:
            # Creiamo una finta directory temp locale se avviato direttamente
            os.makedirs("temp", exist_ok=True)
            risultati = await engine.process_full_audio_pipeline(
                script_text=testo,
                audio_output="temp/master_voice.wav",
                json_output="temp/word_timestamps.json"
            )
            print(json.dumps(risultati[:5], indent=2))
            print("... test completato con successo!")
        except Exception as e:
            print(f"Errore durante il test: {e}")

    asyncio.run(main())
