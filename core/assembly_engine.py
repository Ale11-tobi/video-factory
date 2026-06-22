import os
import sys
import json
import subprocess
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AssemblyEngine:
    """
    Modulo 6 (Tri-Mode): Assembly Engine tramite FFmpeg Complex Filtergraph.
    Gestisce la logica chirurgica dell'overlay a blocchi millisecondo.
    """
    def __init__(self, mode: str = "A", format_ratio: str = "9:16", raw_media_path: str = None, temp_path: str = "temp", output_path: str = "outputs"):
        self.mode = mode.upper()
        self.format_ratio = format_ratio
        self.raw_media_path = raw_media_path
        self.temp_path = temp_path
        self.output_path = output_path
        
        if self.format_ratio == "16:9":
            self.w, self.h = 1920, 1080
        else:
            self.w, self.h = 1080, 1920
            
        os.makedirs(self.output_path, exist_ok=True)

    def _get_audio_duration(self, filepath: str) -> float:
        # Fallback ffprobe if moviepy is not reliable for duration
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        ffprobe_exe = os.path.join(BASE_DIR, "venv", "Scripts", "ffprobe.exe")
        if not os.path.exists(ffprobe_exe): ffprobe_exe = "ffprobe" # Fallback globale
        cmd = [ffprobe_exe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return float(result.stdout.strip())

    def _generate_ass_subtitles(self, words: List[Dict], output_ass: str):
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {self.w}
PlayResY: {self.h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Alignment, BorderStyle, Outline, Shadow, MarginL, MarginR, MarginV
Style: MrBeast,Impact,90,&H00FFFFFF,&H00000000,&H80000000,-1,0,2,1,6,0,10,10,150

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        def format_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            cs = int(round((seconds - int(seconds)) * 100))
            return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

        with open(output_ass, "w", encoding="utf-8") as f:
            f.write(ass_header)
            for w in words:
                start_t = format_time(w["start"])
                end_t = format_time(w["end"])
                text = w["word"].upper().replace('"', '').replace("'", "")
                
                color_tag = ""
                emoji_event = ""
                
                word_clean = text.strip()
                if len(word_clean) > 7:
                    color_tag = "\\c&H0000FFFF&" # Giallo
                elif word_clean in ["SPAZIALE", "INCREDIBILE", "ASSURDO", "SEGRETO", "BOMBA", "SOLDI", "GRATIS"]:
                    color_tag = "\\c&H0000FF00&" # Verde
                    
                    # Seleziona l'emoji in base alla parola
                    emoji_char = "💥"
                    if word_clean in ["SOLDI", "GRATIS"]: emoji_char = "💰"
                    elif word_clean in ["SEGRETO"]: emoji_char = "🤫"
                    elif word_clean in ["SPAZIALE", "INCREDIBILE"]: emoji_char = "🚀"
                    
                    # Calcola i tempi in millisecondi per l'animazione ASS
                    dur_ms = int((w["end"] - w["start"]) * 1000)
                    fade_out_start = max(100, dur_ms - 150)
                    
                    # Aggiunge l'emoji animata in alto (pos Y=self.h/3)
                    emoji_event = f"Dialogue: 0,{start_t},{end_t},MrBeast,,0,0,0,,{{\\pos({self.w//2},{self.h//3})\\fscx0\\fscy0\\t(0,100,\\fscx250\\fscy250)\\t({fade_out_start},{dur_ms},\\fscx0\\fscy0)}}{emoji_char}\n"
                    
                # Effetto Pop (Alex Hormozi style)
                pop_effect = "{\\fscx80\\fscy80\\t(0,50,\\fscx110\\fscy110)\\t(50,150,\\fscx100\\fscy100)" + color_tag + "}"
                
                f.write(f"Dialogue: 0,{start_t},{end_t},MrBeast,,0,0,0,,{pop_effect}{text}\n")
                if emoji_event:
                    f.write(emoji_event)

    def _find_closest_beat(self, target_time: float, beats: List[float]) -> float:
        if not beats:
            return target_time
        return min(beats, key=lambda b: abs(b - target_time))

    def build_and_run(self):
        logger.info(f"Avvio Assembly Graph (Mode {self.mode})...")
        
        with open(os.path.join(self.temp_path, "director_cut.json"), "r", encoding="utf-8") as f:
            director_cut = json.load(f)
        with open(os.path.join(self.temp_path, "word_timestamps.json"), "r", encoding="utf-8") as f:
            words = json.load(f)
            
        beats = []
        beats_path = os.path.join(self.temp_path, "music_beats.json")
        if os.path.exists(beats_path):
            with open(beats_path, "r", encoding="utf-8") as f:
                beats = json.load(f)

        master_voice_path = os.path.join(self.temp_path, "master_voice.wav")
        bg_music_path = os.path.join(self.temp_path, "bg_music.wav")
        total_duration = self._get_audio_duration(master_voice_path)

        ass_path = os.path.join(self.temp_path, "subtitles.ass")
        self._generate_ass_subtitles(words, ass_path)

        scenes = director_cut.get("scenes", [])
        cut_times = [0.0]
        target_step = total_duration / max(1, len(scenes))
        for i in range(1, len(scenes)):
            target = i * target_step
            beat = self._find_closest_beat(target, beats)
            # Evita cut con durata 0.0 o sovrapposizioni errate
            if beat >= cut_times[-1] + 0.5:
                cut_times.append(beat)
            else:
                cut_times.append(max(cut_times[-1] + 0.5, target))
                
        if total_duration >= cut_times[-1] + 0.5:
            cut_times.append(total_duration)
        else:
            cut_times.append(cut_times[-1] + 0.5)

        inputs = []
        filter_complex = []
        
        # --- CREAZIONE DEL NODO "BASE" ---
        if self.mode == "A":
            inputs.extend(["-i", os.path.join(self.temp_path, "avatar_speaking.mp4")])
            filter_complex.append(f"[0:v]scale={self.w}:{self.h}:force_original_aspect_ratio=increase,crop={self.w}:{self.h},setsar=1[base];")
            broll_idx = 1
        elif self.mode == "B":
            inputs.extend(["-i", self.raw_media_path])
            filter_complex.append(f"[0:v]scale={self.w}:{self.h}:force_original_aspect_ratio=increase,crop={self.w}:{self.h},setsar=1[base];")
            broll_idx = 1
        elif self.mode == "C":
            filter_complex.append(f"color=c=black:s={self.w}x{self.h}:d={total_duration}[base];")
            broll_idx = 0

        # --- CATENA DI OVERLAY DINAMICO ---
        last_overlay = "[base]"
        for i, scene in enumerate(scenes):
            is_broll = scene.get("scene_type") == "b-roll" or self.mode == "C"
            fallback_avatar = scene.get("fallback_avatar")
            
            clip_path = None
            if fallback_avatar and os.path.exists(fallback_avatar):
                clip_path = fallback_avatar
            elif is_broll:
                broll_path = os.path.join(self.temp_path, f"scene_{scene['id']}_broll.mp4")
                if os.path.exists(broll_path):
                    clip_path = broll_path
                    
            if clip_path:
                inputs.extend(["-i", clip_path])
                start_t = cut_times[i]
                end_t = cut_times[i+1]
                duration = end_t - start_t
                
                # --- HOOK ZONE (First 30 seconds) ---
                is_hook_zone = start_t < 30.0
                
                if is_hook_zone:
                    # Dynamic Camera: alternate between slow zoom and slight scale
                    if i % 2 == 0:
                        # Slow zoom in
                        cam_effect = f"scale={int(self.w*1.5)}:{int(self.h*1.5)},zoompan=z='min(zoom+0.0015,1.15)':d={int(duration*25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                    else:
                        # Close-up (scaled up static, focus on upper half for faces)
                        cam_effect = f"scale={int(self.w*1.3)}:{int(self.h*1.3)},crop={self.w}:{self.h}:(in_w-out_w)/2:(in_h-out_h)/4,"
                else:
                    cam_effect = f"scale={self.w}:{self.h}:force_original_aspect_ratio=increase,"
                    
                if is_hook_zone and i > 0:
                    # Aggiungiamo un leggero flash cinematico all'inizio della clip per mascherare il taglio
                    flash_effect = ",eq=brightness='if(between(t,0,0.15), 0.3 - (t/0.15)*0.3, 0)'"
                else:
                    flash_effect = ""
                
                filter_complex.append(
                    f"[{broll_idx}:v]{cam_effect}"
                    f"crop={self.w}:{self.h},setsar=1,trim=0:{duration},setpts=PTS-STARTPTS{flash_effect}[b{broll_idx}];"
                )
                
                next_overlay = f"[ov{broll_idx}]"
                filter_complex.append(
                    f"{last_overlay}[b{broll_idx}]overlay=x=0:y=0:enable='between(t,{start_t},{end_t})'{next_overlay};"
                )
                last_overlay = next_overlay
                broll_idx += 1

        # Uso un path relativo per evitare problemi di spazi o escape strani di Windows
        rel_ass_path = "temp/subtitles.ass"
        filter_complex.append(f"{last_overlay}ass='{rel_ass_path}'[vfinal];")

        # --- MIXAGGIO AUDIO ---
        voice_idx = broll_idx if self.mode in ["A", "B"] else broll_idx
        inputs.extend(["-i", master_voice_path])
        current_audio_streams = [f"[{voice_idx}:a]"]
        next_idx = voice_idx + 1
        
        has_bgm = os.path.exists(bg_music_path)
        if has_bgm:
            inputs.extend(["-i", bg_music_path])
            filter_complex.append(f"[{next_idx}:a]volume=0.1,atrim=0:{total_duration}[bgm];")
            current_audio_streams.append("[bgm]")
            next_idx += 1
            
        # Aggiungiamo SFX se esistono per le scene
        import glob
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id")
            sfx_files = glob.glob(os.path.join(self.temp_path, f"scene_{scene_id}_sfx_*.wav"))
            if sfx_files:
                sfx_path = sfx_files[0]
                inputs.extend(["-i", sfx_path])
                start_t = cut_times[i]
                # Delay the SFX to match the scene start time
                filter_complex.append(f"[{next_idx}:a]adelay={int(start_t*1000)}|{int(start_t*1000)},volume=0.8[sfx{i}];")
                current_audio_streams.append(f"[sfx{i}]")
                next_idx += 1
                
        # Mix finale
        num_audio_streams = len(current_audio_streams)
        if num_audio_streams > 1:
            streams_str = "".join(current_audio_streams)
            filter_complex.append(f"{streams_str}amix=inputs={num_audio_streams}:duration=first:dropout_transition=3[afinal]")
        else:
            filter_complex.append(f"{current_audio_streams[0]}anull[afinal]")

        final_filter = "".join(filter_complex)
        output_file = os.path.join(self.output_path, f"final_video_{self.mode}.mp4")
        
        # Scrive il filtro in un file per aggirare WinError 206 (limite cmd Windows)
        filter_script_path = os.path.join(self.temp_path, "ffmpeg_filter.txt")
        with open(filter_script_path, "w", encoding="utf-8") as f:
            f.write(final_filter)
        
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        ffmpeg_exe = os.path.join(BASE_DIR, "venv", "Scripts", "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe): ffmpeg_exe = "ffmpeg" # Fallback globale
        
        cmd = [
            ffmpeg_exe, "-y",
            *inputs,
            "-filter_complex_script", filter_script_path,
            "-map", "[vfinal]",
            "-map", "[afinal]",
            "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-b:v", "0",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_file
        ]
        
        logger.info("Elaborazione Grafo FFmpeg in esecuzione...")
        subprocess.run(cmd, check=True)
        logger.info(f"✅ MONTAGGIO COMPLETATO. Output: {output_file}")
