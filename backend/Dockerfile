FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Installer les packages Python
RUN pip install --no-cache-dir django djangorestframework psycopg2-binary

# Copier le code source
COPY . /app