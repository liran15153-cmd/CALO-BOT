---
type: product
status: active
source_of_truth: true
updated: 2026-06-25
---

# Product Behavior

CALO is a Hebrew-first AI fitness coach product foundation. It is not a generic chatbot and not a medical product.

## Current Product State

- Onboarding/profile stores structured user data.
- Chat messages are saved as chat history, not durable memory.
- `memory_facts` currently stores durable safety facts; non-safety fact extraction is deferred.
- Workout plans, workouts, exercises, workout logs, meal logs, meal image analyses, body metrics, safety events, usage events, and pending actions are persisted product state.
- `ContextBuilder` assembles working context from persisted state and recent chat.
- `coaching_knowledge` is static provider guidance, not user memory.
- Legacy memory/summaries are not active product behavior on `main`.

## Coach Behavior

- User-visible product copy and coach responses are Hebrew-first.
- Responses should be short, practical, and action-oriented.
- The coach should give one clear next action and ask one follow-up question only when needed.
- Provider output must stay general wellness coaching and must not claim medical, diagnostic, or exact nutrition authority.
- If no AI provider is configured, the app must say so instead of faking AI behavior.

## Safety

- Safety handling runs before provider chat.
- Allergy, medical, injury, and nutrition-restriction facts must stay in context when active.
- The app must respond conservatively to pain, injury, dizziness, chest pain, medical conditions, extreme dieting, unsafe supplements, and diagnosis requests.
- Safety events are stored as `SafetyEvent` records.
- Common non-diagnostic substitutions can be handled locally when safe, but sharp, worsening, persistent, or dangerous symptoms should point to qualified help.

## Workouts

- Workout plans are structured app data, not chat-only text.
- The workout execution loop is backed by saved plans and logs.
- `GET /api/workouts/next` derives the next workout and a non-persisted execution adjustment from recent logs.
- Structured workout logs persist status, exercise results, RPE/RIR when supplied, verbal effort signals such as `קל מדי`, `כבד מדי`, and `בשליטה`, pain flags, and notes.
- Verbal effort must stay verbal in coach responses, next-workout adjustments, and dashboard copy. Do not turn `קל מדי`, `כבד מדי`, or `בשליטה` into fake numeric RPE/RIR evidence.
- After a substitution or regression gate, verbal effort can be saved, but advancing to the next exercise version requires numeric `RPE 1-10` plus pain status. Without that, keep the current version and ask for the missing effort/pain signal.

## Meals

- Meal and image estimates are approximate ranges with confidence, not exact nutrition claims.
- Configured image analysis normalizes provider output into persisted meal ranges and detected items.
- If image analysis is not configured, the app must not fake detected foods.

## Dashboard

- The dashboard shows persisted state: current goal, active plan, workouts, meals, consistency, streaks, nutrition ranges, and one next action.
- Dashboard summaries must be derived from stored logs/meals, not legacy memory tables.

## Data Controls

- Settings exposes provider status, usage totals, daily token budget, JSON export, and local reset.
- Settings must not expose secrets.
