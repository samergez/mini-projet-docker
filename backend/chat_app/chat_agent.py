import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

from .rag_retriever import (
    retrieve_relevant_emails, 
    DocumentChunk,
    TOOLS_SCHEMA,
    search_emails_by_date,
    search_emails_between_dates,
    search_emails_by_person,
    get_email_attachments,
    get_email_by_id,
    search_emails_by_subject,
    get_emails_advanced_filter
)

logger = logging.getLogger(__name__)

def log_exception_with_traceback(e, message):
    logger.error(f"{message} : {e}", exc_info=True)
    return str(e)

# Initialisation des clés et clients
GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

GLM_KEY = os.getenv("GLM_API_KEY")
glm_client = ZhipuAI(api_key=GLM_KEY) if (GLM_KEY and ZhipuAI) else None

AVAILABLE_TOOLS = {
    "search_emails_by_date": search_emails_by_date,
    "search_emails_between_dates": search_emails_between_dates,
    "search_emails_by_person": search_emails_by_person,
    "get_email_attachments": get_email_attachments,
    "get_email_by_id": get_email_by_id,
    "search_emails_by_subject": search_emails_by_subject,
    "get_emails_advanced_filter": get_emails_advanced_filter,
}

def run_chat_agent(user_query: str, history: Optional[List[Dict[str, str]]] = None, model_name: Optional[str] = None) -> str:
    target_model = model_name or os.getenv("AI_MODEL", "llama-3.1-8b-instant")
    logger.info(f"🔍 1. Initialisation de la requête pour : '{user_query}' avec le modèle : '{target_model}'")
    
    history = history or []
    trimmed_history = history[-4:] if len(history) > 4 else history
    
    try:
        system_instructions = (
            "Tu es un assistant IA expert en recherche d'e-mails.\n"
            "RÈGLES STRICTES :\n"
            "1. Pour toute recherche par sujet, titre ou projet (ex: 'Sprint S29'), tu dois UTILISER UNIQUEMENT l'outil 'search_emails_by_subject'. N'utilise jamais plusieurs outils en même temps.\n"
            "2. L'outil 'get_email_by_id' s'utilise uniquement avec un nombre.\n"
            "3. INTERDICTION FORMELLE d'écrire des balises comme <function=...> dans le texte de ta réponse.\n"
            "4. Si tu trouves plusieurs e-mails, liste simplement leurs IDs clairement."
        )

        messages = [{"role": "system", "content": system_instructions}]

        for msg in trimmed_history:
            role = "assistant" if msg.get("sender") == "bot" else "user"
            messages.append({"role": role, "content": msg.get("text", "")})

        messages.append({"role": "user", "content": user_query})

        is_glm = "glm" in target_model.lower()

        if is_glm:
            if not glm_client:
                raise ValueError("Client GLM non initialisé ou package zhipuai manquant.")
            logger.info("🤖 2. Envoi de la requête à GLM...")
            
            formatted_tools = [
                {"type": "function", "function": t} if "function" not in t else t 
                for t in TOOLS_SCHEMA
            ] if TOOLS_SCHEMA else None

            create_kwargs = {
                "model": target_model,
                "messages": messages,
            }
            if formatted_tools:
                create_kwargs["tools"] = formatted_tools
                create_kwargs["tool_choice"] = "auto"

            response = glm_client.chat.completions.create(**create_kwargs)
        else:
            if not groq_client:
                raise ValueError("Clé GROQ_API_KEY absente.")
            logger.info("🤖 2. Envoi de la requête à Groq...")
            response = groq_client.chat.completions.create(
                model=target_model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )

        response_message = response.choices[0].message

        # Gestion des outils (Tool Calls)
        if getattr(response_message, "tool_calls", None):
            logger.info("🛠️ 3. L'agent a décidé d'utiliser un Tool !")
            
            # Conversion propre de l'objet Pydantic en dictionnaire pour Zhipu
            if hasattr(response_message, "model_dump"):
                messages.append(response_message.model_dump())
            else:
                messages.append(response_message)

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                raw_args = tool_call.function.arguments
                function_args = json.loads(raw_args) if raw_args else {}
                
                logger.info(f"⚙️ Exécution du Tool '{function_name}' avec les arguments : {function_args}")

                if function_name in AVAILABLE_TOOLS:
                    function_to_call = AVAILABLE_TOOLS[function_name]
                    tool_output = function_to_call(**function_args)
                    tool_output_str = json.dumps(tool_output, ensure_ascii=False)
                    if len(tool_output_str) > 2000:
                        tool_output_str = tool_output_str[:2000] + "... [Texte tronqué]"
                else:
                    logger.error(f"Tool '{function_name}' non implémenté")
                    tool_output_str = json.dumps({"error": "outil indisponible"}, ensure_ascii=False)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output_str,
                })

            logger.info("🤖 4. Génération de la réponse finale avec les résultats des outils...")
            messages.append({
                "role": "system", 
                "content": "RÈGLE ABSOLUE : Rédige un résumé clair ou donne les ID demandés en français. Interdiction d'afficher des balises <function=...>."
            })

            if is_glm:
                second_response = glm_client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=0.1
                )
            else:
                second_response = groq_client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=0.1
                )
            return second_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        error_msg = log_exception_with_traceback(e, f"Erreur sur la requête : '{user_query}'")
        return "Désolé, une erreur s'est produite lors du traitement."