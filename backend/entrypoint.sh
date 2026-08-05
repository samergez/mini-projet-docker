#!/bin/sh

# 1. Créer les dossiers nécessaires s'ils n'existent pas
mkdir -p /app/logs
touch /app/logs/envoi.log
touch /app/logs/reception.log

# 2. Installer Cron (Système) et attendre que ce soit fini
echo "📦 Installation de Cron dans le conteneur..."
apt-get update && apt-get install -y cron

# 3. Installer les dépendances Python obligatoires (Mise à jour pour Django et requirements.txt)
echo "🐍 Installation des dépendances Python..."
if [ -f "requirements.txt" ]; then
    pip install --default-timeout=1000 -r requirements.txt
else
    pip install --default-timeout=1000 django djangorestframework psycopg2-binary groq requests pypdf uvicorn
fi

# 4. Appliquer les migrations de la base de données Django
echo "🗄️ Application des migrations Django..."
python3 manage.py makemigrations
python3 manage.py migrate

# 5. Exporter les variables d'environnement pour Cron
printenv | grep -v "no_proxy" >> /etc/environment

# 6. Configurer les DEUX tâches Cron en parallèle
echo "⏰ Configuration des services Cron..."
# Tâche 1 : Envoi d'un mail toutes les 5 minutes
echo "*/5 * * * * /usr/local/bin/python3 /app/send_emails_dataset.py >> /app/logs/envoi.log 2>&1" > /etc/cron.d/mail-cron

# Tâche 2 : Extraction (Bloc 2) PUIS Vectorisation (Bloc 4) chaînées l'une après l'autre
echo "*/5 * * * * sleep 30 && /usr/local/bin/python3 /app/fetch_emails.py >> /app/logs/reception.log 2>&1 && /usr/local/bin/python3 /app/vectorize_emails.py >> /app/logs/reception.log 2>&1" >> /etc/cron.d/mail-cron

chmod 0644 /etc/cron.d/mail-cron
crontab /etc/cron.d/mail-cron

# 7. Démarrer le service cron en arrière-plan
cron

# 8. Lancer le serveur Django au premier plan (remplace Uvicorn/FastAPI)
echo "🚀 Démarrage du serveur Django (Gunicorn / Runserver)..."
exec python3 manage.py runserver 0.0.0.0:8000