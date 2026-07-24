import os
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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


def retrieve_relevant_emails(query: str, limit: int = 5) -> List[DocumentChunk]:
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

def search_emails_by_date(target_date: str) -> List[Dict[str, Any]]:
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query_sql = "SELECT email_id, chunk_text FROM email_embeddings WHERE chunk_text LIKE %s;"
            cur.execute(query_sql, (f"%{target_date}%",))
            rows = cur.fetchall()
            for row in rows:
                results.append({"email_id": row.get('email_id'), "content": row.get('chunk_text')})
    except Exception as e:
        print(f"❌ Erreur Tool search_emails_by_date : {e}")
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
                results.append({"email_id": row.get('email_id'), "content": row.get('chunk_text')})
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
    """Requête désormais la table unifiée email_embeddings où source_type = 'attachment'"""
    results = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if file_extension:
                # Gère le cas de plusieurs extensions séparées par des virgules ou des espaces (ex: "pdf, txt, csv, png")
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
                # Si aucune extension n'est spécifiée, on renvoie le total global des e-mails avec pièces jointes
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
        print("❌ [DEBUG TOOL ERROR] L'EXCEPTION EXACTE EST :")
        print(traceback.format_exc())
        results.append({"error": str(e)})
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
            "name": "search_emails_by_person",
            "description": "Recherche les e-mails liés à une personne.",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {"type": "string", "description": "Nom ou prénom"}
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
    }
]


if __name__ == "__main__":
    print("🔍 Test direct :")
    print(get_email_attachments(file_extension="pdf"))