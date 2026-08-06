import React, { useState, useEffect } from 'react';

const SenderDetail = ({ senderName, onBack }) => {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const encodedName = encodeURIComponent(senderName);
        fetch(`http://localhost:8000/api/emails/filter/?name=${encodedName}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Erreur lors de la récupération des e-mails de cet expéditeur.");
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
    }, [senderName]);

    if (loading) return <div style={{ padding: '20px', textAlign: 'center', color: '#fff' }}>Chargement des e-mails de {senderName}...</div>;
    if (error) return <div style={{ padding: '20px', textAlign: 'center', color: '#ff6b6b' }}>Erreur : {error}</div>;

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

                        {/* Affichage robuste et stylisé des pièces jointes */}
                        {email.attachments && Array.isArray(email.attachments) && email.attachments.length > 0 && (
                            <div style={{ marginTop: '12px', padding: '10px', background: '#1e1e1e', borderRadius: '6px', border: '1px solid #444' }}>
                                <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#8109E0', display: 'block', marginBottom: '6px' }}>
                                    📎 Pièces jointes ({email.attachments.length}) :
                                </span>
                                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#ccc' }}>
                                    {email.attachments.map((att, attIndex) => {
                                        // Gère le cas où l'attachement est une chaîne ou un objet
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
        </div>
    );
};

export default SenderDetail;