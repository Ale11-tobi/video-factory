import os
import logging
import asyncio

# Importazione dei Moduli
from core.semantic_director import SemanticDirector
from core.audio_engine import AudioEngine
from core.avatar_engine import AvatarEngine
from core.broll_manager import BRollManager
from core.audio_design import AudioDesign
from core.assembly_engine import AssemblyEngine
from core.telegram_notifier import send_telegram_video

logger = logging.getLogger(__name__)

# Configurazione API Keys integrate
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "1BBVi0DC0Zt5QhQG37RirCikK7zL2OYMJhXCHmV7ncORynDfvClYMZVj")

async def process_mode_a(testo: str, format_ratio: str = "9:16", progress_callback=None, telegram_token: str = "", telegram_chat_id: str = "") -> str:
    """Mode A: Zero-Touch Content Factory"""
    logger.info("=== MODE A: Avvio Pipeline ===")
    
    director = SemanticDirector(api_key=GROQ_API_KEY)
    audio_engine = AudioEngine(whisper_model_size="tiny", device="cuda")
    avatar = AvatarEngine()
    broll = BRollManager(pexels_api_key=PEXELS_API_KEY)
    sound = AudioDesign()
    assembly = AssemblyEngine(mode="A", format_ratio=format_ratio)

    if progress_callback: progress_callback("Generazione Regia JSON...", 10)
    director_cut = await director.generate_director_cut(testo, output_path="temp/director_cut.json")
    
    # ESTRAZIONE TESTO PURO: Uniamo solo i segmenti di testo validati e puliti dall'IA
    testo_narrativo = " ".join([scene.get("text_segment", "") for scene in director_cut.get("scenes", [])])
    
    if progress_callback: progress_callback("Generazione Audio TTS...", 30)
    await audio_engine.process_full_audio_pipeline(testo_narrativo)
    
    if progress_callback: progress_callback("Rendering Avatar Statico...", 40)
    avatar.render_avatar(vlog_mode=False)
    
    if progress_callback: progress_callback("Ricerca B-Roll su Pexels...", 60)
    current_time = 0.0
    for scene in director_cut.get("scenes", []):
        if scene.get("scene_type") == "b-roll":
            broll.process_scene_broll(scene["id"], scene.get("broll_prompt"), current_time)
            current_time += 15.0 
            
    if progress_callback: progress_callback("Download Musica & Effetti Sonori...", 80)
    sound.fetch_background_music("https://www.youtube.com/playlist?list=PLRBp0Fe2GpgnIh0AiYKh7o7HnYAej-5ph")
    sound.analyze_beats(audio_path="temp/bg_music.wav", output_json="temp/music_beats.json")
    sound.process_scene_sfx(director_cut_path="temp/director_cut.json")
    
    if progress_callback: progress_callback("Assemblaggio FFmpeg (Video Finale)...", 95)
    assembly.build_and_run()
    
    final_path = os.path.join(assembly.output_path, "final_video_A.mp4")
    logger.info(f"Pipeline Mode A completata: {final_path}")
    
    if telegram_token and telegram_chat_id:
        if progress_callback: progress_callback("Invio su Telegram in corso...", 98)
        send_telegram_video(telegram_token, telegram_chat_id, final_path)
        
    if progress_callback: progress_callback("Montaggio Completato!", 100)
    return final_path

async def process_mode_b_c(mode_type: str, file_path: str, format_ratio: str = "9:16", progress_callback=None, telegram_token: str = "", telegram_chat_id: str = "") -> str:
    """Mode B (Auto-Editor Vlog) e Mode C (Faceless/Podcast)"""
    logger.info(f"=== MODE {mode_type}: Elaborazione File RAW ===")
    
    audio_engine = AudioEngine(whisper_model_size="tiny", device="cuda")
    director = SemanticDirector(api_key=GROQ_API_KEY)
    avatar = AvatarEngine()
    broll = BRollManager(pexels_api_key=PEXELS_API_KEY)
    sound = AudioDesign()
    assembly = AssemblyEngine(mode=mode_type, format_ratio=format_ratio, raw_media_path=file_path)

    os.makedirs("temp", exist_ok=True)
    master_audio = "temp/master_voice.wav"
    
    if progress_callback: progress_callback("Estrazione Audio RAW...", 10)
    os.system(f'ffmpeg -y -i "{file_path}" -vn -acodec pcm_s16le -ar 44100 -ac 2 "{master_audio}" -loglevel error')

    if progress_callback: progress_callback("Trascrizione AI (Whisper)...", 30)
    timestamps = audio_engine.extract_word_timestamps(master_audio)
    testo_trascritto = " ".join([w["word"] for w in timestamps])

    if progress_callback: progress_callback("Generazione Regia JSON...", 40)
    director_cut = await director.generate_director_cut(testo_trascritto, output_path="temp/director_cut.json")
    
    # ESTRAZIONE TESTO PURO: Uniamo solo i segmenti di testo validati e puliti dall'IA
    testo_narrativo = " ".join([scene.get("text_segment", "") for scene in director_cut.get("scenes", [])])
    
    if progress_callback: progress_callback("Generazione Audio TTS...", 30)
    await audio_engine.process_full_audio_pipeline(testo_narrativo)
    
    if progress_callback: progress_callback("Gestione Avatar...", 50)
    avatar.render_avatar(vlog_mode=True)
    
    if progress_callback: progress_callback("Fetch B-Roll & Assets...", 70)
    current_time = 0.0
    for scene in director_cut.get("scenes", []):
        is_broll = scene.get("scene_type") == "b-roll" or mode_type == "C"
        if is_broll:
            broll.process_scene_broll(scene["id"], scene.get("broll_prompt", "cinematic abstract"), current_time)
            current_time += 15.0
            
    if progress_callback: progress_callback("Download Musica & Effetti Sonori...", 80)
    sound.fetch_background_music("https://www.youtube.com/playlist?list=PLRBp0Fe2GpgnIh0AiYKh7o7HnYAej-5ph")
    sound.analyze_beats(audio_path="temp/bg_music.wav", output_json="temp/music_beats.json")
    sound.process_scene_sfx(director_cut_path="temp/director_cut.json")
    
    if progress_callback: progress_callback("Assemblaggio FFmpeg (Video Finale)...", 95)
    assembly.build_and_run()
    
    final_path = os.path.join(assembly.output_path, f"final_video_{mode_type}.mp4")
    logger.info(f"Pipeline Mode {mode_type} completata: {final_path}")
    
    if telegram_token and telegram_chat_id:
        if progress_callback: progress_callback("Invio su Telegram in corso...", 98)
        send_telegram_video(telegram_token, telegram_chat_id, final_path)
        
    if progress_callback: progress_callback("Montaggio Completato!", 100)
    return final_path
