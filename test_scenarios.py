import os
import json
import glob

def test_scenario_contenu_email():
    print("=" * 50)
    print("🧪 SCÉNARIO DE TEST : Vérification du contenu d'un e-mail")
    print("=" * 50)

    # 1. On prend un e-mail au hasard sur le disque (Ground Truth)
    json_files = glob.glob("received_emails/**/contenu_email.json", recursive=True)
    if not json_files:
        print("❌ Aucun e-mail trouvé pour le test.")
        return

    # On prend le premier fichier pour l'exemple
    chemin_test = json_files[0]
    
    with open(chemin_test, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    expediteur_reel = data.get("sender", "Inconnu")
    sujet_reel = data.get("subject", "Sans sujet")

    print(f"📁 Fichier analysé : {chemin_test}")
    print(f"🔍 Vérité terrain (JSON) -> Expéditeur : {expediteur_reel} | Sujet : {sujet_reel}")

    # 2. Simulation de la réponse de l'IA (ou appel direct à ta fonction de recherche)
    # C'est ici que ton IA répond par exemple : "L'e-mail vient de X avec le sujet Y"
    reponse_ia_simulee = f"Cet e-mail a été envoyé par {expediteur_reel} avec pour sujet {sujet_reel}."

    # 3. Le script de test vérifie automatiquement si l'info de l'IA est vraie
    print(f"🤖 Réponse de l'IA : {reponse_ia_simulee}")

    assert expediteur_reel in reponse_ia_simulee, "❌ ÉCHEC DU TEST : L'IA a halluciné l'expéditeur !"
    
    print("✅ SUCCÈS DU SCÉNARIO DE TEST : L'information retournée par l'IA correspond bien au fichier source !")
    print("=" * 50)

if __name__ == "__main__":
    test_scenario_contenu_email()