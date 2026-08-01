import logging
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .chat_agent import run_chat_agent

# Initialisation du logger
logger = logging.getLogger(__name__)

class ChatInputPayload(BaseModel):
    prompt: str = Field(..., min_length=1)
    metadata_filters: Optional[Dict[str, Any]] = None

def process_chat_logic(data: dict) -> dict:
    """
    Logique métier connectée au Chat Agent RAG.
    """
    logger.info("Début du traitement de la requête de chat avec l'Agent IA...")
    
    # 1. Validation avec Pydantic
    validated_data = ChatInputPayload(**data)
    
    user_prompt = validated_data.prompt
    metadata = validated_data.metadata_filters or {}
    
    logger.info(f"Prompt validé avec succès : '{user_prompt}' avec métadonnées : {metadata}")
    
    # 2. Appel de ton Chat Agent (Groq + RAG + Tools)
    ai_response = run_chat_agent(user_query=user_prompt)
    
    logger.info("Traitement par l'Agent IA terminé avec succès.")
    
    return {
        "status": "success",
        "prompt": user_prompt,
        "response": ai_response,
        "metadata_used": metadata
    }