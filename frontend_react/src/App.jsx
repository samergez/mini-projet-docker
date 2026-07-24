import React, { useState, useEffect } from 'react';

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [newTaskText, setNewTaskText] = useState('');
  const [message, setMessage] = useState('Chargement...');

  // Charger les tâches depuis Django au démarrage
  useEffect(() => {
    fetch('http://localhost:8001/api/todos/')
      .then(res => res.json())
      .then(data => {
        setMessage(data.message);
        setTasks(data.tasks);
      })
      .catch(err => console.error("Erreur de connexion :", err));
  }, []);

  // Ajouter une tâche via l'API Django
  const addTask = (e) => {
    e.preventDefault();
    if (!newTaskText.trim()) return;

    fetch('http://localhost:8001/api/todos/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: newTaskText })
    })
      .then(res => res.json())
      .then(data => {
        if (data.task) {
          setTasks([...tasks, data.task]);
          setNewTaskText('');
        }
      })
      .catch(err => console.error("Erreur lors de l'ajout :", err));
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial', maxWidth: '600px', margin: 'auto' }}>
      <h1>🚀 Ma To-Do List Fullstack (Docker)</h1>
      <p style={{ color: 'green', fontWeight: 'bold' }}>{message}</p>

      {/* Formulaire d'ajout */}
      <form onSubmit={addTask} style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={newTaskText}
          onChange={(e) => setNewTaskText(e.target.value)}
          placeholder="Ajouter une nouvelle tâche..."
          style={{ padding: '10px', flex: 1, fontSize: '16px' }}
        />
        <button type="submit" style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}>
          Ajouter
        </button>
      </form>

      {/* Liste des tâches */}
      <h3>Liste des tâches :</h3>
      <ul style={{ lineHeight: '1.8', fontSize: '18px' }}>
        {tasks.map((task) => (
          <li key={task.id}>{task.text}</li>
        ))}
      </ul>
    </div>
  );
}