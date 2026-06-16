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
- `SafetyService`: rule-based safety classification and conservative responses
- `ContextBuilder`: compact AI context from structured state, never full database dumps
- `MemoryService`: durable memory extraction and retrieval
- `WorkoutService`: plan generation and workout log parsing
- `MealService`: image/manual meal logging and estimate handling
- `SummaryService`: daily and weekly summaries from stored facts
- `UsageService`: per-call usage/cost tracking foundation
- `FileStorageService`: sanitized local upload storage
- `SettingsService`: provider status, JSON export, and local data reset

## Persistence

SQLite stores the local user's profile, chat sessions/messages, workout plans, workout logs, meals, image analysis records, durable memories, weekly summaries, safety events, and usage events. Uploaded meal images live under `data/uploads`, not in the database.

## Frontend Surfaces

- Onboarding: profile and consent capture
- Chat: persisted coach conversation with safety and no-provider states
- Workouts: structured plan generation and natural-language log parsing
- Meals: image upload, image analysis, and manual meal estimates
- Dashboard: current goal, plan, weekly activity, nutrition range, memories, and next action
- Settings: provider status, disclaimer, export/reset, and usage totals

## Adapter Direction

The coach engine must not know whether a message came from web UI, desktop wrapper, or a future messaging adapter. A future WhatsApp adapter should call the same core services.
