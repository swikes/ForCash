#!/bin/sh
# Sauvegarde quotidienne de la base SQLite (à lancer par cron sur le serveur) :
#   0 2 * * * /chemin/vers/ForCash/deploy/sauvegarde.sh
# Garde 30 jours d'historique. Copiez aussi régulièrement le dossier backups/
# hors du serveur (Google Drive, autre serveur…) : une sauvegarde sur la même
# machine ne protège pas d'une panne de disque.
set -eu
cd "$(dirname "$0")/.."
mkdir -p backups
STAMP=$(date +%Y-%m-%d)
docker compose exec -T app python -c "import sqlite3; src = sqlite3.connect('/app/data/db.sqlite3'); dst = sqlite3.connect('/app/data/backup.sqlite3'); src.backup(dst); dst.close(); src.close()"
mv data/backup.sqlite3 "backups/scolapay-$STAMP.sqlite3"
gzip -f "backups/scolapay-$STAMP.sqlite3"
find backups -name 'scolapay-*.sqlite3.gz' -mtime +30 -delete
echo "Sauvegarde OK : backups/scolapay-$STAMP.sqlite3.gz"
