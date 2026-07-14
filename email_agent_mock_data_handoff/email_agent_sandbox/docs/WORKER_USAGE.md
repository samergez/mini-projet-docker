# Worker Usage

Install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Validate:

```bash
python tools/validate_dataset.py
```

Dry run:

```bash
python worker/email_worker.py --mode dry-run --once
```

Mark dry-run messages as sent:

```bash
python worker/email_worker.py --mode dry-run --once --mark-dry-run-sent
```

Speed example: `--speed-multiplier 1440` means one simulated day passes in one real minute.

SMTP mode is simple but less realistic. Gmail API import mode is recommended for realistic fake senders.
