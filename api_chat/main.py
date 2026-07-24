import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# On importe notre fonction RAG centralisée et le logger
from chat_agent import run_chat_agent
from logger_config import logger, log_exception_with_traceback

app = FastAPI(title="IA Email Agent - Chat Interface")
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
    logger.info(f"📥 Reçu depuis l'interface graphique : '{payload.message}'")
    
    try:
        # On passe la main au moteur de chat RAG
        ai_response = run_chat_agent(payload.message)
        logger.info("📤 Réponse renvoyée avec succès à l'interface HTML.")
        return ChatResponse(response=ai_response)
        
    except Exception as e:
        # Si un plantage imprévu arrive ici, le trustbag s'active
        log_exception_with_traceback(e, f"Erreur critique dans le point d'accès API pour : '{payload.message}'")
        return ChatResponse(response="Une erreur interne est survenue. Consultez reception.log pour le rapport complet.")