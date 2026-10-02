#!/bin/sh
# Lance la démo ScolaPay sur ton ordinateur (Mac ou Linux) :
#     sh demarrer.sh
# Puis ouvre http://127.0.0.1:8000 dans le navigateur de CE MÊME ordinateur.
set -e
cd "$(dirname "$0")"

URL="http://127.0.0.1:8000/"
DEMO_PASSWORD="Demo-ScolaPay-2026"

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
    "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.10 (ou plus récent) est nécessaire : https://www.python.org/downloads/"
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Création de l'environnement Python..."
  "$PY" -m venv .venv
fi
echo "Installation des dépendances (la première fois : 1 à 2 minutes)..."
.venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt
[ -f .env ] || cp .env.example .env
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py demo --password "$DEMO_PASSWORD" --si-absente

echo ""
echo "  ScolaPay démarre : ouvre $URL dans ton navigateur."
echo "  Identifiant : directeur.demo  (ou caisse.demo)"
echo "  Mot de passe : $DEMO_PASSWORD"
echo "  Laisse cette fenêtre ouverte. Pour arrêter : Ctrl+C."
echo ""

# Ouvre le navigateur quelques secondes après le démarrage du serveur.
(sleep 3; open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || true) >/dev/null 2>&1 &

exec .venv/bin/python manage.py runserver 127.0.0.1:8000
