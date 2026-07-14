# Email Agent Intern Handoff

Clean handoff package for the email-agent sandbox.

## Contents

- `email_agent_sandbox/` - runnable sandbox project.
- `email_agent_internship_scope.md` - internship scope/context document.

## Dataset Status

- Final dataset: `email_agent_sandbox/dataset/emails_dataset.json`
- Total messages: 1000
- Total threads: 102
- Messages with attachments: 290

## Validation

From `email_agent_sandbox/`, run:

```bash
python3 tools/validate_dataset.py
python3 worker/email_worker.py --once --mode dry-run
```

The `state/` folder has been reset for a clean handoff.
