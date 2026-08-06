import React, { useState, useEffect } from 'react';
import SenderDetail from './SenderDetail'; // Import de la vue détaillée

const EmailDashboard = () => {
    const [sendersData, setSendersData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSender, setSelectedSender] = useState(null); // État pour stocker l'expéditeur cliqué

    useEffect(() => {
        fetch('http://localhost:8000/api/emails/filter/')
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Erreur lors de la récupération des e-mails");
                }
                return response.json();
            })
            .then((data) => {
                if (data.status === "success") {
                    const counts = {};
                    data.data.forEach((email) => {
                        let sender = email.sender ? email.sender.trim() : "Inconnu";
                        const normalizedSender = sender.toLowerCase();
                        
                        if (!counts[normalizedSender]) {
                            counts[normalizedSender] = { originalName: sender, count: 0 };
                        }
                        counts[normalizedSender].count += 1;
                    });

                    const formattedSenders = Object.values(counts).map((item) => ({
                        name: item.originalName,
                        count: item.count,
                    }));

                    setSendersData(formattedSenders);
                }
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    // Si un expéditeur est sélectionné, on affiche sa page de détails à la place de la liste
    if (selectedSender) {
        return <SenderDetail senderName={selectedSender} onBack={() => setSelectedSender(null)} />;
    }

    if (loading) return <div style={{ padding: '20px', textAlign: 'center', color: '#fff' }}>Chargement du dashboard...</div>;
    if (error) return <div style={{ padding: '20px', textAlign: 'center', color: '#ff6b6b' }}>Erreur : {error}</div>;

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
            <h1 style={{ fontSize: '24px', marginBottom: '10px', color: '#fff' }}>Tableau de bord - Expéditeurs d'e-mails</h1>
            <p style={{ color: '#bbb', marginBottom: '20px' }}>Liste unique des personnes ayant envoyé des e-mails avec statistiques. Cliquez sur un nom pour voir ses e-mails.</p>
            
            <ul style={{ listStyle: 'none', padding: 0, background: '#2b2b2b', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.3)', border: '1px solid #444' }}>
                {sendersData.map((sender, index) => (
                    <li 
                        key={index}
                        onClick={() => setSelectedSender(sender.name)} // Enregistre l'expéditeur cliqué
                        style={{ 
                            padding: '15px 20px', 
                            borderBottom: index < sendersData.length - 1 ? '1px solid #444' : 'none',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            transition: 'background 0.2s',
                            color: '#fff'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = '#383838'}
                        onMouseLeave={(e) => e.currentTarget.style.background = '#2b2b2b'}
                    >
                        <span style={{ fontWeight: '500' }}>{sender.name}</span>
                        <span style={{ background: '#8109E0', color: '#ffffff', padding: '4px 12px', borderRadius: '12px', fontSize: '14px', fontWeight: 'bold' }}>
                            {sender.count} e-mail{sender.count > 1 ? 's' : ''}
                        </span>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default EmailDashboard;