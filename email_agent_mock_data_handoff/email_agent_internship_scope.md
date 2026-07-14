# Email Agent Internship – Scope and Responsibilities

## Objective

The internship subject is to build an **Email Agent App** using a fake Gmail sandbox mailbox.

The goal is to avoid using any real company mailbox, real client emails, real suppliers, real invoices, or confidential data during development.

The sandbox mailbox will be populated with fake but realistic business emails generated from a static JSON dataset.

---

## Global Architecture

```text
1000 fake emails in JSON
        ↓
Python worker
        ↓
Periodic import/send to Gmail sandbox
        ↓
Intern Email Agent App
        ↓
Classification, summaries, action extraction, attachment analysis, draft replies
```

The system is intentionally split into two parts:

1. **Dataset preparation**, done before the internship.
2. **Email Agent App development**, done by the intern.

---

## Supervisor Responsibility

The supervisor's responsibility is only to prepare the fake dataset.

### Supervisor will provide

- A static JSON dataset containing around **1000 fake emails**.
- Fake contacts, fake companies, fake projects, and fake business threads.
- Fake attachment references.
- Fake PDF, Excel, Word, image, or text attachments.
- Hidden ground truth for evaluation.
- Documentation explaining the dataset structure.

### Supervisor will not provide

- Real mailbox access.
- Real client emails.
- Real supplier emails.
- Real invoices.
- Real customs documents.
- Real company confidential data.
- Real production OAuth credentials.

---

## Intern Responsibility

The intern will build the app that consumes the fake Gmail mailbox.

The intern is responsible for:

- Setting up Gmail API access for the sandbox Gmail account.
- Running or improving the Python worker.
- Importing/sending fake emails periodically to the sandbox Gmail inbox.
- Reading emails from Gmail using Gmail API.
- Reading attachments from Gmail.
- Building the Email Agent App.
- Classifying emails.
- Summarizing email threads.
- Extracting action items.
- Detecting urgent emails.
- Extracting entities such as company, project, amount, deadline, invoice number, shipment reference, and responsible person.
- Summarizing attachments.
- Generating suggested draft replies.
- Building a simple dashboard.
- Comparing agent output with the hidden ground truth.

---

## Recommended Simple Option A

The selected approach is **Option A: full emails already generated in JSON**.

This means the JSON contains the final email body exactly as it should appear in Gmail.

The Python worker does not generate email content.

The worker only reads the JSON and sends/imports emails one by one.

```text
emails_dataset.json
        ↓
worker reads next unsent email
        ↓
worker sends/imports it to Gmail
        ↓
worker marks it as sent
```

This keeps the system simple and avoids creating another LLM-based simulator.

---

## Dataset Design

The dataset should be thread-based, not only a flat list of disconnected emails.

Recommended structure:

```text
dataset/
├── emails_dataset.json
├── attachments/
│   ├── pdf/
│   ├── excel/
│   ├── word/
│   ├── images/
│   └── txt/
└── docs/
```

Each thread should contain a cohesive business conversation.

Example thread types:

- Client quotation request.
- Supplier offer follow-up.
- Internal team project discussion.
- Accounting invoice follow-up.
- Government or tax administration request.
- Customs clearance issue.
- Import/export shipment tracking.
- Technical support incident.
- Payment reminder.
- Meeting report follow-up.

---

## Email JSON Fields

Each email should contain at least:

```text
message_id
thread_id
message_order
send_offset_minutes
from
to
cc
subject
body
language
priority
labels
attachments
requires_action
expected_action
ground_truth
```

The `send_offset_minutes` field allows the worker to post emails progressively instead of injecting the full mailbox at once.

---

## Attachments

Attachments are an important part of the internship.

The fake dataset should include emails with attachments such as:

- PDF quotation.
- PDF invoice.
- PDF purchase order.
- PDF proforma invoice.
- PDF delivery note.
- PDF customs document.
- Excel price comparison.
- Excel order list.
- Word meeting report.
- PNG or JPG screenshot.
- Technical datasheet.

The JSON should reference attachment paths, for example:

```text
attachments/pdf/fake_invoice_001.pdf
attachments/excel/fake_supplier_comparison_001.xlsx
attachments/word/fake_meeting_report_001.docx
```

The intern's app should be able to retrieve and analyze these attachments from Gmail.

---

## Gmail Integration Recommendation

The preferred Gmail mode is **Gmail API import**, not normal SMTP sending.

### Why Gmail API import is better

- It avoids sending real emails over the internet.
- It allows fake sender identities to appear in the sandbox inbox.
- It supports attachments.
- It is cleaner for a fake mailbox simulation.
- It avoids needing many real Gmail accounts.
- It reduces spam and deliverability problems.

### Required setup for the intern

The intern should create or use:

- A sandbox Gmail account.
- A Google Cloud project.
- Gmail API enabled.
- OAuth consent screen.
- OAuth Desktop Client.
- `credentials.json` file.
- Local `token.json` generated after first login.

After the first OAuth login, the worker can reuse the saved token.

---

## Worker Responsibility

The Python worker should remain simple.

It should:

- Read the JSON dataset.
- Check unsent emails.
- Check if the scheduled offset has arrived.
- Build a MIME email.
- Attach files if needed.
- Import the message into Gmail using Gmail API.
- Save the Gmail message ID.
- Mark the message as sent.
- Keep logs.

The worker should not:

- Generate email content.
- Call an LLM.
- Invent business logic.
- Modify the scenario.
- Use real mailbox data.

---

## Email Agent App Expected Features

The intern app should provide:

- Email synchronization from Gmail.
- Inbox dashboard.
- Email detail view.
- Thread view.
- Attachment download and analysis.
- Email classification.
- Priority detection.
- Thread summarization.
- Action item extraction.
- Deadline extraction.
- Entity extraction.
- Suggested reply generation.
- Search by natural language.
- Evaluation against ground truth.

---

## Hidden Ground Truth

The JSON dataset should include hidden ground truth fields that are not sent inside the email body.

Example:

```text
ground_truth.category
ground_truth.priority
ground_truth.requires_action
ground_truth.expected_action
ground_truth.entities.client
ground_truth.entities.supplier
ground_truth.entities.project
ground_truth.entities.amount
ground_truth.entities.deadline
ground_truth.attachment_expected
```

This allows the supervisor to evaluate whether the intern's agent understood the email correctly.

---

## Dataset Generation Method

The supervisor can use Codex, Claude Code, Cursor, or another coding assistant to generate the large JSON dataset.

Recommended generation process:

```text
Step 1: Generate fake companies and contacts.
Step 2: Generate fake projects.
Step 3: Generate 80 to 120 cohesive threads.
Step 4: Expand each thread into 8 to 15 emails.
Step 5: Add attachment references.
Step 6: Add hidden ground truth.
Step 7: Validate the JSON.
Step 8: Generate fake attachment files.
Step 9: Test worker in dry-run mode.
Step 10: Test Gmail import with a small batch before running the full dataset.
```

The final target is around:

```text
1000 fake emails
80 to 120 threads
250 to 350 emails with attachments
650 to 750 emails without attachments
```

---

## Important Data Safety Rule

All companies, contacts, projects, email addresses, document numbers, invoice numbers, shipment references, and amounts must be fictional.

The dataset must not include real names, real client names, real supplier names, real project names, real email addresses, or real confidential information.

---

## Final Internship Boundary

The supervisor prepares the fake JSON dataset and the sandbox files.

The intern builds the Gmail integration and the Email Agent App.

```text
Supervisor:
Generate 1000 fake JSON emails + fake attachments.

Intern:
Use Gmail API + worker + app to process the fake mailbox.
```
