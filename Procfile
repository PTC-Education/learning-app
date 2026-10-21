release: python manage.py migrate
web: gunicorn mysite.wsgi --worker-class gthread --threads 4
worker: python manage.py rqworker high default low
