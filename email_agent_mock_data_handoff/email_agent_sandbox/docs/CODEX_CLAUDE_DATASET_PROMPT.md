# Prompt for Codex / Claude Code / Cursor

Use this prompt inside the repository.

---

You are working inside an email-agent sandbox repository. Expand the static Option A dataset to around 1,000 cohesive fake emails.

Hard constraints:

1. Do not use any real company, client, supplier, person, project, or government case name.
2. Do not use names from private context, memory, past chats, or real customer history.
3. Do not use the supervising company name or its real customers.
4. All entities must be fictional and use reserved fake domains like `example.test`.
5. Keep Option A: every email has final full `body_text`. Do not create mail blocks. Do not require runtime LLM generation.
6. Every attachment referenced by JSON must exist under `dataset/attachments/...`.
7. Include hidden `ground_truth` for each message.
8. Keep threads cohesive and avoid contradictions.

Target:

- around 1,000 messages;
- around 80 to 120 threads;
- average 8 to 12 messages per business thread;
- 25% to 35% of messages with attachments;
- mix French, English, and some bilingual business emails.

Categories to use: `client_request`, `client_reply`, `client_offer`, `supplier_rfq`, `supplier_offer`, `supplier_delay`, `supplier_invoice`, `internal`, `accounting`, `tax`, `customs`, `shipment`, `delivery`, `support`, `bank`, `admin_notice`, `noise`.

Scenario types:

- client quotation request for fictional industrial solution;
- supplier RFQ and offer;
- internal estimation and validation;
- discount negotiation and order confirmation;
- supplier delay and client update;
- shipment tracking and delivery note;
- import/export document issue with fictional customs-style office;
- accounting monthly close and invoice verification;
- bank payment confirmation;
- support ticket with screenshot or service report;
- low-priority notices and newsletters.

Tasks:

1. Read `dataset/emails_dataset.json`, `companies.json`, `contacts.json`, and `projects.json`.
2. Add more fictional entities.
3. Expand `dataset/emails_dataset.json` to around 1,000 messages.
4. Keep messages sorted by `send_after_minutes`.
5. Ensure unique `message_id`.
6. Ensure every `reply_to_message_id` refers to an earlier message in the same thread.
7. Create placeholder attachment files when needed.
8. Run `python tools/validate_dataset.py` and fix errors.
9. Update `dataset_info.total_threads` and `dataset_info.total_messages`.

Quality rules: make emails realistic but synthetic, add amounts/dates/references/deadlines, vary phrasing, use signatures, and keep contact identities consistent.

Final deliverable: valid JSON dataset, all referenced attachments present, validator passes, no real entities or private data.

---
