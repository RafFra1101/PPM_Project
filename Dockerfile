# Specifica l'immagine di base
FROM python:3.11.3

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file requirements.txt e il progetto Django
COPY requirements.txt .
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta su cui sarà in ascolto l'applicazione
EXPOSE 8000

# Comando per eseguire l'applicazione
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
