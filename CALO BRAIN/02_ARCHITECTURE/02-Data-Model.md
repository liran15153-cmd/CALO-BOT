---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-20
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
- UsageEvent
- WeeklySummary

All entities feed dashboard and coaching context from persisted records.
