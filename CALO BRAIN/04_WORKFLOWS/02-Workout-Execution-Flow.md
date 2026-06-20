---
type: workflow
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - backend/app/services/workout_service.py
  - frontend/src/WorkoutsPanel.tsx
notes: >-
  Plan execution, adaptation, and logging loop.
---

# Workout Execution Flow

- Pull current active plan from persistence.
- Compute next workout and execution adaptation.
- Render executable variants while preserving base plan.
- Save structured logs using workout/exercise IDs.
