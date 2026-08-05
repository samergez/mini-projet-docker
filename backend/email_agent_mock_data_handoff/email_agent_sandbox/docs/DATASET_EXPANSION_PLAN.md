# Dataset Expansion Plan

Generate in batches instead of one huge edit. Suggested target for final dataset: around 1,000 messages, 80-120 threads, 25-35% messages with attachments.

Distribution: client/project 250, supplier/order 200, internal 150, accounting 120, customs/import/export 100, shipment 80, bank/payment 50, admin/noise 50.

Always run `python tools/validate_dataset.py` after each expansion.
