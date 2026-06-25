---
type: reference
status: active
source_of_truth: true
updated: 2026-06-25
---

# Prompt Registry

Prompts stay short and task-specific.

## Active Prompt Types

- Coach chat
- Workout generation
- Meal image analysis
- Meal text parsing
- Safety classification

## Constraints

- Use compact structured context only.
- Do not send full chat history.
- Do not send the entire database.
- Require Hebrew-first user-facing output.
- Allow short English fitness/nutrition terms when they sound natural.
- Avoid medical, diagnostic, or exact nutrition claims.
- Keep provider responses plain text for the current chat UI.
- Use `coaching_knowledge` as bounded static coaching guidance.
- If a workout log uses verbal effort such as `קל מדי`, `כבד מדי`, or `בשליטה`, preserve it as verbal effort. Do not invent numeric RPE/RIR.
- For a substitution/regression progression gate, save verbal effort but do not advance the gate from verbal effort alone. Require numeric `RPE 1-10` plus pain status before moving one step.

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON.
- Provider-backed chat goes through `token_budgeting.build_optimized_chat_request()`.
- `ContextBuilder` can include profile, current plan, recent workouts, recent meals, body metrics, active safety memory facts, recent chat, training status, and static coaching knowledge.
- `coaching_knowledge` is not user memory.
- Optimized workout chat context keeps one compact `coaching_behavior` item so verbal effort guidance survives token compaction.
- Legacy user-fact prompts are not active on `main`.
