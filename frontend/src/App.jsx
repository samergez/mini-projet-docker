import React, { useState } from 'react';
import './App.css';

function App() {
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
    
    // On met à jour l'historique local incluant le nouveau message de l'utilisateur
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
          history: updatedMessages // <-- Envoie l'historique complet pour que le backend se souvienne du contexte
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
  );
}

export default App;