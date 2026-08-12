import logging
import traceback
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatSerializer
from .service import process_chat_logic
from .rag_retriever import get_emails_advanced_filter

# Initialisation du logger pour l'application
logger = logging.getLogger(__name__)

# Create your views here.
class ChatAPIView(APIView):
    def post(self, request):
        # Valide les données de la requête avec DRF
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            try:
                logger.info("Requête POST reçue et validée sur /api/chat/")
                # Appel de la logique métier (service.py) en passant tout validated_data 
                # (qui contient maintenant le prompt, l'historique et le model_name)
                result = process_chat_logic(serializer.validated_data)
                logger.info("Traitement de la requête terminé avec succès.")
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                # Journalisation de l'erreur critique et du traceback complet dans les logs/fichier
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
        # Récupération des query parameters (ex: ?name=...&date_from=...&date_to=...)
        name = request.GET.get('name', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)

        try:
            logger.info(f"Requête GET reçue pour le filtrage des emails (name={name}, date_from={date_from}, date_to={date_to})")
            
            # Appel de la fonction du Bloc 1
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