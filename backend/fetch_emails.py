import os
import json
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import logging
import traceback
import re

# Dossier de destination à l'intérieur du conteneur (/app pointe sur backend)
RECEIVED_DIR = "/app/received_emails"
os.makedirs(RECEIVED_DIR, exist_ok=True)

# --- CORRECTION SÉCURITÉ CRITIQUE ---
IMAP_SERVER = "imap.gmail.com"
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

if not SMTP_EMAIL or not SMTP_PASSWORD:
    raise ValueError("❌ Erreur critique : Les variables d'environnement SMTP_EMAIL et SMTP_PASSWORD sont obligatoires.")

# --- CONFIGURATION STRICTE DES LOGS ---
logger = logging.getLogger("scrapper_logger")
logger.setLevel(logging.DEBUG)

log_format = logging.Formatter('%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

os.makedirs('/app/logs', exist_ok=True)

file_handler = logging.FileHandler('/app/logs/reception.log', encoding='utf-8')
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_format)
logger.addHandler(stream_handler)


def clean_message_id(msg_id: str) -> str:
    """Nettoie le Message-ID pour qu'il soit utilisable dans un nom de dossier."""
    if not msg_id:
        return "unknown_id"
    return re.sub(r'[^a-zA-Z0-9_\.-]', '_', msg_id).strip('_')


def get_already_downloaded_message_ids():
    """
    Parcourt le dossier pour lister les Message-IDs de mails déjà récupérés.
    """
    downloaded_ids = set()
    if not os.path.exists(RECEIVED_DIR):
        return downloaded_ids
        
    for folder_name in os.listdir(RECEIVED_DIR):
        # On lit le fichier JSON de métadonnées s'il existe pour récupérer le vrai Message-ID stable
        json_path = os.path.join(RECEIVED_DIR, folder_name, "contenu_email.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stable_id = data.get("Message_ID")
                    if stable_id:
                        downloaded_ids.add(stable_id)
            except Exception:
                pass
                
        # Rétrocompatibilité : si l'ancien format était basé sur la fin du nom du dossier
        if folder_name.startswith("email_") and len(folder_name.split('_')) >= 3:
            parts = folder_name.split('_')
            downloaded_ids.add(parts[-1])
            
    return downloaded_ids


def fetch_and_save_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(SMTP_EMAIL, SMTP_PASSWORD)
        mail.select("inbox")
        
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            logger.error("❌ Impossible de fouiller la boîte de réception Gmail.")
            return

        mail_ids = messages[0].split()
        total_mails = len(mail_ids)
        
        if not mail_ids:
            logger.info("📭 Aucun e-mail trouvé sur ton Gmail pour le moment.")
            mail.logout()
            return
            
        logger.info(f"🔍 checking {total_mails} mails")
        
        already_downloaded = get_already_downloaded_message_ids()
        
        # Pré-filtrage ou récupération par batch pour identifier rapidement les nouveaux
        # Traitement individuel optimisé (complexité linéaire O(n))
        new_mail_count = 0
        
        for index, mid in enumerate(mail_ids, start=1):
            status, data = mail.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            raw_msg_id = msg.get("Message-ID")
            stable_msg_id = clean_message_id(raw_msg_id)
            
            # Vérification de déduplication via la clé stable
            if stable_msg_id in already_downloaded or (raw_msg_id and raw_msg_id in already_downloaded):
                continue
                
            new_mail_count += 1
            
            subject, encoding = decode_header(msg["Subject"])[0] if msg["Subject"] else ("", "utf-8")
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
                
            from_ = msg.get("From")
            date_header = msg.get("Date")
            
            # Utilisation de la date du message si possible, sinon repli sur la date du jour
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_header)
                timestamp = parsed_date.strftime("%Y%m%d_%H%M%S")
            except Exception:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
            email_folder = os.path.join(RECEIVED_DIR, f"email_{timestamp}_{stable_msg_id}")
            os.makedirs(email_folder, exist_ok=True)
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    filename = part.get_filename()

                    if filename:
                        filepath = os.path.join(email_folder, filename)
                        payload = part.get_payload(decode=True)
                        if payload:
                            with open(filepath, "wb") as f:
                                f.write(payload)
                    elif content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
            
            email_data = {
                "Message_ID": raw_msg_id,
                "Gmail_ID": mid.decode(),
                "De": from_,
                "A": [msg.get("To")],
                "Sujet": subject,
                "Date": date_header,
                "Corps": body
            }
            
            with open(os.path.join(email_folder, "contenu_email.json"), "w", encoding="utf-8") as f:
                json.dump(email_data, f, indent=4, ensure_ascii=False)
                
            # 🚀 Utilisation directe de l'index de enumerate (évite le O(n²) de .index())
            logger.info(f"✅ {index}/{total_mails} treated")

        if new_mail_count == 0:
            logger.info("⏭️ skipped : tous les e-mails sont déjà stockés en local ou aucun nouveau.")
        
        mail.logout()

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"❌ Erreur critique lors de la récupération depuis Gmail :\n{error_details}")

if __name__ == "__main__":
    fetch_and_save_emails()