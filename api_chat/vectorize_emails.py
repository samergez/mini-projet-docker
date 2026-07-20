import os
import json
import hashlib
import csv
import psycopg2
from psycopg2.extras import execute_values
import requests
from pypdf import PdfReader

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "db_service",
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "database": os.getenv("DB_NAME", "email_db"),
    "port": os.getenv("DB_PORT", "5432")
}

OLLAMA_URL = "http://ollama:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text"
EMAILS_DIR = "/app/received_emails"

CHUNK_SIZE = 500  
CHUNK_OVERLAP = 50  

# --- GESTION DES DOUBLONS PAR HACHAGE ---
def calculate_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# --- DECOUPAGE (CHUNKING) ---
def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

# --- GENERER LES VECTEURS (EMBEDDING) ---
def get_ollama_embedding(text):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"❌ Erreur Ollama sur le chunk : {e}")
        return None

# --- EXTRACTION DES PIÈCES JOINTES ---
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    except Exception as e:
        print(f"❌ Impossible de lire le PDF {pdf_path}: {e}")
    return text

def extract_text_from_csv(csv_path):
    text = ""
    try:
        with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                text += " ".join(row) + "\n"
    except Exception as e:
        print(f"❌ Impossible de lire le CSV {csv_path}: {e}")
    return text

# --- INITIALISATION DE LA TABLE ---
def init_vector_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_embeddings (
            id SERIAL PRIMARY KEY,
            email_id VARCHAR(100),
            source_type VARCHAR(20), 
            file_name VARCHAR(255),
            chunk_index INT,
            chunk_text TEXT,
            content_hash VARCHAR(32) UNIQUE,
            embedding vector(768),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- VERIFIER SI UN HASH EXISTE DEJA ---
def hash_exists(cur, content_hash):
    cur.execute("SELECT 1 FROM email_embeddings WHERE content_hash = %s LIMIT 1;", (content_hash,))
    return cur.fetchone() is not None

# --- INSERTION DES CHUNKS EN BASE ---
def save_chunks_to_db(cur, conn, chunks, email_id, source_type, file_name=""):
    rows_to_insert = []
    
    for index, chunk in enumerate(chunks):
        chunk_hash = calculate_md5(f"{email_id}_{source_type}_{file_name}_{index}_{chunk}")
        
        # 🔍 Si le hash existe déjà en BDD, on passe directement sans appeler Ollama
        if hash_exists(cur, chunk_hash):
            continue
            
        vector = get_ollama_embedding(chunk)
        if vector:
            rows_to_insert.append((email_id, source_type, file_name, index, chunk, chunk_hash, vector))
    
    if rows_to_insert:
        try:
            execute_values(
                cur,
                """INSERT INTO email_embeddings (email_id, source_type, file_name, chunk_index, chunk_text, content_hash, embedding)
                   VALUES %s ON CONFLICT (content_hash) DO NOTHING;""",
                rows_to_insert
            )
            conn.commit()
            print(f"✅ {len(rows_to_insert)} nouveaux chunks insérés ({source_type}) pour {email_id}.")
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur lors de l'insertion en base : {e}")

# --- PIPELINE PRINCIPAL ---
def process_embeddings():
    init_vector_table()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    if not os.path.exists(EMAILS_DIR):
        print("📂 Aucun dossier d'e-mails trouvé.")
        return

    print("🔍 Analyse et vectorisation des e-mails...")
    for folder_name in os.listdir(EMAILS_DIR):
        folder_path = os.path.join(EMAILS_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
            
        json_path = os.path.join(folder_path, "contenu_email.json")
        if not os.path.exists(json_path):
            continue
            
        with open(json_path, 'r', encoding='utf-8') as f:
            email_data = json.load(f)
            
        email_id = email_data.get("id", folder_name)
        
        # 1. Traitement du corps de l'e-mail
        full_text = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
        if full_text.strip():
            chunks = chunk_text(full_text)
            save_chunks_to_db(cur, conn, chunks, email_id, "email_body")
        
        # 2. Traitement des pièces jointes
        for file_name in os.listdir(folder_path):
            if file_name == "contenu_email.json":
                continue
                
            file_absolute_path = os.path.join(folder_path, file_name)
            extracted_text = ""
            
            if file_name.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(file_absolute_path)
            elif file_name.lower().endswith('.csv'):
                extracted_text = extract_text_from_csv(file_absolute_path)
                
            if extracted_text.strip():
                attachment_chunks = chunk_text(extracted_text)
                save_chunks_to_db(cur, conn, attachment_chunks, email_id, "attachment", file_name)
                
    print("🎉 Traitement terminé !")
    cur.close()
    conn.close()

if __name__ == "__main__":
    process_embeddings()