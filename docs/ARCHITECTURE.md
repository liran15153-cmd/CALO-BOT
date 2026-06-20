# Architecture

## Principle

CALO Coach is a local-first product foundation, not a fake demo. The frontend is a client of backend APIs. Backend routes stay thin; product behavior lives in services.

## Runtime

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Pydantic + SQLAlchemy
- Storage: SQLite at `data/app.db`
- Uploads: local files under `data/uploads`
- AI: provider interface with Anthropic Claude implementation when `ANTHROPIC_API_KEY` exists

## Backend Boundaries

- `api`: route handlers, request/response models, dependency wiring
- `models`: SQLAlchemy entities
- `schemas`: Pydantic public contracts
- `services`: business logic and AI orchestration
- `prompts`: short, task-specific prompt builders

## Core Services

- `AIProvider`: chat, structured extraction, image analysis, summarization, honest no-key fallback
- `CoachEngine`: safety check, context build, AI response, persistence
- `CoachIntentService`: deterministic v1 intent classification for module dispatch before generic chat
- `CoachingKnowledgeService`: compact, source-backed general fitness coaching rules injected into provider context
- `SafetyService`: rule-based safety classification and conservative responses
- `ContextBuilder`: compact AI context from structured state and intent-relevant memories, never full database dumps
- `MemoryService`: durable memory extraction and retrieval
- `WorkoutService`: profile-aware plan generation, row-level workout/exercise persistence, next-workout selection, recent workout-log retrieval, text workout log parsing, structured workout log validation, and structured workout log persistence
- `TrainingAdaptationService`: compact interpretation of recent workout logs for load, adherence, pain, recovery signals, and exercise-level next-session adjustments
- `DashboardService`: weekly product summary, active goal fallback from saved plans, consecutive active-day streaks, and the compact next-workout/action surface composed from persisted plans, workout logs, meals, memories, and `WorkoutService.next_workout()`
- `MealService`: image/manual meal logging, configured image-analysis normalization, and estimate handling
- `SummaryService`: daily summaries, explicit persisted weekly summaries, and read-only current-week preview summaries from stored facts
- `UsageService`: per-call usage tracking plus a daily token budget gate before provider-backed calls
- `FileStorageService`: sanitized local upload storage with type allow-list, magic-byte checks, and size caps
- `SettingsService`: provider status, JSON export, and local data reset

## Persistence

SQLite stores the local user's profile, chat sessions/messages, workout plans, workout logs, meals, image analysis records, durable memories, weekly summaries, safety events, and usage events. Uploaded meal images live under `data/uploads`; meal rows store upload-root-relative image references, not absolute local filesystem paths or binary image data.

Workout plans are stored both as the original structured `plan_json` and as `Workout` / `WorkoutExercise` rows so future editors and execution flows can work against durable sub-objects instead of parsing a blob. The next-workout API returns a derived `execution_plan` for today's adjusted session, but it does not mutate `WorkoutPlan.plan_json`, `Workout.workout_json`, or `WorkoutExercise` rows. Structured execution results are stored in `WorkoutLog.exercise_results` JSON in v1 while primary log fields such as `workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain queryable columns. Workout-log IDs are validated against persisted workout rows before saving, and safety classification receives the full log source text, including exercise-level notes.

## Frontend Surfaces

- Onboarding: profile and consent capture
- Chat: persisted coach conversation with safety and no-provider states
- Workouts: structured plan generation, next workout display, structured execution logging, natural-language log parsing, and recent workout-log history
- Meals: image upload, image analysis ranges, detected/manual items, follow-up questions, manual meal estimates, and recent meal history
- Dashboard: current goal, plan, next workout, weekly activity, read-only weekly review, nutrition ranges, today's nutrition action, memories, and one adaptation-backed next action
- Settings: provider status, disclaimer, export/reset, usage totals, and remaining daily AI token budget

## Adapter Direction

The coach engine must not know whether a message came from web UI, desktop wrapper, or a future messaging adapter. A future WhatsApp adapter should call the same core services.

The current identity resolver is still the local default user. A WhatsApp or cloud adapter must add a channel/external-user identity boundary before public release.
