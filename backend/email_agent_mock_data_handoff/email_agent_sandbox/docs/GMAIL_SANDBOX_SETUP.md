# Gmail Sandbox Setup

Use a dedicated sandbox Gmail account only.

## SMTP quick test

Create a Gmail app password, copy `.env.example` to `.env`, fill SMTP values, then run `--mode smtp`.

Limitation: Gmail SMTP will show the real Gmail account as sender unless aliases are configured.

## Gmail API import - recommended

Create a Google Cloud OAuth Desktop App for the sandbox account, download `client_secret.json`, put it in `credentials/client_secret.json`, install requirements, then run:

```bash
python worker/email_worker.py --mode gmail-api-import --once
```

Use only the sandbox Gmail account during OAuth.
