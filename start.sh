#!/bin/sh

python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic --noinput
/usr/local/lib/python3.9/site-packages/gunicorn-20.1.0.dist-info/METADATA/gunicorn PPM_Project.wsgi:application --bind=0.0.0.0:$PORT