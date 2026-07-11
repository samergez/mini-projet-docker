import os
import time
import random
import json
import smtplib
import psycopg2
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration des dossiers
EMAILS_DIR = "./data/emails"
ATTACHMENTS_DIR = "./data/attachments"

os.makedirs(EMAILS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Configuration SMTP et Base de Données (Injectés par Docker)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

EXPEDITEURS = [
    "service.client@banque-entreprise.com",
    "logistique@fournisseur-global.fr",
    "direction@client-partenaire.tn",
    "facturation@operateur-telecom.com",
    "support@hebergement-cloud.net"
]

SUJETS_ET_CORPS = [
    {
        "categorie": "Banque",
        "sujet": "Avis de virement SEPA reçu - Ref #89210",
        "corps": "Bonjour Samer,\n\nNous vous informons qu'un virement de 12 450,00 EUR en provenance de la direction financière a été validé et crédité sur votre compte pro ce matin. Vous trouverez l'avis d'opération bancaire officiel en pièce jointe.\n\nCordialement,\nLe service Clientèle Entreprises."
    },
    {
        "categorie": "Fournisseur",
        "sujet": "Facture impayée - Rappel de paiement - Société MaterielIT",
        "corps": "Bonjour l'équipe,\n\nSauf erreur de notre part, nous n'avons toujours pas reçu le règlement concernant notre facture n° FACT-2026-0712 relative au renouvellement de vos serveurs de base de données. Le document PDF est de nouveau joint à cet e-mail.\n\nMerci de régulariser la situation au plus vite."
    },
    {
        "categorie": "Client",
        "sujet": "Demande de devis - Intégration API de messagerie",
        "corps": "Bonjour,\n\nWe aimerions intégrer un agent intelligent capable de trier et de répondre à nos e-mails clients automatiquement. Pouvez-vous nous envoyer vos tarifs et vos disponibilités pour une réunion technique la semaine prochaine ?\n\nMerci d'avance,\nResponsable Innovation."
    },
    {
        "categorie": "Technique",
        "sujet": "Alerte de sécurité - Activité suspecte détectée sur le réseau",
        "corps": "ATTENTION : Notre système de monitoring a détecté 3 tentatives de connexion infructueuses sur l'accès administrateur de votre conteneur de base de données principal. Veuillez consulter le rapport technique joint pour vérifier les adresses IP d'origine."
    }
]

PIECES_JOINTES_TYPES = [
    {"nom": "avis_virement.pdf", "contenu": "FAUX PDF: Avis de virement reçu."},
    {"nom": "facture_2026.pdf", "contenu": "FAUX PDF: Facture en attente de paiement."},
    {"nom": "cahier_des_charges.pdf", "contenu": "FAUX PDF: Spécifications techniques du client."},
    {"nom": "logs_erreur.txt", "contenu": "FAUX TEXTE: Journal des erreurs serveurs."}
]

# --- FONCTIONS DE LA BASE DE DONNÉES (Tâche 11) ---
def get_db_connection():
    return psycopg2.connect(
        host="db_service",
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def email_already_processed(custom_id):
    """Vérifie si l'e-mail a déjà été envoyé pour éviter les doublons."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM processed_emails WHERE custom_message_id = %s;", (custom_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"⚠️ Erreur vérification BDD : {e}")
        return False

def log_email_status(custom_id, recipient, status):
    """Enregistre ou met à jour le statut dans la table anti-doublon."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if status == "sent":
            cur.execute(
                "INSERT INTO processed_emails (custom_message_id, recipient_email, status) VALUES (%s, %s, %s);",
                (custom_id, recipient, status)
            )
        elif status == "replied":
            cur.execute(
                "UPDATE processed_emails SET status = %s, replied_at = CURRENT_TIMESTAMP WHERE custom_message_id = %s;",
                (status, custom_id)
            )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erreur enregistrement BDD : {e}")

# --- FONCTION D'ENVOI SMTP MAIL ET REPLY (Tâche 10 & 12) ---
def send_smtp_email(to_email, subject, body_content, reply_to_id=None):
    """Envoie un véritable e-mail et retourne son Message-ID en-tête."""
    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Génération d'un ID de message unique pour le protocole de messagerie
    domain = SMTP_EMAIL.split('@')[-1]
    msg_id = f"<{time.time()}--worker@{domain}>"
    msg['Message-ID'] = msg_id
    
    # 🔗 Correction : Utilisation du bon nom de variable (reply_to_id) pour lier le fil
    if reply_to_id:
        msg['In-Reply-To'] = reply_to_id
        msg['References'] = reply_to_id

    msg.attach(MIMEText(body_content, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        return msg_id
    except Exception as e:
        print(f"❌ Erreur d'envoi SMTP : {e}")
        return None

def generer_un_email():
    template = random.choice(SUJETS_ET_CORPS)
    expediteur = random.choice(EXPEDITEURS)
    
    inclure_pj = random.choice([True, False])
    nom_pj = None
    if inclure_pj:
        pj_choisie = random.choice(PIECES_JOINTES_TYPES)
        nom_pj = f"{random.randint(100,999)}_{pj_choisie['nom']}"
        chemin_pj = os.path.join(ATTACHMENTS_DIR, nom_pj)
        with open(chemin_pj, "w", encoding="utf-8") as f:
            f.write(pj_choisie["contenu"])
    
    id_email = f"mail_{random.randint(1000, 9999)}"
    email_data = {
        "id_email": id_email,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expediteur": expediteur,
        "sujet": template["sujet"],
        "corps": template["corps"],
        "categorie_metier": template["categorie"],
        "piece_jointe_associee": nom_pj
    }
    
    chemin_email = os.path.join(EMAILS_DIR, f"{id_email}.json")
    with open(chemin_email, "w", encoding="utf-8") as f:
        json.dump(email_data, f, indent=4, ensure_ascii=False)
        
    return email_data

# --- BOUCLE PRINCIPALE DU WORKER ---
print("🚀 Lancement du Worker connecté à PostgreSQL et Gmail...")
time.sleep(5) # Laisse le temps à la BDD de démarrer au premier lancement

try:
    while True:
        # 1. On génère notre e-mail de simulation
        mail = generer_un_email()
        custom_id = mail['id_email']
        
        # 2. Sécurité Anti-Doublon (Tâche 11)
        if email_already_processed(custom_id):
            print(f"⏭️ E-mail {custom_id} déjà présent en BDD. Ignoré.")
            continue
            
        print(f"\n📬 Nouvel e-mail généré localement : {custom_id}")
        
        # 3. Envoi du mail Initial à TA boîte mail de test (Tâche 10)
        corps_complet = f"Provenance simulée: {mail['expediteur']}\n\n{mail['corps']}"
        print(f"📤 Envoi de l'e-mail initial vers {SMTP_EMAIL}...")
        
        id_initial = send_smtp_email(SMTP_EMAIL, mail['sujet'], corps_complet)
        
        if id_initial:
            log_email_status(custom_id, SMTP_EMAIL, "sent")
            print(f"✅ E-mail initial envoyé avec succès !")
            
            time.sleep(2) # Pause de sécurité
            
            # 4. Envoi de la réponse (Reply) dans le même fil (Tâche 12)
            sujet_reply = f"Re: {mail['sujet']}"
            corps_reply = "Bonjour,\n\nCeci est le suivi automatique du Worker pour simuler un échange continu.\n\nCordialement."
            print("🔄 Envoi de la réponse chaînée (Reply)...")
            
            id_reply = send_smtp_email(SMTP_EMAIL, sujet_reply, corps_reply, reply_to_id=id_initial)
            
            if id_reply:
                log_email_status(custom_id, SMTP_EMAIL, "replied")
                print("🏁 Fil de discussion (Mail + Reply) validé en BDD !")

        # 5. Cadence imposée par le tuteur : 1 minute (Tâche 10)
        print("⏳ En attente de la prochaine exécution du Worker (60 secondes)...")
        time.sleep(60)

except KeyboardInterrupt:
    print("\n🛑 Worker arrêté proprement.")