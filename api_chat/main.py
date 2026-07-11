import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
# Remplacement du SDK Google par le SDK officiel de Groq
from groq import Groq

app = FastAPI(title="IA Email Agent - Chat Interface")

# Initialisation dynamique du client Groq avec la clé du fichier .env
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)

# Configuration des templates HTML
templates = Jinja2Templates(directory="templates")

# 1. Structure stricte Pydantic pour les messages
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# 2. Route pour afficher l'interface Web
@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# 3. Route API dynamique pour envoyer une demande à l'IA (Groq)
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(payload: ChatMessage):
    try:
        # Configuration du Master Prompt
        master_prompt = (
            "Tu es l'assistant IA expert en gestion d'e-mails de l'entreprise. "
            "Réponds de manière concise, professionnelle et structure tes réponses. "
            f"Voici la demande de l'utilisateur : {payload.message}"
        )
        
        # Tâche 1 : Récupération dynamique du modèle depuis le .env (llama3-8b-8192 par défaut)
        current_model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
        
        # Appel à l'API Groq avec le modèle dynamique
        completion = client.chat.completions.create(
            model=current_model,
            messages=[{"role": "user", "content": master_prompt}]
        )
        
        return ChatResponse(response=completion.choices[0].message.content)
    except Exception as e:
        return ChatResponse(response=f"Erreur avec l'API : {str(e)}")