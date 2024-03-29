#!/bin/sh

python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic --noinput
gunicorn PPM_Project.wsgi:application --bind=0.0.0.0:$PORT --timeout 300 --workers 4