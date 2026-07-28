import json
import os
import jwt
from datetime import datetime, timedelta
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

SECRET_KEY = "cle-secrete-super-secure-pour-demo"

TASKS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'todos.json')
USERS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'users.json')

def load_json(path, default_data):
    if not os.path.exists(path):
        save_json(path, default_data)
        return default_data
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default_data

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_current_user_id(request):
    """Extrait l'ID de l'utilisateur depuis le cookie JWT"""
    token = request.COOKIES.get('jwt_token')
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256", "HS405"])
        return payload.get('user_id')
    except:
        return None

# --- AUTHENTIFICATION ---
@csrf_exempt
def api_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username, password = data.get('username'), data.get('password')
            if not username or not password:
                return JsonResponse({"error": "Champs requis"}, status=400)
            users = load_json(USERS_JSON_PATH, [])
            if any(u['username'] == username for u in users):
                return JsonResponse({"error": "Utilisateur existant"}, status=400)
            
            new_user = {"id": len(users) + 1, "username": username, "password": password}
            users.append(new_user)
            save_json(USERS_JSON_PATH, users)
            return JsonResponse({"status": "success", "message": "Inscription réussie !"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username, password = data.get('username'), data.get('password')
            users = load_json(USERS_JSON_PATH, [])
            user = next((u for u in users if u['username'] == username and u['password'] == password), None)
            if not user:
                return JsonResponse({"error": "Identifiants invalides"}, status=401)

            payload = {"user_id": user['id'], "username": user['username'], "exp": datetime.utcnow() + timedelta(hours=1)}
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            response = JsonResponse({"status": "success", "message": f"Bienvenue {username} !"})
            response.set_cookie(key='jwt_token', value=token, httponly=True, samesite='Lax', max_age=3600)
            return response
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

@csrf_exempt
def api_logout(request):
    if request.method == 'POST':
        response = JsonResponse({"status": "success", "message": "Déconnecté"})
        response.delete_cookie('jwt_token')
        return response
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

@csrf_exempt
def api_profile(request):
    if request.method == 'GET':
        user_id = get_current_user_id(request)
        if not user_id:
            return JsonResponse({"error": "Non authentifié"}, status=401)
        users = load_json(USERS_JSON_PATH, [])
        user = next((u for u in users if u['id'] == user_id), None)
        if not user:
            return JsonResponse({"error": "Utilisateur introuvable"}, status=404)
        return JsonResponse({"status": "success", "user": {"id": user['id'], "username": user['username']}})
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


# --- TO-DOS FILTRÉES PAR UTILISATEUR ---
@csrf_exempt
def api_todos(request, task_id=None):
    user_id = get_current_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Veuillez vous connecter pour voir vos tâches"}, status=401)

    tasks = load_json(TASKS_JSON_PATH, [])

    if request.method == 'GET':
        # Filtrer uniquement les tâches de l'utilisateur connecté
        user_tasks = [t for t in tasks if t.get('user_id') == user_id]
        return JsonResponse({"message": "API Django connectée avec succès !", "tasks": user_tasks})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_text = data.get('text')
            if new_text:
                new_id = max([t['id'] for t in tasks], default=0) + 1
                new_task = {"id": new_id, "user_id": user_id, "text": new_text}
                tasks.append(new_task)
                save_json(TASKS_JSON_PATH, tasks)
                return JsonResponse({"status": "success", "task": new_task}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method in ['PUT', 'PATCH']:
        if task_id is None:
            return JsonResponse({"error": "ID manquant"}, status=400)
        try:
            data = json.loads(request.body)
            new_text = data.get('text')
            for task in tasks:
                if task['id'] == task_id and task.get('user_id') == user_id:
                    task['text'] = new_text
                    save_json(TASKS_JSON_PATH, tasks)
                    return JsonResponse({"status": "success", "tasks": [t for t in tasks if t.get('user_id') == user_id]})
            return JsonResponse({"error": "Tâche non trouvée ou non autorisée"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'DELETE':
        if task_id is None:
            return JsonResponse({"error": "ID manquant"}, status=400)
        
        filtered_tasks = [t for t in tasks if not (t['id'] == task_id and t.get('user_id') == user_id)]
        if len(filtered_tasks) < len(tasks):
            save_json(TASKS_JSON_PATH, filtered_tasks)
            return JsonResponse({"status": "success", "tasks": [t for t in filtered_tasks if t.get('user_id') == user_id]})
        return JsonResponse({"error": "Tâche non trouvée ou non autorisée"}, status=404)
        
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

urlpatterns = [
    path('api/todos/', api_todos),
    path('api/todos/<int:task_id>/', api_todos),
    path('api/register/', api_register),
    path('api/login/', api_login),
    path('api/logout/', api_logout),
    path('api/profile/', api_profile),
]