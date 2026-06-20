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
- `WorkoutService`: profile-aware plan generation, row-level workout/exercise persistence, and workout log parsing
- `TrainingAdaptationService`: compact interpretation of recent workout logs for load, adherence, pain and recovery signals
- `MealService`: image/manual meal logging, configured image-analysis normalization, and estimate handling
- `SummaryService`: daily and weekly summaries from stored facts
- `UsageService`: per-call usage tracking plus a daily token budget gate before provider-backed calls
- `FileStorageService`: sanitized local upload storage with type allow-list, magic-byte checks, and size caps
- `SettingsService`: provider status, JSON export, and local data reset

## Persistence

SQLite stores the local user's profile, chat sessions/messages, workout plans, workout logs, meals, image analysis records, durable memories, weekly summaries, safety events, and usage events. Uploaded meal images live under `data/uploads`, not in the database.

Workout plans are stored both as the original structured `plan_json` and as `Workout` / `WorkoutExercise` rows so future editors can work against durable sub-objects instead of parsing a blob.

## Frontend Surfaces

- Onboarding: profile and consent capture
- Chat: persisted coach conversation with safety and no-provider states
- Workouts: structured plan generation and natural-language log parsing
- Meals: image upload, image analysis ranges, detected items, follow-up questions, and manual meal estimates
- Dashboard: current goal, plan, weekly activity, nutrition range, memories, and next action
- Settings: provider status, disclaimer, export/reset, usage totals, and remaining daily AI token budget

## Adapter Direction

The coach engine must not know whether a message came from web UI, desktop wrapper, or a future messaging adapter. A future WhatsApp adapter should call the same core services.

The current identity resolver is still the local default user. A WhatsApp or cloud adapter must add a channel/external-user identity boundary before public release.
