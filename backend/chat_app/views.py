import logging
import traceback
import json
import re
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatSerializer
from .service import process_chat_logic
from .rag_retriever import get_emails_advanced_filter

# Initialisation du logger pour l'application
logger = logging.getLogger(__name__)

def extract_json_from_response(raw_response):
    """
    Extrait et nettoie un objet JSON depuis une réponse brute d'un LLM,
    même si elle contient du texte autour ou des balises markdown.
    """
    if not raw_response or not isinstance(raw_response, str):
        return {}
    
    # Tentative 1 : Parsing direct si la chaîne est déjà un JSON valide
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass

    # Tentative 2 : Nettoyage des balises markdown courantes (```json ... ```)
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Tentative 3 : Recherche par expression régulière du premier '{' au dernier '}'
    match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError(f"Impossible d'extraire un JSON valide de la réponse : {raw_response}", raw_response, 0)


# Create your views here.
class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            try:
                logger.info("Requête POST reçue et validée sur /api/chat/")
                result = process_chat_logic(serializer.validated_data)
                logger.info("Traitement de la requête terminé avec succès.")
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Erreur critique lors du traitement du chat : {str(e)}")
                logger.error(traceback.format_exc())
                return Response(
                    {"status": "error", "message": "Une erreur interne est survenue sur le serveur."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.warning(f"Échec de validation des données reçues : {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailAdvancedFilterAPIView(APIView):
    def get(self, request):
        name = request.GET.get('name', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)

        try:
            logger.info(f"Requête GET reçue pour le filtrage des emails (name={name}, date_from={date_from}, date_to={date_to})")
            results = get_emails_advanced_filter(name=name, date_from=date_from, date_to=date_to)
            
            logger.info(f"Filtrage réussi : {len(results)} e-mails trouvés.")
            return Response({
                "status": "success",
                "count": len(results),
                "data": results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du filtrage des e-mails : {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExtractProjectsJSONAPIView(APIView):
    def post(self, request):
        model_name = request.data.get('model_name', 'llama-3.1-8b-instant')
        
        try:
            emails = get_emails_advanced_filter()
            emails_text = json.dumps(emails, ensure_ascii=False)[:15000]

            prompt = (
                f"Voici la liste des e-mails disponibles sous format JSON :\n{emails_text}\n\n"
                "Analyse ces e-mails et extrait la liste des projets mentionnés. "
                "Tu dois impérativement répondre **uniquement** sous la forme d'un objet JSON valide, sans texte autour, sans markdown (pas de ```json), respectant cette structure exacte :\n"
                "{\n"
                "  \"projects\": [\n"
                "    {\n"
                "      \"name\": \"Nom du projet\",\n"
                "      \"email_ids\": [326, 327],\n"
                "      \"description\": \"Courte description\"\n"
                "    }\n"
                "  ]\n"
                "}"
            )

            logger.info(f"Requête reçue pour l'extraction des projets en JSON avec le modèle : {model_name}")
            service_payload = {
                "prompt": prompt,
                "history": [],
                "model_name": model_name
            }
            service_result = process_chat_logic(service_payload)
            raw_response = service_result.get("response", "{}")
            
            logger.info(f"Réponse brute reçue de l'agent (Projets) : {repr(raw_response)}")
            parsed_json = extract_json_from_response(raw_response)
            
            return Response({"status": "success", "data": parsed_json}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction JSON des projets : {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExtractClientsJSONAPIView(APIView):
    def post(self, request):
        model_name = request.data.get('model_name', 'llama-3.1-8b-instant')
        
        try:
            emails = get_emails_advanced_filter()
            emails_text = json.dumps(emails, ensure_ascii=False)[:15000]

            prompt = (
                f"Voici la liste des e-mails disponibles sous format JSON :\n{emails_text}\n\n"
                "Analyse ces e-mails et extrait la liste des clients mentionnés. "
                "Tu dois impérativement répondre **uniquement** sous la forme d'un objet JSON valide, sans texte autour, sans markdown (pas de ```json), respectant cette structure exacte :\n"
                "{\n"
                "  \"clients\": [\n"
                "    {\n"
                "      \"name\": \"Nom du client\",\n"
                "      \"email_ids\": [246, 354],\n"
                "      \"description\": \"Courte description ou secteur\"\n"
                "    }\n"
                "  ]\n"
                "}"
            )

            logger.info(f"Requête reçue pour l'extraction des clients en JSON avec le modèle : {model_name}")
            service_payload = {
                "prompt": prompt,
                "history": [],
                "model_name": model_name
            }
            service_result = process_chat_logic(service_payload)
            raw_response = service_result.get("response", "{}")
            
            logger.info(f"Réponse brute reçue de l'agent (Clients) : {repr(raw_response)}")
            parsed_json = extract_json_from_response(raw_response)
            
            return Response({"status": "success", "data": parsed_json}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction JSON des clients : {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )