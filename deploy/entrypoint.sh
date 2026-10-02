#!/bin/sh
# Démarrage du conteneur : migrations, école de démo (si demandée), serveur web.
set -e
python manage.py migrate --noinput
if [ -n "${SCOLAPAY_DEMO_PASSWORD:-}" ]; then
  python manage.py demo --password "$SCOLAPAY_DEMO_PASSWORD" --si-absente
fi
exec gunicorn scolapay.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 60
