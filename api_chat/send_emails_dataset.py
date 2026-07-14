import os
import json
import time
import psycopg2
import smtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuration de la base de données et SMTP
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mdp_samer")
DB_NAME = os.getenv("DB_NAME", "test_db")
DB_PORT = os.getenv("DB_PORT", "5432")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "samer.stage.ia@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "lqbvmvvnryesurci")

DATASET_FILE = "/app/dataset/emails_dataset.json"

def get_db_connection():
    return psycopg2.connect(
        host="db_service",
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def email_already_processed(custom_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM processed_emails WHERE custom_message_id = %s;", (custom_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

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
    msg['To'] = SMTP_EMAIL  # Envoi à toi-même pour test
    msg['Subject'] = subject
    
    if msg_id:
        msg['Message-ID'] = msg_id
    if thread_id:
        msg['In-Reply-To'] = thread_id
        msg['References'] = thread_id

    # Attacher le corps du texte
    msg.attach(MIMEText(body, 'plain'))
    
    # Gestion des pièces jointes
    if attachments:
        for filepath in attachments:
            if not os.path.exists(filepath):
                print(f"⚠️ Pièce jointe introuvable et ignorée : {filepath}")
                continue
                
            filename = os.path.basename(filepath)
            
            # Détecter le type de fichier (PDF, image, CSV, etc.)
            content_type, encoding = mimetypes.guess_type(filepath)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            # Lecture du fichier en binaire
            with open(filepath, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            
            # Encodage
            encoders.encode_base64(part)
            
            # Ajout des headers
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={filename}",
            )
            msg.attach(part)
            print(f"📎 Pièce jointe ajoutée avec succès : {filename}")
    
    # Envoi via SMTP Gmail
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

def find_attachment_path(filename):
    """
    Parcourt les sous-dossiers csv, images et pdf pour trouver le chemin d'accès réel du fichier dans Docker.
    """
    dataset_dir = os.path.dirname(DATASET_FILE) # /app/dataset
    
    # Liste des sous-dossiers possibles d'après ton architecture
    possible_paths = [
        os.path.join(dataset_dir, "attachments", "csv", filename),
        os.path.join(dataset_dir, "attachments", "images", filename),
        os.path.join(dataset_dir, "attachments", "pdf", filename),
        os.path.join(dataset_dir, "attachments", "txt" , filename), # Au cas où
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

    # Récupération de la liste des messages
    messages = data.get("messages", [])
    if not messages:
        print("❌ Aucun message trouvé dans la clé 'messages' du dataset.")
        return

    print(f"🔍 Scan du dataset ({len(messages)} e-mails trouvés)...")

    for email_data in messages:
        custom_id = email_data.get("message_id") or email_data.get("id")
        
        if not custom_id:
            continue

        # Éviter les doublons
        if email_already_processed(custom_id):
            continue

        subject = email_data.get("subject", "Sans objet")
        body = email_data.get("body_text", "")
        
        # Récupération des pièces jointes déclarées dans le JSON
        attachments_raw = email_data.get("attachments", [])
        attachment_paths = []
        
        for item in attachments_raw:
            filename = None
            
            # Si la pièce jointe est un dictionnaire
            if isinstance(item, dict):
                filename = item.get("file_name") or item.get("filename") or item.get("name")
            # Si c'est directement une chaîne de texte
            elif isinstance(item, str):
                filename = item
                
            if filename:
                # Recherche intelligente du chemin du fichier dans l'arborescence
                file_path = find_attachment_path(filename)
                if file_path:
                    attachment_paths.append(file_path)
                else:
                    print(f"⚠️ Impossible de localiser le fichier physique pour : {filename}")

        print(f"📬 E-mail sélectionné : {custom_id} (Sujet : {subject})")
        
        # 1. Envoi du mail initial avec pièces jointes si trouvées
        send_email(subject, body, msg_id=custom_id, attachments=attachment_paths)
        print(f"✅ E-mail initial envoyé avec succès !")

        # 2. Simulation de la réponse (Reply)
        time.sleep(2)
        reply_id = f"reply_{custom_id}"
        reply_body = "Bonjour, \n\nCeci est le suivi automatique pour simuler un échange continu.\n\nCordialement."
        send_email(f"Re: {subject}", reply_body, msg_id=reply_id, thread_id=custom_id)
        print(f"🔄 Envoi de la réponse chaînée (Reply)...")

        # 3. Sauvegarde en BDD
        save_to_db(custom_id, SMTP_EMAIL)
        print(f"🏁 Traitement validé en BDD pour {custom_id} !")
        return

    print("🎉 Tous les e-mails du dataset ont été traités !")

if __name__ == "__main__":
    process_single_email()