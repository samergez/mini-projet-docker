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
    search_emails_by_subject,
    get_emails_advanced_filter
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
    "get_emails_advanced_filter": get_emails_advanced_filter,
}

def run_chat_agent(user_query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    logger.info(f"🔍 1. Initialisation de la requête pour : '{user_query}'")
    
    if not groq_client:
        raise ValueError("Clé GROQ_API_KEY absente.")
        
    current_model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
    history = history or []
    
    # 🚀 TRONCATURE DE L'HISTORIQUE : On garde uniquement les 4 derniers messages
    trimmed_history = history[-4:] if len(history) > 4 else history
    
    try:
        system_instructions = (
            "Tu es un assistant IA expert en recherche d'e-mails et analyse RAG.\n"
            "RÈGLES STRICTES DE FONCTIONNEMENT :\n"
            "1. L'outil 'get_email_by_id' ne doit être utilisé QUE si l'utilisateur fournit un identifiant numérique exact (ex: un nombre comme 711).\n"
            "2. Si l'utilisateur cherche un e-mail ou demande son ID à partir d'un nom de projet, d'un sujet ou d'un intitulé (ex: 'Sprint S29', 'Facture'), tu dois utiliser les outils de recherche textuelle (`search_emails_by_subject` ou `get_emails_advanced_filter`), jamais `get_email_by_id` directement.\n"
            "3. N'utilise jamais l'outil 'search_emails_by_person' avec des termes vagues comme 'personne'.\n"
            "4. INTERDICTION absolue d'afficher des balises techniques comme <function=...> dans tes réponses.\n"
            "5. Si un outil ne renvoie rien, réponds simplement qu'aucun e-mail n'a été trouvé."
        )

        messages = [{"role": "system", "content": system_instructions}]

        for msg in trimmed_history:
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

        # Si le modèle décide d'appeler des outils
        if response_message.tool_calls:
            logger.info("🛠️ 3. L'agent a décidé d'utiliser un Tool !")
            
            # On ajoute la réponse initiale de l'assistant (qui contient les tool_calls) dans la conversation
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                raw_args = tool_call.function.arguments
                function_args = json.loads(raw_args) if raw_args else {}
                
                logger.info(f"⚙️ Exécution du Tool '{function_name}' avec les arguments : {function_args}")

                if function_name in AVAILABLE_TOOLS:
                    function_to_call = AVAILABLE_TOOLS[function_name]
                    tool_output = function_to_call(**function_args)
                    
                    # Troncature optionnelle si le texte est trop long
                    tool_output_str = json.dumps(tool_output, ensure_ascii=False)
                    if len(tool_output_str) > 2000:
                        tool_output_str = tool_output_str[:2000] + "... [Texte tronqué]"
                else:
                    logger.error(f"Tool '{function_name}' non implémenté")
                    tool_output_str = json.dumps({"error": "outil indisponible"}, ensure_ascii=False)

                # Ajout du résultat de l'outil avec le rôle 'tool' requis par l'API
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output_str,
                })

            logger.info("🤖 4. Génération de la réponse finale par Groq avec les résultats des outils...")
            
            # 🚀 Ajout d'une consigne de sécurité anti-bafouillage
            messages.append({
                "role": "system", 
                "content": (
                    "RÈGLE ABSOLUE : Tu dois rédiger un résumé clair, en français, des e-mails fournis ci-dessus ou donner l'information demandée (comme les ID trouvés). "
                    "INTERDICTION formelle d'afficher des balises techniques comme <function=...> ou du code JSON brut. "
                    "Fais des phrases complètes pour l'utilisateur."
                )
            })

            second_response = groq_client.chat.completions.create(
                model=current_model,
                messages=messages,
                temperature=0.1  # 🌡️ On baisse la température pour forcer le déterminisme et la stabilité !
            )
            return second_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        error_msg = log_exception_with_traceback(e, f"Erreur sur la requête : '{user_query}'")
        return "Désolé, une erreur s'est produite lors du traitement."