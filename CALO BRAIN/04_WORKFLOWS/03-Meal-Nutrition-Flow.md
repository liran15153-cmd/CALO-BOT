---
type: workflow
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - backend/app/services/meal_service.py
  - frontend/src/MealsPanel.tsx
notes: >-
  Meal logging flow and uncertainty policy.
---

# Meal and Nutrition Flow

- Manual meals: parse to approximate ranges and editable structure.
- Images: run only when provider configured, return uncertainty + confidence.
- No exact macro certainty from computer vision; always include ranges.
