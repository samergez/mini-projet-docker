import json
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# "Base de données" temporaire en mémoire pour le test
TASKS_LIST = [
    {"id": 1, "text": "Valider l'architecture Docker Compose"},
    {"id": 2, "text": "Connecter Django et React"}
]

@csrf_exempt
def api_todos(request):
    global TASKS_LIST
    if request.method == 'GET':
        return JsonResponse({"message": "API Django connectée avec succès !", "tasks": TASKS_LIST})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_text = data.get('text')
            if new_text:
                new_task = {"id": len(TASKS_LIST) + 1, "text": new_text}
                TASKS_LIST.append(new_task)
                return JsonResponse({"status": "success", "task": new_task}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

urlpatterns = [
    path('api/todos/', api_todos),
]