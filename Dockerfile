# Usa l'immagine di base di Python
FROM python:3.11.3

# Imposta la directory di lavoro

WORKDIR /app

# Copia i requisiti del progetto e installali
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice del progetto nella directory di lavoro
COPY db.sqlite3 /app/
COPY . /app/


RUN chmod 777 /app/db.sqlite3

# Avvia il server di sviluppo di Django
CMD python manage.py runserver
