import os
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from email.utils import parsedate_to_datetime

# --- Configuration ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mdp_samer")
DB_NAME = os.getenv("DB_NAME", "test_db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_HOST = "db_service"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama_local:11434")
EMBEDDING_MODEL = "nomic-embed-text"

# --- Schémas Pydantic ---
class DocumentChunk(BaseModel):
    message_id: str = Field(..., description="ID unique de l'e-mail")
    chunk_text: str = Field(..., description="Segment de texte extrait")
    subject: Optional[str] = Field("Sans objet", description="Sujet de l'e-mail")
    body_text: Optional[str] = Field("", description="Contenu textuel de l'e-mail")
    recipient_email: Optional[str] = None
    similarity: float = Field(..., description="Score de similarité")


def get_db_connection():
    """Crée une nouvelle connexion autonome et réinitialise tout état d'erreur transactionnel."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )
    conn.autocommit = True
    conn.rollback()
    return conn


def get_query_embedding(query: str) -> List[float]:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": query},
            timeout=5
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"⚠️ Ollama non disponible : {e}")
        return []


def retrieve_relevant_emails(query: str, limit: int = 10) -> List[DocumentChunk]:
    chunks = []
    query_vector = get_query_embedding(query)
    if not query_vector:
        return chunks

    vector_str = "[" + ",".join(map(str, query_vector)) + "]"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = """
                SELECT 
                    email_id as message_id, 
                    chunk_text,
                    (1 - (embedding <=> %s::vector)) AS similarity
                FROM email_embeddings
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """
            cur.execute(query_sql, (vector_str, vector_str, limit))
            results = cur.fetchall()
            
            for row in results:
                chunk = DocumentChunk(
                    message_id=row['message_id'],
                    chunk_text=row['chunk_text'],
                    subject="Sans objet",
                    body_text=row['chunk_text'],
                    recipient_email=None,
                    similarity=float(row['similarity'])
                )
                chunks.append(chunk)
    except Exception as e:
        print(f"⚠️ Erreur PGVector ignorée : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        
    return chunks


# =====================================================================
# --- TOOLS (FUNCTION CALLING) ---
# =====================================================================

def parse_any_date(date_input: Any) -> datetime:
    """Tente de parser la date sous forme de datetime quel que soit son format."""
    if not date_input:
        return None
        
    date_str = str(date_input).strip()
    
    # 1. Essai du parser standard RFC 2822 (courrier/email)
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        pass

    # 2. Essais sur les formats ISO et habituels
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y/%m/%d",
        "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:19], fmt)
        except Exception:
            continue
            
    return None


def search_emails_by_date(target_date: str) -> List[Dict[str, Any]]:
    """Recherche les e-mails de manière robuste en comparant directement les portions de dates."""
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # On récupère les e-mails ayant une date
            query_sql = "SELECT email_id, chunk_text, metadata FROM email_embeddings WHERE metadata->>'date' IS NOT NULL;"
            cur.execute(query_sql)
            rows = cur.fetchall()
            
            target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
            
            seen_emails = set()
            
            for row in rows:
                email_id = str(row.get('email_id'))
                if email_id in seen_emails:
                    continue  # Évite les doublons si plusieurs chunks pour le même email
                
                meta = row.get('metadata')
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        continue
                
                date_str = str(meta.get('date', ''))
                parsed_dt = parse_any_date(date_str)
                
                if parsed_dt and parsed_dt.date() == target_dt:
                    seen_emails.add(email_id)
                    text = row.get('chunk_text', '')
                    if len(text) > 400:
                        text = text[:400] + "..."
                        
                    results.append({
                        "email_id": email_id, 
                        "date": date_str,
                        "content": text
                    })
                
    except Exception as e:
        print(f"❌ Erreur Tool search_emails_by_date : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            
    return results


def search_emails_between_dates(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Recherche exacte des e-mails entre deux dates (format YYYY-MM-DD)."""
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = "SELECT email_id, chunk_text, metadata FROM email_embeddings WHERE metadata->>'date' IS NOT NULL;"
            cur.execute(query_sql)
            rows = cur.fetchall()
            
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            for row in rows:
                meta = row.get('metadata')
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        continue
                
                date_str = meta.get('date') if isinstance(meta, dict) else None
                if not date_str:
                    continue
                
                parsed_dt = parse_any_date(date_str)
                if not parsed_dt:
                    continue
                    
                email_date = parsed_dt.date()
                if start_dt <= email_date <= end_dt:
                    text = row.get('chunk_text', '')
                    if len(text) > 150:
                        text = text[:150] + "..."
                        
                    results.append({
                        "email_id": str(row.get('email_id')), 
                        "date": str(date_str),
                        "content": text
                    })
            
    except Exception as e:
        print(f"❌ Erreur Tool search_emails_between_dates : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return results


def search_emails_by_person(person_name: str) -> List[Dict[str, Any]]:
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = "SELECT email_id, chunk_text FROM email_embeddings WHERE chunk_text ILIKE %s;"
            cur.execute(query_sql, (f"%{person_name}%",))
            rows = cur.fetchall()
            for row in rows:
                text = row.get('chunk_text', '')
                if len(text) > 150:
                    text = text[:150] + "..."
                results.append({"email_id": row.get('email_id'), "content": text})
    except Exception as e:
        print(f"❌ Erreur Tool search_emails_by_person : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            
    return results


def get_email_attachments(email_id: Optional[str] = None, file_extension: Optional[str] = None) -> List[Dict[str, Any]]:
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if file_extension:
                extensions = [ext.strip().lstrip('.') for ext in file_extension.replace(',', ' ').split() if ext.strip()]
                
                if len(extensions) > 1:
                    placeholders = " OR ".join(["file_name ILIKE %s" for _ in extensions])
                    query_sql = f"""
                        SELECT COUNT(DISTINCT email_id) AS total 
                        FROM email_embeddings 
                        WHERE source_type = 'attachment' AND ({placeholders});
                    """
                    params = [f"%.{ext}%" for ext in extensions]
                    cur.execute(query_sql, params)
                else:
                    target_ext = extensions[0] if extensions else "pdf"
                    ext_pattern = f"%.{target_ext}%"
                    query_sql = """
                        SELECT COUNT(DISTINCT email_id) AS total 
                        FROM email_embeddings 
                        WHERE source_type = 'attachment' AND file_name ILIKE %s;
                    """
                    cur.execute(query_sql, (ext_pattern,))
                
                row = cur.fetchone()
                total_count = row['total'] if row and 'total' in row else 0
                results.append({
                    "file_extension_searched": file_extension,
                    "total_matching_emails": int(total_count)
                })
                
            elif email_id is None:
                query_sql = """
                    SELECT COUNT(DISTINCT email_id) AS total 
                    FROM email_embeddings 
                    WHERE source_type = 'attachment';
                """
                cur.execute(query_sql)
                row = cur.fetchone()
                total_count = row['total'] if row and 'total' in row else 0
                results.append({
                    "file_extension_searched": "all",
                    "total_matching_emails": int(total_count)
                })
                
            elif email_id:
                query_sql = """
                    SELECT DISTINCT email_id, file_name 
                    FROM email_embeddings 
                    WHERE source_type = 'attachment' AND email_id = %s;
                """
                cur.execute(query_sql, (email_id,))
                rows = cur.fetchall()
                for row in rows:
                    results.append(dict(row))
    except Exception as e:
        print(traceback.format_exc())
        results.append({"error": str(e)})
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        
    return results


def get_email_by_id(email_id: str) -> List[Dict[str, Any]]:
    """Récupère le contenu complet d'un e-mail grâce à son ID unique."""
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = "SELECT email_id, chunk_text FROM email_embeddings WHERE email_id = %s;"
            cur.execute(query_sql, (email_id,))
            rows = cur.fetchall()
            for row in rows:
                results.append({"email_id": row.get('email_id'), "content": row.get('chunk_text', '')})
    except Exception as e:
        print(f"❌ Erreur Tool get_email_by_id : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return results


def search_emails_by_subject(keyword: str) -> List[Dict[str, Any]]:
    """Recherche des e-mails en fonction d'un mot-clé spécifique."""
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = "SELECT email_id, chunk_text FROM email_embeddings WHERE chunk_text ILIKE %s;"
            cur.execute(query_sql, (f"%{keyword}%",))
            rows = cur.fetchall()
            for row in rows:
                text = row.get('chunk_text', '')
                if len(text) > 150:
                    text = text[:150] + "..."
                results.append({"email_id": row.get('email_id'), "content": text})
    except Exception as e:
        print(f"❌ Erreur Tool search_emails_by_subject : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return results


def get_emails_advanced_filter(name: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """Récupère les e-mails avec filtres optionnels sur le nom de la personne et/ou une plage de dates."""
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = """
                SELECT 
                    email_id, 
                    chunk_text, 
                    metadata,
                    source_type,
                    file_name
                FROM email_embeddings;
            """
            cur.execute(query_sql)
            rows = cur.fetchall()
            
            start_dt = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
            end_dt = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
            
            emails_dict = {}
            
            for row in rows:
                email_id = str(row.get('email_id'))
                if not email_id:
                    continue
                
                if email_id not in emails_dict:
                    emails_dict[email_id] = {
                        "email_id": email_id,
                        "content": "",
                        "date": None,
                        "sender": "",
                        "attachments": []
                    }
                
                text = row.get('chunk_text', '')
                if text and not emails_dict[email_id]["content"]:
                    emails_dict[email_id]["content"] = text
                
                meta = row.get('metadata')
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                
                if isinstance(meta, dict):
                    if not emails_dict[email_id]["date"]:
                        emails_dict[email_id]["date"] = meta.get('date')
                    if not emails_dict[email_id]["sender"]:
                        emails_dict[email_id]["sender"] = meta.get('sender') or meta.get('from') or meta.get('author', '')
                
                source_type = row.get('source_type')
                file_name = row.get('file_name')
                if source_type == 'attachment' or file_name:
                    if file_name and file_name not in emails_dict[email_id]["attachments"]:
                        emails_dict[email_id]["attachments"].append(file_name)

            for email_id, data in emails_dict.items():
                match = True
                
                if name:
                    name_clean = name.strip().lower()
                    sender_str = str(data["sender"]).lower()
                    content_str = str(data["content"]).lower()
                    if name_clean not in sender_str and name_clean not in content_str:
                        match = False
                
                if match and (start_dt or end_dt):
                    date_str = data["date"]
                    if not date_str:
                        match = False
                    else:
                        parsed_dt = parse_any_date(date_str)
                        if not parsed_dt:
                            match = False
                        else:
                            email_date = parsed_dt.date()
                            if start_dt and email_date < start_dt:
                                match = False
                            if end_dt and email_date > end_dt:
                                match = False
                
                if match:
                    results.append(data)
                    
    except Exception as e:
        print(f"❌ Erreur get_emails_advanced_filter : {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
                
    return results


# =====================================================================
# --- SCHÉMAS DES TOOLS POUR L'API GROQ ---
# =====================================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_emails_by_date",
            "description": "Recherche les e-mails par date exacte (YYYY-MM-DD).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {"type": "string", "description": "Date au format YYYY-MM-DD"}
                },
                "required": ["target_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails_between_dates",
            "description": "Recherche des e-mails reçus entre une date de début et une date de fin au format YYYY-MM-DD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Date de début au format YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "Date de fin au format YYYY-MM-DD"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails_by_person",
            "description": "Recherche les e-mails où une personne spécifique est mentionnée. Extrait le nom ou prénom exact de la question de l'utilisateur (ex: 'Ines').",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {"type": "string", "description": "Le prénom ou le nom exact mentionné dans la question (ex: Ines)"}
                },
                "required": ["person_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_attachments",
            "description": "Récupère les pièces jointes d'un e-mail OU compte les e-mails contenant une ou plusieurs extensions spécifiques (ex: pdf, txt, csv, png).",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": ["string", "null"],
                        "description": "ID unique du message (Mettre null si recherche globale par extension)."
                    },
                    "file_extension": {
                        "type": ["string", "null"],
                        "description": "Extension(s) de fichier à filtrer, séparées par des virgules ou espaces (ex: pdf, txt, csv, png)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_by_id",
            "description": "Récupère le contenu complet d'un e-mail spécifique en connaissant son ID unique (ex: 85, 190).",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {"type": "string", "description": "L'ID unique de l'e-mail recherché"}
                },
                "required": ["email_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails_by_subject",
            "description": "Recherche des e-mails en fonction d'un mot-clé présent dans le sujet ou le texte (ex: 'Facture', 'Urgent', 'Projet').",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Le mot-clé à rechercher (ex: Facture, Urgent)"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_emails_advanced_filter",
            "description": "Récupère les e-mails avec des filtres optionnels sur le nom (expéditeur ou contenu) et/ou une plage de dates (date_from, date_to au format YYYY-MM-DD). Si aucun paramètre n'est fourni, renvoie tous les e-mails avec leurs pièces jointes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": ["string", "null"],
                        "description": "Nom de la personne à rechercher (expéditeur ou dans le texte)."
                    },
                    "date_from": {
                        "type": ["string", "null"],
                        "description": "Date de début minimale au format YYYY-MM-DD."
                    },
                    "date_to": {
                        "type": ["string", "null"],
                        "description": "Date de fin maximale au format YYYY-MM-DD."
                    }
                },
                "required": []
            }
        }
    }
]