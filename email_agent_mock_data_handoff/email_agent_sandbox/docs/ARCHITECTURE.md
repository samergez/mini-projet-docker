# Architecture

```text
Static JSON dataset -> Python periodic worker -> Sandbox Gmail mailbox -> Intern email agent app
```

The dataset contains final email text. The worker only schedules, attaches files, sends/imports messages, and saves state. It does not generate content and does not call an LLM.

Recommended mode: `gmail-api-import`, because it preserves fake sender/receiver headers inside the Gmail sandbox.
