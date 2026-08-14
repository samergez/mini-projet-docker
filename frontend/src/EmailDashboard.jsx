import React, { useState, useEffect } from 'react';
import SenderDetail from './SenderDetail';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

const EmailDashboard = () => {
    const [sendersData, setSendersData] = useState([]);
    const [projectsData, setProjectsData] = useState([]);
    const [clientsData, setClientsData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSender, setSelectedSender] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Récupération des expéditeurs
                const resSenders = await fetch('http://localhost:8000/api/emails/filter/');
                if (!resSenders.ok) throw new Error("Erreur lors de la récupération des e-mails");
                const dataSenders = await resSenders.json();

                if (dataSenders.status === "success") {
                    const counts = {};
                    dataSenders.data.forEach((email) => {
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

                // 2. Récupération des projets en JSON avec GLM
                const resProjects = await fetch('http://127.0.0.1:8000/api/extract-projects/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model_name: 'glm-5.2' })
                });
                const dataProjects = await resProjects.json();
                if (dataProjects.status === 'success' && dataProjects.data.projects) {
                    setProjectsData(dataProjects.data.projects);
                }

                // 3. Récupération des clients en JSON avec GLM
                const resClients = await fetch('http://127.0.0.1:8000/api/extract-clients/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model_name: 'glm-5.2' })
                });
                const dataClients = await resClients.json();
                if (dataClients.status === 'success' && dataClients.data.clients) {
                    setClientsData(dataClients.data.clients);
                }

            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (selectedSender) {
        return <SenderDetail senderName={selectedSender} onBack={() => setSelectedSender(null)} />;
    }

    if (loading) return <div style={{ padding: '20px', textAlign: 'center', color: '#fff' }}>Chargement du dashboard...</div>;
    if (error) return <div style={{ padding: '20px', textAlign: 'center', color: '#ff6b6b' }}>Erreur : {error}</div>;

    // Configuration des données pour Chart.js - Projets
    const projectLabels = projectsData.map(p => p.name);
    const projectCounts = projectsData.map(p => p.email_ids?.length || 0);

    const chartProjectsData = {
        labels: projectLabels,
        datasets: [{
            label: 'Nombre d\'e-mails',
            data: projectCounts,
            backgroundColor: ['#ff2222', '#2299ff', '#77cc77', '#ffdd66', '#ff88cc', '#aa44ff', '#ff8822'],
            borderRadius: 6,
        }],
    };

    // Configuration des données pour Chart.js - Clients
    const clientLabels = clientsData.map(c => c.name);
    const clientCounts = clientsData.map(c => c.email_ids?.length || 0);

    const chartClientsData = {
        labels: clientLabels,
        datasets: [{
            label: 'Nombre d\'e-mails',
            data: clientCounts,
            backgroundColor: ['#00D26A', '#2299ff', '#ffdd66', '#ff88cc', '#aa44ff', '#ff2222', '#ff8822'],
            borderRadius: 6,
        }],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    footer: (tooltipItems) => {
                        const index = tooltipItems[0].dataIndex;
                        const item = tooltipItems[0].chart.data.sourceData?.[index];
                        return item?.description ? `\nDescription: ${item.description}` : '';
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: { color: '#aaa', stepSize: 1 },
                grid: { color: '#444' }
            },
            x: {
                ticks: { color: '#fff', font: { size: 11 } },
                grid: { display: false }
            }
        }
    };

    // Injection des données sources dans l'objet chart pour les tooltips
    chartProjectsData.sourceData = projectsData;
    chartClientsData.sourceData = clientsData;

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
            <h1 style={{ fontSize: '24px', marginBottom: '10px', color: '#fff' }}>Tableau de bord - Expéditeurs d'e-mails</h1>
            <p style={{ color: '#bbb', marginBottom: '20px' }}>Liste unique des personnes ayant envoyé des e-mails avec statistiques. Cliquez sur un nom pour voir ses e-mails.</p>
            
            {/* Liste des expéditeurs */}
            <ul style={{ listStyle: 'none', padding: 0, background: '#2b2b2b', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.3)', border: '1px solid #444', marginBottom: '30px' }}>
                {sendersData.map((sender, index) => (
                    <li 
                        key={index}
                        onClick={() => setSelectedSender(sender.name)}
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

            {/* SECTION GRAPHIQUE 1 : Statistiques par Projet */}
            <div style={{ background: '#2b2b2b', padding: '20px', borderRadius: '8px', border: '1px solid #444', color: '#fff', marginBottom: '25px' }}>
                <h2 style={{ fontSize: '18px', marginBottom: '15px', borderBottom: '1px solid #444', paddingBottom: '8px' }}>
                    📊 Statistiques des e-mails par Projet
                </h2>
                {projectsData.length === 0 ? (
                    <p style={{ color: '#888', fontSize: '14px' }}>Aucun projet chargé.</p>
                ) : (
                    <div style={{ padding: '10px 0' }}>
                        <Bar data={chartProjectsData} options={chartOptions} />
                    </div>
                )}
            </div>

            {/* SECTION GRAPHIQUE 2 : Statistiques par Client */}
            <div style={{ background: '#2b2b2b', padding: '20px', borderRadius: '8px', border: '1px solid #444', color: '#fff' }}>
                <h2 style={{ fontSize: '18px', marginBottom: '15px', borderBottom: '1px solid #444', paddingBottom: '8px' }}>
                    📈 Statistiques des e-mails par Client
                </h2>
                {clientsData.length === 0 ? (
                    <p style={{ color: '#888', fontSize: '14px' }}>Aucun client chargé.</p>
                ) : (
                    <div style={{ padding: '10px 0' }}>
                        <Bar data={chartClientsData} options={chartOptions} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default EmailDashboard;