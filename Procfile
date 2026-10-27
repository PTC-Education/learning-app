release: python manage.py migrate
web: gunicorn mysite.wsgi --worker-class gthread --threads 4 --workers 1 --max-requests 1000 --max-requests-jitter 50
worker: python manage.py rqworker high default low
