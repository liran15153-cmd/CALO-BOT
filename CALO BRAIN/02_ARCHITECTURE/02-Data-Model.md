---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-21
related_paths:
  - backend/app/models.py
  - backend/app/schemas.py
notes: >-
  Entity map and persistence intent.
---

# Data Model

- UserProfile
- OnboardingState
- CoachingMemory
- WorkoutPlan
- WorkoutDay
- Exercise
- WorkoutLog
- MealLog
- MealImageAnalysis
- SafetyEvent
- ChatMessage
- PendingAction
- UsageEvent
- WeeklySummary

All entities feed dashboard and coaching context from persisted records.
PendingAction stores user decisions waiting for confirmation, such as activating a candidate workout plan, so product state does not depend on chat message metadata.
UsageEvent stores estimated provider input/output totals plus `token_breakdown_json` for system prompt, history, memory, tools/coaching knowledge, user message, output, input total, and total. Coach ChatMessage metadata also carries the per-turn token breakdown plus conversation token total for provider-backed turns.
