import os
import glob

def verifier_dossier_emails(dossier_base="received_emails"):
    print("=" * 50)
    print("🔍 LANCEMENT DU SCRIPT DE VÉRIFICATION (GROUND TRUTH)")
    print("=" * 50)

    if not os.path.exists(dossier_base):
        print(f"❌ Erreur : Le dossier '{dossier_base}' est introuvable à cet endroit.")
        return

    # Recherche de tous les fichiers JSON de contenu d'e-mail
    json_files = glob.glob(os.path.join(dossier_base, "**/contenu_email.json"), recursive=True)
    total_emails = len(json_files)

    # Recherche de tous les fichiers PDF dans les sous-dossiers
    pdf_files = glob.glob(os.path.join(dossier_base, "**/*.pdf"), recursive=True)
    total_pdfs = len(pdf_files)

    print(f"📊 Résultats du comptage réel sur le disque :")
    print(f"   - Nombre total d'e-mails (contenu_email.json) : {total_emails}")
    print(f"   - Nombre total de fichiers PDF joints : {total_pdfs}")
    print("=" * 50)
    print("💡 Conseil : Compare ces chiffres avec la réponse de ton IA pour valider ton test.")

if __name__ == "__main__":
    verifier_dossier_emails()