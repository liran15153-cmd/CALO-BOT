# Development Log

## 2026-06-15

- Initialized local-first CALO Coach project.
- Chosen stack: FastAPI, SQLite, SQLAlchemy, React, Vite, TypeScript.
- Locked v1 scope to AI Fitness Coach only.
- Deliberately excluded WhatsApp, payments, cloud deployment, mobile, and medical claims from v1.
- Implemented onboarding, chat persistence, safety events, memory extraction, workout plans/logs, meal upload/manual logging, summaries, dashboard, settings export/reset, and usage tracking.
- Verified no-key AI behavior stays explicit instead of faking coach or vision output.

## 2026-06-16

- Added deterministic coach intent dispatch for workout plan creation, workout logging, and meal logging before generic AI chat.
- Made workout plan generation use saved profile availability, equipment, session length, preferred days, and limitations when the request is open-ended.
- Persisted generated workout days and exercises into row-level `Workout` and `WorkoutExercise` records in addition to `plan_json`.
- Added intent-aware memory filtering in the context builder.
- Moved dashboard aggregation and next-action logic into `DashboardService`.
- Changed empty dashboard nutrition estimates to return and render an empty state instead of `null-null`.
- Hardened meal image uploads with a 5 MB cap and image signature checks.
- Normalized configured image-analysis JSON into persisted meal calorie/macro ranges and detected `MealItem` rows.
- Hydrated the workouts UI from the current persisted plan and removed demo-filled workout form defaults.
- Displayed configured meal image ranges, detected items, and follow-up questions in the meals UI.
- Added `docs/RELEASE_CHECKLIST.md` to separate local-first readiness from public release blockers.
