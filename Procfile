web: 
  python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn PPM_Project.wsgi --log-file -

db:
  sqlite3 db.sqlite3