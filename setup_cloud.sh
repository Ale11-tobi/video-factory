#!/bin/bash
# Script di installazione automatica per Lightning AI (Ubuntu/Debian)

echo "🚀 Inizio installazione dell'infrastruttura Video Factory su Lightning AI..."

# 1. Aggiornamento sistema e dipendenze base
sudo apt-get update
sudo apt-get install -y ffmpeg git wget curl python3-pip python3-venv

# 2. Creazione cartelle di lavoro
mkdir -p temp
mkdir -p outputs
mkdir -p models

# 3. Creazione ambiente virtuale (consigliato su cloud)
python3 -m venv venv
source venv/bin/activate

# 4. Installazione librerie Python
echo "📦 Installazione dipendenze Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Download pesi XTTSv2 (il motore scaricherà da solo al primo avvio)
# 6. Installazione SadTalker (verrà scaricato dinamicamente o gestito qui)
if [ ! -d "SadTalker" ]; then
    echo "🤖 Clonazione di SadTalker..."
    git clone https://github.com/OpenTalker/SadTalker.git
    cd SadTalker
    pip install -r requirements.txt
    
    # Download checkpionts SadTalker
    bash scripts/download_models.sh
    cd ..
fi

echo "✅ Installazione completata! Per avviare:"
echo "source venv/bin/activate && streamlit run app.py"
