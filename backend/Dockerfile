FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système nécessaires (gcc, libpq-dev pour PostgreSQL et cron)
RUN apt-get update && apt-get install -y gcc libpq-dev cron && rm -rf /var/lib/apt/lists/*

# Installer tous les packages Python nécessaires en une seule fois
RUN pip install --no-cache-dir django djangorestframework psycopg2-binary requests pydantic groq pypdf

# Copier le code source
COPY . /app

# Rendre le script d'entrée exécutable
RUN chmod +x /app/entrypoint.sh

# Définir l'entrypoint pour lancer le script de démarrage
ENTRYPOINT ["sh", "/app/entrypoint.sh"]