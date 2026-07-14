import os
import json
import time
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration de la base de données et SMTP
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mdp_samer")  # <-- Corrigé ici
DB_NAME = os.getenv("DB_NAME", "test_db")            # <-- Corrigé ici
DB_PORT = os.getenv("DB_PORT", "5432")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "samer.stage.ia@gmail.com") # <-- Ajouté par sécurité
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "lqbvmvvnryesurci")    # <-- Ajouté par sécurité

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

def send_email(subject, body, msg_id=None, thread_id=None):
    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = SMTP_EMAIL  # Envoi à toi-même pour test
    msg['Subject'] = subject
    
    if msg_id:
        msg['Message-ID'] = msg_id
    if thread_id:
        msg['In-Reply-To'] = thread_id
        msg['References'] = thread_id

    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

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
        
        print(f"📬 E-mail sélectionné : {custom_id} (Sujet : {subject})")
        
        # 1. Envoi du mail initial
        send_email(subject, body, msg_id=custom_id)
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