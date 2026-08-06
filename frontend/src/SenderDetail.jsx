import React, { useState, useEffect } from 'react';

const SenderDetail = ({ senderName, onBack }) => {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // États pour les filtres de date ("de" et "à")
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    // Fonction pour récupérer les e-mails avec les filtres de date optionnels
    const fetchEmails = () => {
        setLoading(true);
        let url = `http://localhost:8000/api/emails/filter/?name=${encodeURIComponent(senderName)}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;

        fetch(url)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Erreur lors de la récupération des e-mails.");
                }
                return response.json();
            })
            .then((data) => {
                if (data.status === "success") {
                    setEmails(data.data);
                }
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    };

    // Chargement initial au montage ou quand l'expéditeur change
    useEffect(() => {
        fetchEmails();
    }, [senderName]);

    // Déclenchement de la recherche par date lors du clic sur le bouton de filtre
    const handleFilterSubmit = (e) => {
        e.preventDefault();
        fetchEmails();
    };

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif', color: '#fff' }}>
            <button 
                onClick={onBack}
                style={{ 
                    padding: '8px 16px', 
                    marginBottom: '20px', 
                    background: '#444', 
                    color: '#fff', 
                    border: 'none', 
                    borderRadius: '4px', 
                    cursor: 'pointer',
                    fontWeight: 'bold'
                }}
            >
                ← Retour au tableau de bord
            </button>

            <h1 style={{ fontSize: '22px', marginBottom: '5px' }}>E-mails de : {senderName}</h1>
            <p style={{ color: '#bbb', marginBottom: '20px' }}>Total : {emails.length} e-mail(s) trouvé(s)</p>

            {/* Formulaire de filtre par date ("de" et "à") */}
            <form onSubmit={handleFilterSubmit} style={{ display: 'flex', gap: '15px', alignItems: 'center', background: '#2b2b2b', padding: '15px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #444' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <label style={{ fontSize: '12px', color: '#aaa' }}>Date de début :</label>
                    <input 
                        type="date" 
                        value={dateFrom} 
                        onChange={(e) => setDateFrom(e.target.value)}
                        style={{ padding: '6px', background: '#1e1e1e', color: '#fff', border: '1px solid #555', borderRadius: '4px' }}
                    />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <label style={{ fontSize: '12px', color: '#aaa' }}>Date de fin :</label>
                    <input 
                        type="date" 
                        value={dateTo} 
                        onChange={(e) => setDateTo(e.target.value)}
                        style={{ padding: '6px', background: '#1e1e1e', color: '#fff', border: '1px solid #555', borderRadius: '4px' }}
                    />
                </div>
                <button 
                    type="submit"
                    style={{ 
                        marginTop: '18px',
                        padding: '8px 16px', 
                        background: '#8109E0', 
                        color: '#fff', 
                        border: 'none', 
                        borderRadius: '4px', 
                        cursor: 'pointer',
                        fontWeight: 'bold'
                    }}
                >
                    Filtrer
                </button>
            </form>

            {loading ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#fff' }}>Chargement des e-mails...</div>
            ) : error ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#ff6b6b' }}>Erreur : {error}</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    {emails.map((email, index) => (
                        <div 
                            key={index} 
                            style={{ 
                                background: '#2b2b2b', 
                                padding: '15px', 
                                borderRadius: '8px', 
                                border: '1px solid #444',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px', color: '#aaa' }}>
                                <span><strong>Date :</strong> {email.date || 'Inconnue'}</span>
                                <span><strong>ID :</strong> {email.email_id || 'N/A'}</span>
                            </div>
                            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#fff' }}>
                                {email.subject || 'Pas de sujet'}
                            </h3>
                            <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#ddd', whiteSpace: 'pre-line' }}>
                                {email.content || 'Aucun contenu'}
                            </p>

                            {/* Pièces jointes */}
                            {email.attachments && Array.isArray(email.attachments) && email.attachments.length > 0 && (
                                <div style={{ marginTop: '12px', padding: '10px', background: '#1e1e1e', borderRadius: '6px', border: '1px solid #444' }}>
                                    <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#8109E0', display: 'block', marginBottom: '6px' }}>
                                        📎 Pièces jointes ({email.attachments.length}) :
                                    </span>
                                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#ccc' }}>
                                        {email.attachments.map((att, attIndex) => {
                                            let attName = typeof att === 'string' ? att : (att.filename || att.name || JSON.stringify(att));
                                            return (
                                                <li key={attIndex} style={{ marginBottom: '4px' }}>
                                                    <span style={{ color: '#fff' }}>{attName}</span>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SenderDetail;