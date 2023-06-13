# Specifica la base image
FROM python:3.11.3

# Copia i file del progetto nella directory /app
COPY . /app

# Imposta la directory di lavoro
WORKDIR /app

# Crea un ambiente virtuale
RUN python -m venv venv

# Attiva l'ambiente virtuale
RUN . venv/bin/activate

# Aggiorna pip all'interno dell'ambiente virtuale
RUN pip install --upgrade pip

# Installa le dipendenze del progetto dal file requirements.txt
RUN pip install -r requirements.txt

# Esponi la porta
EXPOSE 8000

# Avvia il server di sviluppo di Django all'interno dell'ambiente virtuale
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
