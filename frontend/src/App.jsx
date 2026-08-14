import React, { useState } from 'react';
import './App.css';
import EmailDashboard from './EmailDashboard';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedModel, setSelectedModel] = useState('llama-3.1-8b-instant');

  // Stocker l'historique des messages par modèle de manière indépendante
  const [chatHistories, setChatHistories] = useState({
    'llama-3.1-8b-instant': [
      { sender: 'bot', text: 'Bonjour ! Je suis Groq. Comment puis-je vous aider avec vos e-mails ?' }
    ],
    'glm-5.2': [
      { sender: 'bot', text: 'Bonjour ! Je suis GLM (5.2). Comment puis-je vous aider avec vos e-mails ?' }
    ]
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Récupérer les messages du modèle actuellement actif
  const messages = chatHistories[selectedModel] || [];

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');
    
    // Mettre à jour l'historique uniquement pour le modèle en cours
    const updatedMessages = [...messages, { sender: 'user', text: userMessage }];
    setChatHistories((prev) => ({
      ...prev,
      [selectedModel]: updatedMessages
    }));
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          prompt: userMessage, 
          history: updatedMessages,
          model_name: selectedModel
        }),
      });

      const data = await response.json();
      const botReply = data.response || data.message || "Réponse reçue du serveur.";

      // Ajouter la réponse du bot dans l'historique du modèle actif
      setChatHistories((prev) => ({
        ...prev,
        [selectedModel]: [...prev[selectedModel], { sender: 'bot', text: botReply }]
      }));
    } catch (error) {
      console.error("Erreur de connexion:", error);
      setChatHistories((prev) => ({
        ...prev,
        [selectedModel]: [...prev[selectedModel], { sender: 'bot', text: "Désolé, impossible de contacter le serveur." }]
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Barre de navigation stylisée avec le thème */}
      <nav style={{ display: 'flex', justifyContent: 'center', gap: '10px', padding: '15px', background: '#2b2b2b', borderBottom: '1px solid #444' }}>
        <button 
          onClick={() => setCurrentView('dashboard')}
          style={{ 
            padding: '8px 16px', 
            cursor: 'pointer', 
            background: currentView === 'dashboard' ? '#8109E0' : '#444', 
            color: '#fff', 
            border: 'none', 
            borderRadius: '4px', 
            fontWeight: 'bold' 
          }}
        >
          Tableau de bord (Expéditeurs)
        </button>
        <button 
          onClick={() => setCurrentView('chat')}
          style={{ 
            padding: '8px 16px', 
            cursor: 'pointer', 
            background: currentView === 'chat' ? '#8109E0' : '#444', 
            color: '#fff', 
            border: 'none', 
            borderRadius: '4px', 
            fontWeight: 'bold' 
          }}
        >
          Assistant Chat RAG
        </button>
      </nav>

      {currentView === 'dashboard' ? (
        <EmailDashboard />
      ) : (
        <div className="chat-container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h2>Assistant E-mails RAG</h2>
            
            {/* Sélecteur de modèle d'IA */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label htmlFor="modelSelect" style={{ color: '#fff', fontSize: '14px' }}>Modèle :</label>
              <select 
                id="modelSelect"
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: '4px', background: '#333', color: '#fff', border: '1px solid #555' }}
              >
                <option value="llama-3.1-8b-instant">Groq (llama-3.1)</option>
                <option value="glm-5.2">GLM (5.2)</option>
              </select>
            </div>
          </div>

          <div className="messages-box">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender}`}>
                <span>{msg.text}</span>
              </div>
            ))}
            {loading && <div className="message bot"><em>L'agent réfléchit...</em></div>}
          </div>

          <form onSubmit={sendMessage} className="chat-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Posez votre question ici..."
            />
            <button type="submit">Envoyer</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;