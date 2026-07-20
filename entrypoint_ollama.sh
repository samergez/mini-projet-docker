#!/bin/bash

# Démarrer le serveur Ollama en tâche de fond
ollama serve &

# Attendre que le serveur Ollama réponde (on teste le port 11434)
echo "⏳ Attente du démarrage du serveur Ollama..."
while ! curl -s http://localhost:11434 > /dev/null; do
    sleep 2
done

echo "✅ Serveur Ollama démarré !"

# Télécharger automatiquement le modèle d'embedding (274 Mo)
echo "📥 Téléchargement du modèle nomic-embed-text..."
ollama pull nomic-embed-text

echo "🎉 Modèle nomic-embed-text prêt à l'usage !"

# Garder Ollama actif au premier plan
wait