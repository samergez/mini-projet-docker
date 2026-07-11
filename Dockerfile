FROM python:3.10-slim

# On installe les dépendances nécessaires à ton API, y compris groq
RUN pip install fastapi uvicorn jinja2 groq pydantic

WORKDIR /app

# On copie tout le contenu du dossier (dont main.py)
COPY . .

CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]