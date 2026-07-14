import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="IA Email Agent - Chat Interface")


GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)


templates = Jinja2Templates(directory="templates")

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str


@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(payload: ChatMessage):
    try:
        master_prompt = (
            "Tu es l'assistant IA expert en gestion d'e-mails de l'entreprise. "
            "Réponds de manière concise, professionnelle et structure tes réponses. "
            f"Voici la demande de l'utilisateur : {payload.message}"
        )
        current_model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
        completion = client.chat.completions.create(
            model=current_model,
            messages=[{"role": "user", "content": master_prompt}]
        )
        
        return ChatResponse(response=completion.choices[0].message.content)
    except Exception as e:
        return ChatResponse(response=f"Erreur avec l'API : {str(e)}")