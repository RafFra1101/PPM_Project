# Usa un'immagine di base di Python
FROM python:3.9

# Imposta la directory di lavoro nell'immagine Docker
WORKDIR /app

# Copia il codice del progetto nella directory di lavoro dell'immagine Docker
COPY . .

# Installa le dipendenze del progetto
RUN pip install --no-cache-dir -r requirements.txt


ENTRYPOINT [ "sh", "./start.sh" ]

