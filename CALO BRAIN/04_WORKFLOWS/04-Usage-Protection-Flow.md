---
type: workflow
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - backend/app/services/usage_service.py
notes: >-
  Usage accounting and budget enforcement flow.
---

# Usage Protection Flow

1. Check budget before provider path.
2. If exceeded, return provider_status: budget_exceeded without external calls.
3. Persist usage event for traceability.
4. Show remaining budget in settings UI.
