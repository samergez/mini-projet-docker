FROM python:3.10-slim


RUN pip install fastapi uvicorn jinja2 groq pydantic

WORKDIR /app

COPY . .

CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]