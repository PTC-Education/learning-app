release: python manage.py migrate
web: gunicorn mysite.wsgi --workers 1 --threads 8 --max-requests 1000 --max-requests-jitter 50 --timeout 30
worker: python manage.py rqworker high default low
