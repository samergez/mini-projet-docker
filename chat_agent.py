import os
import json
from typing import List
from groq import Groq
from rag_retriever import (
    retrieve_relevant_emails, 
    DocumentChunk,
    TOOLS_SCHEMA,
    search_emails_by_date,
    search_emails_by_person,
    get_email_attachments
)
from logger_config import logger, log_exception_with_traceback

GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

AVAILABLE_TOOLS = {
    "search_emails_by_date": search_emails_by_date,
    "search_emails_by_person": search_emails_by_person,
    "get_email_attachments": get_email_attachments,
}

def run_chat_agent(user_query: str) -> str:
    logger.info(f"🔍 1. Initialisation de la requête pour : '{user_query}'")
    
    if not groq_client:
        raise ValueError("Clé GROQ_API_KEY absente.")
        
    current_model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
    
    try:
        system_instructions = (
            "Tu es un assistant IA expert en recherche d'e-mails.\n"
            "RÈGLES D'UTILISATION DES OUTILS :\n"
            "1. Si la question demande combien d'e-mails contiennent une pièce jointe ou un PDF, appelle 'get_email_attachments' avec file_extension='pdf' et email_id=null.\n"
            "2. Ne mentionne jamais d'erreur technique dans ta réponse."
        )

        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_query}
        ]

        logger.info("🤖 2. Envoi de la requête à Groq (avec support des Tools)...")
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

            logger.info("🤖 4. Génération de la réponse finale par Groq...")
            clean_messages = [
                {
                    "role": "system", 
                    "content": "Tu réponds à l'utilisateur de manière concise en affirmant le résultat exact fourni par la base de données. Ne doute pas des chiffres reçus."
                },
                {
                    "role": "user", 
                    "content": f"Résultat SQL de la base de données : {tool_outputs_summary}\n\nQuestion posée : {user_query}"
                }
            ]

            second_response = groq_client.chat.completions.create(
                model=current_model,
                messages=clean_messages
            )
            return second_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        error_msg = log_exception_with_traceback(e, f"Erreur sur la requête : '{user_query}'")
        return "Désolé, une erreur s'est produite lors du traitement."


if __name__ == "__main__":
    logger.info("⚡ DÉMARRAGE DU TEST DES TOOLS EN LIGNE DE COMMANDE ⚡")
    question = "combien d'emails contiennent un fichier attaché pdf ?"
    reponse = run_chat_agent(question)
    print(f"\n💡 RÉPONSE DE L'AGENT :\n{reponse}\n")