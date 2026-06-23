---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-23
---

# System Architecture

CALO Coach is a local-first product foundation, not a demo chatbot. The frontend calls backend APIs; routes stay thin; product behavior lives in services.

## Runtime

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Pydantic + SQLAlchemy
- Local storage: SQLite at `data/app.db`
- Uploads: local files under `data/uploads`, or Supabase Storage when configured
- AI: provider interface with Anthropic implementation and honest no-key fallback

## Backend Boundaries

- `api`: route handlers, request/response models, dependency wiring
- `models`: SQLAlchemy entities
- `schemas`: Pydantic public contracts
- `services`: business logic and AI orchestration
- `prompts`: short task-specific prompt builders

## Core Services

- `AIProvider`: chat, structured extraction, image analysis, and no-key fallback
- `CoachEngine`: safety check, context build, AI response, and persistence orchestration
- `CoachIntentService`: deterministic v1 intent classification before generic chat
- `ContextBuilder`: compact context from profile, plans, logs, meals, safety, body metrics, and recent chat
- `SafetyService`: rule-based safety classification and conservative responses
- `WorkoutService`: plan generation, plan activation, next workout, and workout logging
- `TrainingAdaptationService`: recent workout interpretation for adherence, recovery, pain, and load signals
- `MealService`: image/manual meal logging and estimate normalization
- `DashboardService`: current goal, active plan, weekly activity, nutrition ranges, and next action
- `BodyMetricService`: body metric persistence and recent/latest metric reads
- `SettingsService`: provider status, JSON export, and data reset
- `UsageService`: provider usage tracking and daily token budget gate
- `FileStorageService`: local upload validation and storage
- `ReadinessService`: Supabase/Auth/Storage readiness reporting

## Persistence

The active model set is:

- `users`
- `fitness_profiles`
- `chat_sessions`
- `chat_messages`
- `pending_actions`
- `workout_plans`
- `workouts`
- `workout_exercises`
- `workout_logs`
- `meal_logs`
- `meal_items`
- `meal_image_analyses`
- `body_metrics`
- `safety_events`
- `usage_events`

Legacy personalization/state and persisted summary tables are intentionally absent from active `main`. The cleanup migration remains only to remove old deployments safely.

## Adapter Direction

The coach engine should not know whether a message came from the web UI, desktop wrapper, or a future messaging adapter. Future public adapters must add a real external-user identity boundary before release.
