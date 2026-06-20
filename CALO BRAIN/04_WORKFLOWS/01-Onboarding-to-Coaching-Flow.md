---
type: workflow
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - backend/app/api/onboarding.py
  - frontend/src/OnboardingPanel.tsx
notes: >-
  Structured onboarding and profile lifecycle.
---

# Onboarding to Coaching Flow

1. Collect essential profile fields.
2. Persist profile + onboarding state.
3. Build compact profile summary.
4. Start context-aware coaching session.
5. Persist durable memories only after extracting relevant facts.
