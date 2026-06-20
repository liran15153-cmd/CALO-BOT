---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - backend/app/main.py
  - backend/app/api
notes: >-
  Service boundaries and route ownership.
---

# Service and Route Map

- **Route layer** stays thin and schema-driven.
- **Service layer** contains domain logic (coach_engine, context_builder, workout_service, meal_service, safety_service, usage_service).
- **Frontend** reads persisted state and renders actionable surfaces.
- **Provider** logic is only called after safety + budget gates pass.
