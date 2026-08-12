import logging
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from .chat_agent import run_chat_agent

# Initialisation du logger
logger = logging.getLogger(__name__)

class ChatInputPayload(BaseModel):
    prompt: str = Field(..., min_length=1)
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Historique des messages de la conversation")
    metadata_filters: Optional[Dict[str, Any]] = None

def process_chat_logic(data: dict) -> dict:
    """
    Logique métier connectée au Chat Agent RAG.
    """
    logger.info("Début du traitement de la requête de chat avec l'Agent IA...")
    
    # 1. Validation avec Pydantic
    validated_data = ChatInputPayload(**data)
    
    user_prompt = validated_data.prompt
    chat_history = validated_data.history or []
    metadata = validated_data.metadata_filters or {}
    
    logger.info(f"Prompt validé avec succès : '{user_prompt}' avec historique de {len(chat_history)} messages.")
    logger.info(f"xxxxxxxxxxxxxxx'{chat_history}'")
    
    # 2. Appel de ton Chat Agent en lui passant l'historique
    ai_response = run_chat_agent(user_query=user_prompt, history=chat_history)
    
    logger.info("Traitement par l'Agent IA terminé avec succès.")
    
    return {
        "status": "success",
        "prompt": user_prompt,
        "response": ai_response,
        "metadata_used": metadata
    }