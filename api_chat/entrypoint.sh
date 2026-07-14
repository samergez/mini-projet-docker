#!/bin/sh

# 1. Installer les dépendances Python nécessaires
echo "📦 Installation des dépendances du Backend..."
pip install --default-timeout=1000 fastapi uvicorn jinja2 groq psycopg2-binary

# 2. Lancer la boucle d'envoi automatique toutes les 20 secondes en tâche de fond
echo "⏰ Démarrage du planificateur d'envoi (toutes les 20 secondes)..."
(
  while true; do
    # L'option -u force Python à écrire ses logs en temps réel sans mise en cache
    /usr/local/bin/python -u /app/send_emails_dataset.py >> /var/log/cron.log 2>&1
    sleep 20
  done
) &

# 3. Lancer l'API principale (FastAPI) au premier plan
echo "🚀 Démarrage de l'API de Chat..."
exec uvicorn main:app --host 0.0.0.0 --port 8000