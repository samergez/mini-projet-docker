# Email Agent Sandbox - Static Option A

Starter package for an email-agent internship sandbox. It uses only fictional data and reserved `example.test` emails.

## Included

- `dataset/emails_dataset.json`: static full email bodies, threads, schedules, ground truth.
- `dataset/attachments/`: fake PDF/CSV/TXT/PNG attachments.
- `worker/email_worker.py`: periodic sender/importer. No runtime LLM.
- `tools/validate_dataset.py`: schema/file sanity check.
- `docs/`: architecture, schema, worker usage, Gmail setup, evaluation, and dataset-expansion prompt.

## First test

```bash
python tools/validate_dataset.py
python worker/email_worker.py --once --mode dry-run
```

## Best mode later

Use `gmail-api-import` for a realistic fake inbox with fake From/To headers. SMTP mode is easier but less realistic.
