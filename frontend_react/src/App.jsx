import React, { useState, useEffect } from 'react';

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [newTaskText, setNewTaskText] = useState('');
  const [message, setMessage] = useState('');

  // États pour l'authentification
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [authMessage, setAuthMessage] = useState('');

  // États pour l'édition de tâche
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState('');

  // Charger le profil et les tâches au démarrage
  useEffect(() => {
    fetch('http://localhost:8001/api/profile/', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setUser(data.user);
          // Si connecté, on charge ses tâches
          fetchTasks();
        } else {
          setMessage("Veuillez vous connecter pour voir vos tâches.");
        }
      })
      .catch(() => {
        setUser(null);
        setMessage("Veuillez vous connecter pour voir vos tâches.");
      });
  }, []);

  const fetchTasks = () => {
    fetch('http://localhost:8001/api/todos/', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.tasks) {
          setMessage(data.message);
          setTasks(data.tasks);
        }
      })
      .catch(err => console.error("Erreur chargement tâches :", err));
  };

  // Connexion / Inscription
  const handleAuth = (e) => {
    e.preventDefault();
    const endpoint = authMode === 'login' ? 'login' : 'register';

    fetch(`http://localhost:8001/api/${endpoint}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: usernameInput, password: passwordInput }),
      credentials: 'include'
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          if (authMode === 'login') {
            window.location.reload();
          } else {
            setAuthMode('login');
            setAuthMessage("Inscription réussie, connectez-vous !");
            setPasswordInput('');
          }
        } else {
          setAuthMessage(data.error || "Une erreur est survenue");
        }
      })
      .catch(() => setAuthMessage("Erreur réseau"));
  };

  // Déconnexion
  const handleLogout = () => {
    fetch('http://localhost:8001/api/logout/', {
      method: 'POST',
      credentials: 'include'
    })
      .then(() => {
        window.location.reload();
      });
  };

  // Ajouter une tâche
  const addTask = (e) => {
    e.preventDefault();
    if (!newTaskText.trim()) return;

    fetch('http://localhost:8001/api/todos/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: newTaskText }),
      credentials: 'include'
    })
      .then(res => res.json())
      .then(data => {
        if (data.task) {
          setTasks([...tasks, data.task]);
          setNewTaskText('');
        }
      });
  };

  // Supprimer une tâche
  const deleteTask = (id) => {
    fetch(`http://localhost:8001/api/todos/${id}/`, {
      method: 'DELETE',
      credentials: 'include'
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setTasks(tasks.filter(task => task.id !== id));
        }
      });
  };

  // Modifier une tâche
  const updateTask = (id) => {
    if (!editText.trim()) return;

    fetch(`http://localhost:8001/api/todos/${id}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: editText }),
      credentials: 'include'
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setTasks(tasks.map(task => task.id === id ? { ...task, text: editText } : task));
          setEditingId(null);
          setEditText('');
        }
      });
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial', maxWidth: '600px', margin: 'auto' }}>
      <h1>🚀 Application Fullstack (JWT & Cookies)</h1>
      <p style={{ color: user ? 'green' : 'orange', fontWeight: 'bold' }}>{message}</p>

      {/* --- BLOC AUTHENTIFICATION --- */}
      <div style={{ background: '#f4f4f4', padding: '20px', borderRadius: '8px', marginBottom: '30px' }}>
        {user ? (
          <div>
            <p>Connecté en tant que : <strong>{user.username}</strong></p>
            <button onClick={handleLogout} style={{ padding: '8px 15px', backgroundColor: '#d9534f', color: 'white', border: 'none', cursor: 'pointer' }}>
              Se déconnecter
            </button>
          </div>
        ) : (
          <div>
            <h3>{authMode === 'login' ? 'Connexion' : 'Inscription'}</h3>
            {authMessage && <p style={{ color: 'red' }}>{authMessage}</p>}
            <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <input
                type="text"
                placeholder="Nom d'utilisateur"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                style={{ padding: '8px' }}
              />
              <input
                type="password"
                placeholder="Mot de passe"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                style={{ padding: '8px' }}
              />
              <button type="submit" style={{ padding: '10px', backgroundColor: '#007BFF', color: 'white', border: 'none', cursor: 'pointer' }}>
                {authMode === 'login' ? 'Se connecter' : 'S\'inscrire'}
              </button>
            </form>
            <p style={{ marginTop: '10px', fontSize: '14px' }}>
              {authMode === 'login' ? 'Pas encore de compte ? ' : 'Déjà un compte ? '}
              <span
                style={{ color: 'blue', cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
              >
                {authMode === 'login' ? 'Créer un compte' : 'Se connecter'}
              </span>
            </p>
          </div>
        )}
      </div>

      {/* --- TO-DO LIST (Visible uniquement si connecté) --- */}
      {user && (
        <>
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

          <h3>Liste de tes tâches :</h3>
          <ul style={{ lineHeight: '1.8', fontSize: '18px', paddingLeft: '20px' }}>
            {tasks.map((task) => (
              <li key={task.id} style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                {editingId === task.id ? (
                  <div style={{ display: 'flex', gap: '10px', flex: 1, marginRight: '10px' }}>
                    <input
                      type="text"
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      style={{ padding: '5px', flex: 1 }}
                    />
                    <button onClick={() => updateTask(task.id)} style={{ padding: '5px 10px', cursor: 'pointer' }}>Enregistrer</button>
                    <button onClick={() => setEditingId(null)} style={{ padding: '5px 10px', cursor: 'pointer' }}>Annuler</button>
                  </div>
                ) : (
                  <>
                    <span style={{ flex: 1 }}>{task.text}</span>
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <button onClick={() => { setEditingId(task.id); setEditText(task.text); }} style={{ padding: '5px 10px', cursor: 'pointer' }}>Modifier</button>
                      <button onClick={() => deleteTask(task.id)} style={{ padding: '5px 10px', cursor: 'pointer', backgroundColor: '#ff4d4d', color: 'white', border: 'none' }}>Supprimer</button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}