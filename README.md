# medical-records-ui

python manage.py runserver
gunicorn medicalrecords.wsgi:application --bind 0.0.0.0:8000