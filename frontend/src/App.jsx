import React, { useState } from 'react';
import './App.css';
import EmailDashboard from './EmailDashboard';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');

  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Bonjour ! Comment puis-je vous aider avec vos e-mails ?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');
    
    const updatedMessages = [...messages, { sender: 'user', text: userMessage }];
    setMessages(updatedMessages);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          prompt: userMessage, 
          history: updatedMessages 
        }),
      });

      const data = await response.json();
      const botReply = data.response || data.message || "Réponse reçue du serveur.";

      setMessages((prev) => [...prev, { sender: 'bot', text: botReply }]);
    } catch (error) {
      console.error("Erreur de connexion:", error);
      setMessages((prev) => [...prev, { sender: 'bot', text: "Désolé, impossible de contacter le serveur." }]);
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
          <h2>Assistant E-mails RAG</h2>
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