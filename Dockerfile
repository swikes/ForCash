FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_DEBUG=1 python manage.py collectstatic --noinput

# Migrations à chaque démarrage (sans effet si déjà faites), puis gunicorn.
# Si SCOLAPAY_DEMO_PASSWORD est défini, l'école de démo est créée au besoin.
CMD ["sh", "deploy/entrypoint.sh"]
