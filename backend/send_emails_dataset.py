import os
import json
import time
import psycopg2
import smtplib
import ssl  # Ajouté pour la connexion SSL native
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuration fixe pour Gmail (règle le problème du Cron Docker)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mdp_samer")
DB_NAME = os.getenv("DB_NAME", "test_db")
DB_PORT = os.getenv("DB_PORT", "5432")

# --- CORRECTION SÉCURITÉ CRITIQUE ---
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

if not SMTP_EMAIL or not SMTP_PASSWORD:
    raise ValueError("❌ Erreur critique : Les variables d'environnement SMTP_EMAIL et SMTP_PASSWORD sont obligatoires.")

DATASET_FILE = "/app/dataset/emails_dataset.json"

def get_db_connection():
    return psycopg2.connect(
        host="db_service",
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def get_already_processed_ids():
    """Charge tous les identifiants déjà traités en une seule fois."""
    processed_ids = set()
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT custom_message_id FROM processed_emails;")
            rows = cur.fetchall()
            for row in rows:
                processed_ids.add(row[0])
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement des e-mails traités : {e}")
    finally:
        conn.close()
    return processed_ids

def save_to_db(custom_id, recipient, status="sent"):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO processed_emails (custom_message_id, recipient_email, status, sent_at, replied_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (custom_message_id) DO NOTHING;
        """,
        (custom_id, recipient, status)
    )
    conn.commit()
    cur.close()
    conn.close()

def send_email(subject, body, msg_id=None, thread_id=None, attachments=None):
    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = SMTP_EMAIL  
    msg['Subject'] = subject
    
    if msg_id:
        msg['Message-ID'] = msg_id
    if thread_id:
        msg['In-Reply-To'] = thread_id
    if thread_id:
        msg['References'] = thread_id

    msg.attach(MIMEText(body, 'plain'))
    
    if attachments:
        for filepath in attachments:
            if not os.path.exists(filepath):
                print(f"⚠️ Pièce jointe introuvable et ignorée : {filepath}")
                continue
                
            filename = os.path.basename(filepath)
            content_type, encoding = mimetypes.guess_type(filepath)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            with open(filepath, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={filename}",
            )
            msg.attach(part)
            print(f"📎 Pièce jointe ajoutée avec succès : {filename}")
    
    # --- MODIFICATION ICI : Passage sur le port SSL 465 ---
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"❌ Échec critique de l'envoi de l'e-mail : {e}")
        raise e  # On propage l'erreur pour que process_single_email la gère s'il le faut

def find_attachment_path(filename):
    dataset_dir = os.path.dirname(DATASET_FILE)
    possible_paths = [
        os.path.join(dataset_dir, "attachments", "csv", filename),
        os.path.join(dataset_dir, "attachments", "images", filename),
        os.path.join(dataset_dir, "attachments", "pdf", filename),
        os.path.join(dataset_dir, "attachments", "txt" , filename),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def process_single_email():
    if not os.path.exists(DATASET_FILE):
        print(f"❌ Fichier dataset introuvable : {DATASET_FILE}")
        return

    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data.get("messages", [])
    if not messages:
        print("❌ Aucun message trouvé dans la clé 'messages' du dataset.")
        return

    print(f"🔍 Scan du dataset ({len(messages)} e-mails trouvés)...")
    
    # 🚀 Optimisation : Chargement unique en mémoire des IDs déjà traités
    already_processed = get_already_processed_ids()

    for email_data in messages:
        custom_id = email_data.get("message_id") or email_data.get("id")
        if not custom_id:
            continue

        # 🚀 Optimisation : Vérification en O(1) en mémoire au lieu d'un SELECT par ligne
        if custom_id in already_processed:
            continue

        subject = email_data.get("subject", "Sans objet")
        body = email_data.get("body_text", "")
        
        attachments_raw = email_data.get("attachments", [])
        attachment_paths = []
        
        for item in attachments_raw:
            filename = None
            if isinstance(item, dict):
                filename = item.get("file_name") or item.get("filename") or item.get("name")
            elif isinstance(item, str):
                filename = item
                
            if filename:
                file_path = find_attachment_path(filename)
                if file_path:
                    attachment_paths.append(file_path)
                else:
                    print(f"⚠️ Impossible de localiser le fichier physique pour : {filename}")

        print(f"📬 E-mail sélectionné : {custom_id} (Sujet : {subject})")
        
        try:
            # Envoi initial
            send_email(subject, body, msg_id=custom_id, attachments=attachment_paths)
            print(f"✅ E-mail initial envoyé avec succès !")

            time.sleep(2)
            
            # Envoi de la réponse (Reply)
            reply_id = f"reply_{custom_id}"
            reply_body = "Bonjour, \n\nCeci est le suivi automatique pour simuler un échange continu.\n\nCordialement."
            send_email(f"Re: {subject}", reply_body, msg_id=reply_id, thread_id=custom_id)
            print(f"🔄 Envoi de la réponse chaînée (Reply)...")

            # Validation BDD si tout s'est bien passé
            save_to_db(custom_id, SMTP_EMAIL)
            print(f"🏁 Traitement validé en BDD pour {custom_id} !")
            return  # Arrêt après un e-mail traité conformément à ta logique initiale

        except Exception as err:
            print(f"💥 Erreur durant l'exécution du traitement pour {custom_id}: {err}")
            return

    print("🎉 Tous les e-mails du dataset ont été traités !")

if __name__ == "__main__":
    process_single_email()