-- init-db/init.sql
CREATE TABLE IF NOT EXISTS processed_emails (
    id SERIAL PRIMARY KEY,
    custom_message_id VARCHAR(255) UNIQUE NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    replied_at TIMESTAMP
);