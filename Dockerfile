FROM python:3.10

# Hugging Face richiede che il server giri come utente 1000 per poter salvare i file (config.json, history.json)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

# Copia solo il file delle librerie del sito
COPY --chown=user requirements_frontend.txt .
RUN pip install --no-cache-dir -r requirements_frontend.txt

# Copia tutto il codice dando i permessi all'utente
COPY --chown=user . .

EXPOSE 7860

CMD ["streamlit", "run", "frontend_app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
