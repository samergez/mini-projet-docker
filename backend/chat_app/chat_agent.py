import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
from .rag_retriever import (
    retrieve_relevant_emails, 
    DocumentChunk,
    TOOLS_SCHEMA,
    search_emails_by_date,
    search_emails_between_dates,
    search_emails_by_person,
    get_email_attachments,
    get_email_by_id,
    search_emails_by_subject
)

logger = logging.getLogger(__name__)

def log_exception_with_traceback(e, message):
    logger.error(f"{message} : {e}", exc_info=True)
    return str(e)

GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

AVAILABLE_TOOLS = {
    "search_emails_by_date": search_emails_by_date,
    "search_emails_between_dates": search_emails_between_dates,
    "search_emails_by_person": search_emails_by_person,
    "get_email_attachments": get_email_attachments,
    "get_email_by_id": get_email_by_id,
    "search_emails_by_subject": search_emails_by_subject,
}

def run_chat_agent(user_query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    logger.info(f"🔍 1. Initialisation de la requête pour : '{user_query}'")
    
    if not groq_client:
        raise ValueError("Clé GROQ_API_KEY absente.")
        
    current_model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
    history = history or []
    
    try:
        system_instructions = (
            "Tu es un assistant IA expert en recherche d'e-mails et analyse RAG.\n"
            "RÈGLES STRICTES DE FONCTIONNEMENT :\n"
            "1. À CHAQUE FOIS que l'utilisateur pose une question sur des e-mails (recherche par mot-clé, par sujet, par personne, par date ou par intervalle de dates), TU DOIS IMPÉRATIVEMENT appeler l'outil correspondant. Ne réponds jamais de mémoire.\n"
            "2. Si l'utilisateur mentionne un mot-clé comme 'Urgent' ou 'Facture', utilise immédiatement l'outil 'search_emails_by_subject'.\n"
            "3. Ne donne JAMAIS de conseils de programmation, de code Python ou de requêtes SQL à l'utilisateur.\n"
            "4. Si l'outil retourne des résultats vides, indique simplement et sobrement à l'utilisateur qu'aucun e-mail n'a été trouvé pour cette période, sans inventer de prétexte.\n"
            "5. Ne mentionne jamais d'erreur technique dans ta réponse."
        )

        messages = [{"role": "system", "content": system_instructions}]

        for msg in history[:-1]:
            role = "assistant" if msg.get("sender") == "bot" else "user"
            messages.append({"role": role, "content": msg.get("text", "")})

        messages.append({"role": "user", "content": user_query})

        logger.info("🤖 2. Envoi de la requête à Groq (avec support des Tools et Historique)...")
        response = groq_client.chat.completions.create(
            model=current_model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            logger.info("🛠️ 3. L'agent a décidé d'utiliser un Tool !")
            tool_outputs_summary = []

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                raw_args = tool_call.function.arguments
                function_args = json.loads(raw_args) if raw_args else {}
                
                logger.info(f"⚙️ Exécution du Tool '{function_name}' avec les arguments : {function_args}")

                if function_name in AVAILABLE_TOOLS:
                    function_to_call = AVAILABLE_TOOLS[function_name]
                    tool_output = function_to_call(**function_args)
                    tool_outputs_summary.append(json.dumps(tool_output, ensure_ascii=False))

            logger.info("🤖 4. Génération de la réponse finale par Groq avec le contexte...")
            
            clean_messages = [
                {
                    "role": "system", 
                    "content": (
                        "Tu réponds à l'utilisateur de manière claire et structurée en te basant STRICTEMENT sur les résultats de la base de données fournis. "
                        "INTERDICTION absolue de générer du code (Python, SQL, etc.) ou de donner des conseils techniques. "
                        "Si les résultats sont vides, dis simplement qu'aucun e-mail n'a été trouvé."
                    )
                }
            ]
            
            for msg in history[:-1]:
                role = "assistant" if msg.get("sender") == "bot" else "user"
                clean_messages.append({"role": role, "content": msg.get("text", "")})

            clean_messages.append({
                "role": "user", 
                "content": f"Résultat de la base de données : {tool_outputs_summary}\n\nQuestion posée : {user_query}"
            })

            second_response = groq_client.chat.completions.create(
                model=current_model,
                messages=clean_messages
            )
            return second_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        error_msg = log_exception_with_traceback(e, f"Erreur sur la requête : '{user_query}'")
        return "Désolé, une erreur s'est produite lors du traitement."