FROM python:3.10-slim

WORKDIR /app

# Copia solo il file delle librerie del sito (niente roba pesante di Kaggle)
COPY requirements_frontend.txt .
RUN pip install --no-cache-dir -r requirements_frontend.txt

# Copia il resto dei file
COPY . .

# Espone la porta usata da Hugging Face
EXPOSE 7860

# Lancia il sito
CMD ["streamlit", "run", "frontend_app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
