---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-21
related_paths:
  - backend/app/main.py
  - backend/app/api
notes: >-
  Service boundaries and route ownership.
---

# Service and Route Map

- **Route layer** stays thin and schema-driven.
- **Service layer** contains domain logic (coach_engine, context_builder, workout_service, pending_action_service, meal_service, safety_service, usage_service).
- **Pending action routes** expose current unresolved decisions and resolve confirm/decline choices without using chat metadata as the source of truth.
- **Frontend** reads persisted state and renders actionable surfaces.
- **Provider** logic is only called after safety + budget gates pass.
- **Token budgeting** lives in `token_budgeting.py` and `usage_service.py`: coach chat builds a compact provider payload, keeps a legacy full-context baseline for measurement, records system/history/memory/tools/message/output breakdowns, and stores per-conversation totals on provider-backed coach messages.
