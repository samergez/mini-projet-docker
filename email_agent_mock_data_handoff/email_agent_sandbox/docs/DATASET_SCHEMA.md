# Dataset Schema

Main file: `dataset/emails_dataset.json`.

Top-level keys: `dataset_info`, `companies`, `contacts`, `projects`, `attachments_catalog`, `threads`, `messages`.

Important message fields: `message_id`, `thread_id`, `project_id`, `message_order`, `send_after_minutes`, `mailbox_side`, `from`, `to`, `subject`, `body_text`, `language`, `priority`, `reply_to_message_id`, `attachments`, `labels`, `ground_truth`.

`ground_truth` is hidden evaluation data and is not sent inside the email.

Option A rule: `body_text` is the final full email. No runtime mail-block assembly.
