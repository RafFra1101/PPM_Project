# Usa un'immagine di base di Python
FROM python:3.9

# Imposta la directory di lavoro nell'immagine Docker
WORKDIR /app

# Copia il codice del progetto nella directory di lavoro dell'immagine Docker
COPY . /app

# Installa le dipendenze del progetto
RUN pip install --no-cache-dir -r requirements.txt

RUN curl -sSL https://github.com/docker/compose/releases/download/3.9/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
RUN chmod +x /usr/local/bin/docker-compose

COPY docker-compose.yml /app/docker-compose.yml


# Esegui le migrazioni del database
RUN python manage.py makemigrations
RUN python manage.py migrate

# Esporri la porta del server web (modifica il numero di porta se necessario)
EXPOSE 8000

# Avvia il server web
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
