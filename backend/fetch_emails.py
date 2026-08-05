import os
import json
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import logging
import traceback

# Dossier de destination à l'intérieur du conteneur (/app pointe sur backend)
RECEIVED_DIR = "/app/received_emails"
os.makedirs(RECEIVED_DIR, exist_ok=True)

# Configuration fixe pour ton Gmail
IMAP_SERVER = "imap.gmail.com"
SMTP_EMAIL = "samer.stage.ia@gmail.com"
SMTP_PASSWORD = "lqbvmvvnryesurci"  # Ton mot de passe d'application Google

# --- CONFIGURATION STRICTE DES LOGS ---
logger = logging.getLogger("scrapper_logger")
logger.setLevel(logging.DEBUG)

# Format précis : Date, Heure exacte avec millisecondes, Niveau de log, Message
log_format = logging.Formatter('%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Sécurité : Création du dossier logs s'il n'existe pas encore
os.makedirs('/app/logs', exist_ok=True)

# Option A : Écriture dans le fichier logs/reception.log
file_handler = logging.FileHandler('/app/logs/reception.log', encoding='utf-8')
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# Option B : Affichage simultané en console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_format)
logger.addHandler(stream_handler)


def get_already_downloaded_ids():
    """
    Parcourt le dossier pour lister les IDs de mails déjà récupérés.
    """
    downloaded_ids = set()
    if not os.path.exists(RECEIVED_DIR):
        return downloaded_ids
        
    for folder_name in os.listdir(RECEIVED_DIR):
        if folder_name.startswith("email_") and len(folder_name.split('_')) >= 3:
            parts = folder_name.split('_')
            msg_id = parts[-1] # Récupère l'identifiant court à la fin
            downloaded_ids.add(msg_id)
            
    return downloaded_ids

def fetch_and_save_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(SMTP_EMAIL, SMTP_PASSWORD)
        mail.select("inbox")
        
        # "ALL" permet de scanner l'intégralité des e-mails
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
            
        # Log de début de scan horodaté
        logger.info(f"🔍 checking {total_mails} mails")
        
        already_downloaded = get_already_downloaded_ids()
        
        # Filtrage des doublons locaux
        new_mail_ids = [mid for mid in mail_ids if mid.decode() not in already_downloaded]
        skipped_count = total_mails - len(new_mail_ids)
        
        if skipped_count > 0:
            logger.info(f"⏭️ skipped : {skipped_count} e-mail(s) déjà stocké(s) en local.")
            
        if not new_mail_ids:
            logger.info("🎉 Aucun nouvel e-mail à traiter.")
            mail.logout()
            return
        
        # Traitement individuel
        for mid in new_mail_ids:
            str_id = mid.decode()
            current_index = mail_ids.index(mid) + 1
            
            status, data = mail.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
                
            from_ = msg.get("From")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_folder = os.path.join(RECEIVED_DIR, f"email_{timestamp}_{str_id}")
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
                "Gmail_ID": str_id,
                "De": from_,
                "A": [msg.get("To")],
                "Sujet": subject,
                "Date": msg.get("Date"),
                "Corps": body
            }
            
            with open(os.path.join(email_folder, "contenu_email.json"), "w", encoding="utf-8") as f:
                json.dump(email_data, f, indent=4, ensure_ascii=False)
            
            # Log de succès
            logger.info(f"✅ {current_index}/{total_mails} treated")

        mail.logout()

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"❌ Erreur critique lors de la récupération depuis Gmail :\n{error_details}")

if __name__ == "__main__":
    fetch_and_save_emails()