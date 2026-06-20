import json
import os
import asyncio
import logging
import re
from typing import Dict, Any

# Dipendenze suggerite: groq, tenacity
from groq import AsyncGroq, RateLimitError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticDirector:
    """
    Modulo 1: Semantic Director.
    Si occupa di analizzare il testo in input e generare il director_cut.json 
    con gestione rigorosa del Rate Limiting (es. 30 req/min).
    """
    def __init__(self, api_key: str, smart_3d: bool = False):
        if not api_key:
            raise ValueError("API Key non fornita.")
        self.client = AsyncGroq(api_key=api_key)
        self.model_name = "llama-3.1-8b-instant"
        self.smart_3d = smart_3d

    def get_system_prompt(self) -> str:
        """Restituisce il prompt di sistema ingegnerizzato per l'LLM."""
        smart_3d_rule = ""
        if self.smart_3d:
            smart_3d_rule = "   -> REGOLA SMART 3D ATTIVA: Analizza lo script per soggetti complessi. Genera 'generative_3d_prompt' dettagliati per essi. Se il soggetto si ripete nel testo, RIUTILIZZA LA STESSA IDENTICA STRINGA DI PROMPT precedente in modo che il motore di rendering recuperi il video dalla cache. Tuttavia, assicurati che le scene 3D uguali NON siano mai adiacenti!"

        return f"""Sei il 'Semantic Director', un regista IA esperto di video short-form virali (TikTok, Reels, Shorts).
Il tuo obiettivo è smontare uno script testuale e convertirlo in una timeline JSON (director_cut.json) pronta per un'automazione video.

REGOLE TASSATIVE:
1. Ritmo Dinamico: Dividi il testo in scene brevi e d'impatto (massimo 1-2 frasi per scena).
2. Alternanza Visiva ("scene_type"): 
   - "avatar": Il presentatore IA parla in camera.
   - "b-roll": Voce fuori campo con clip di stock a copertura dell'intero schermo.
3. Ottimizzazione Query B-Roll: "broll_prompt" deve essere MASSIMO 1-2 parole in inglese (es. "money", "future", "nature"). DEVI VARIARE SEMPRE LA PAROLA per ogni scena b-roll, NON RIPETERE MAI LA STESSA PAROLA.
4. Generazione 3D Stile Geopop: "generative_3d_prompt" deve contenere una descrizione in inglese ESTREMAMENTE dettagliata per un generatore video AI 3D (es. "A photorealistic 3D render of a massive golden asteroid floating in deep space..."). Se la scena non necessita di 3D, restituisci null.
{smart_3d_rule}
5. PULIZIA TESTO VOCALE (CRITICA): Il campo "text_segment" è la sceneggiatura PURA.
   - NON SCRIVERE MAI NESSUNA INDICAZIONE DI REGIA NEL TEXT_SEGMENT.
   - Estrai SOLO la narrazione. Esempio: se lo script dice "VISUALE: Asteroide. Sapevi che...", in "text_segment" scrivi solo "Sapevi che...".
6. Audio Design: Usa "sfx_trigger" per inserire sound effect nei momenti chiave ("whoosh", "impact", "riser", "explosion", "magic", null).
7. Effetti Visivi: Usa "visual_effect" per suggerire zoom dinamici ("zoom_in_110", "slight_pan", null).

FORMATO DI RISPOSTA (ESCLUSIVAMENTE JSON VALIDO):
{
  "video_title": "Titolo ottimizzato per l'algoritmo",
  "scenes": [
    {
      "id": 1,
      "text_segment": "Il testo esatto che l'avatar/TTS pronuncerà in questa scena",
      "scene_type": "avatar" | "b-roll",
      "mood": "Intenzione emotiva (es. energetic, mysterious, serious)",
      "broll_prompt": "keyword1 keyword2" | null,
      "generative_3d_prompt": "Descrizione 3D dettagliata in inglese" | null,
      "sfx_trigger": "whoosh" | "impact" | "riser" | "explosion" | "magic" | null,
      "visual_effect": "zoom_in_110" | "camera_shake" | null
    }
  ]
}"""

    # Implementazione Smart del Rate Limiting (Gestione del limite 30 req/min)
    # Riprova in caso di quota esaurita (ResourceExhausted) con backoff esponenziale
    # Implementazione Smart del Rate Limiting
    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True
    )
    async def _call_llm_api(self, script_text: str) -> str:
        logger.info(f"Chiamata API Groq ({self.model_name}) in corso...")
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"SCRIPT INPUT:\n{script_text}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        content = response.choices[0].message.content
        
        # Pulizia robusta del JSON usando regex nel caso l'LLM aggiunga testo o markdown
        import re
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            content = match.group(0)
            
        # Rimuove le virgole finali ("trailing commas") che Llama 3 spesso genera per errore
        content = re.sub(r',\s*\}', '}', content)
        content = re.sub(r',\s*\]', ']', content)
            
        return content

    async def generate_director_cut(self, script_text: str, output_path: str = "temp/director_cut.json") -> Dict[str, Any]:
        """
        Esegue l'analisi semantica suddividendo il testo in chunk per rispettare i limiti TPM di Groq.
        """
        logger.info("Avvio analisi semantica dello script...")
        
        # Suddivisione in chunk da circa 1500 caratteri per evitare il limite di 6000 TPM
        chunk_size = 1500
        chunks = []
        words = script_text.split()
        current_chunk = []
        current_len = 0
        
        for word in words:
            current_chunk.append(word)
            current_len += len(word) + 1
            if current_len >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        all_scenes = []
        video_title = "Video Generato"
        
        try:
            for i, chunk in enumerate(chunks):
                logger.info(f"Elaborazione chunk {i+1}/{len(chunks)}...")
                response_json = await self._call_llm_api(chunk)
                
                try:
                    data = json.loads(response_json)
                    if "video_title" in data and i == 0:
                        video_title = data["video_title"]
                    if "scenes" in data:
                        all_scenes.extend(data["scenes"])
                except json.JSONDecodeError as e:
                    logger.error(f"Errore parsing JSON dal chunk {i+1}: {e}")
                    
                if i < len(chunks) - 1:
                    await asyncio.sleep(5)
                    
            for idx, scene in enumerate(all_scenes):
                scene["id"] = idx + 1
                
            director_cut = {
                "video_title": video_title,
                "scenes": all_scenes
            }
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(director_cut, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Director cut salvato in {output_path} con {len(all_scenes)} scene totali.")
            return director_cut
        except Exception as e:
            logger.error(f"Errore imprevisto nel Semantic Director: {e}")
            raise

# --- TEST LOCALE ---
if __name__ == "__main__":
    async def main():
        # Esempio di utilizzo (Richiede variabile d'ambiente GROQ_API_KEY)
        api_key = os.environ.get("GROQ_API_KEY", "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")
        director = SemanticDirector(api_key=api_key)
        
        script_di_prova = (
            "Sapevi che c'è un trucco psicologico che usano tutti i grandi brand? "
            "Si chiama scarsità indotta. Ti fanno credere che il prodotto stia finendo, "
            "e tu corri a comprarlo. Non farti più fregare."
        )
        
        try:
            result = await director.generate_director_cut(script_di_prova, output_path="temp/director_cut.json")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print("Esecuzione fallita:", e)

    asyncio.run(main())
