-- init-db/init.sql

CREATE TABLE IF NOT EXISTS processed_emails (
    id SERIAL PRIMARY KEY,
    custom_message_id VARCHAR(255) UNIQUE NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    replied_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_attachments (
    attachment_id VARCHAR(50) PRIMARY KEY,
    email_id VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_text TEXT
);

INSERT INTO email_attachments (attachment_id, email_id, filename, content_text)
VALUES 
    ('ATT-01', 'MSG-101', 'Devis_Orion_QT159.pdf', 'Contenu du devis en pièce jointe PDF'),
    ('ATT-02', 'MSG-102', 'Rapport_Mensuel.pdf', 'Compte rendu des activités du mois'),
    ('ATT-03', 'MSG-103', 'Facture_F2026_09.pdf', 'Facture de prestation de service')
ON CONFLICT (attachment_id) DO NOTHING;