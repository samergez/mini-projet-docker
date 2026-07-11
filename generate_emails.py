import os
import time
import random
import json
from datetime import datetime

# Configuration des dossiers
EMAILS_DIR = "./data/emails"
ATTACHMENTS_DIR = "./data/attachments"

# On s'assure que les dossiers existent sur ton PC
os.makedirs(EMAILS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Listes de données pour simuler des e-mails professionnels réalistes
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
        "corps": "Bonjour,\n\nNous aimerions intégrer un agent intelligent capable de trier et de répondre à nos e-mails clients automatiquement. Pouvez-vous nous envoyer vos tarifs et vos disponibilités pour une réunion technique la semaine prochaine ?\n\nMerci d'avance,\nResponsable Innovation."
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

def generer_un_email():
    # Sélection aléatoire des données
    template = random.choice(SUJETS_ET_CORPS)
    expediteur = random.choice(EXPEDITEURS)
    
    # Décider s'il y a une pièce jointe (1 chance sur 2)
    inclure_pj = random.choice([True, False])
    nom_pj = None
    
    if inclure_pj:
        pj_choisie = random.choice(PIECES_JOINTES_TYPES)
        nom_pj = f"{random.randint(100,999)}_{pj_choisie['nom']}"
        
        # On crée physiquement le faux fichier sur le PC pour simuler la pièce jointe
        chemin_pj = os.path.join(ATTACHMENTS_DIR, nom_pj)
        with open(chemin_pj, "w", encoding="utf-8") as f:
            f.write(pj_choisie["contenu"])
    
    # Structure de l'e-mail au format JSON requis
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
    
    # Sauvegarde de l'e-mail sous forme de fichier JSON
    chemin_email = os.path.join(EMAILS_DIR, f"{id_email}.json")
    with open(chemin_email, "w", encoding="utf-8") as f:
        json.dump(email_data, f, indent=4, ensure_ascii=False)
        
    return email_data

print("🚀 Lancement du simulateur d'e-mails professionnels...")
print(f"📁 Les e-mails seront stockés dans : {EMAILS_DIR}")
print(f"📁 Les pièces jointes seront stockées dans : {ATTACHMENTS_DIR}\n")

try:
    while True:
        mail = generer_un_email()
        print(f"📬 [{mail['timestamp']}] Nouvel e-mail de <{mail['expediteur']}> généré avec succès !")
        if mail['piece_jointe_associee']:
            print(f"📎 Pièce jointe créée : {mail['piece_jointe_associee']}")
        
        # Ton encadrant a dit toutes les 7 minutes (420 secondes)
        # Pour nos tests actuels, on met 15 secondes pour voir le script travailler !
        print("⏳ En attente du prochain e-mail (15 secondes)...")
        time.sleep(15)

except KeyboardInterrupt:
    print("\n🛑 Simulateur arrêté proprement.")