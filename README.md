# CALO Coach

Local-first AI fitness coach foundation.

This first version is a desktop/web app that runs locally. It focuses on a real creative product loop for fitness coaching: onboarding, coach chat, structured memory, workout planning/logging, meal logging with optional image analysis, summaries, dashboard, safety guardrails, and usage tracking.

The product UI and coach-facing responses are Hebrew-only. Technical identifiers such as API fields, provider statuses, environment variables, model names, and URLs remain in English.

This is release-ready as a local-first product foundation. It is not ready to expose on the public internet without adding authentication, user ownership boundaries, migrations, deployment hardening, and stronger upload security.

## Run Locally

```powershell
npm run install:all
npm run dev
```

Backend: `http://127.0.0.1:8000`  
Frontend: `http://127.0.0.1:5173` by default. If that port is already taken, Vite will use the next free port.

Verified locally with Node `v24.15.0`, npm `11.12.1`, and Python `3.14.4`. Pin tool versions before team or cloud release.

## Environment

Copy `.env.example` to `.env.local` or set environment variables directly.

- `DATABASE_URL`: defaults to `sqlite:///./data/app.db`
- `BACKEND_CORS_ORIGINS`: defaults to local Vite ports `5173` and `5174`
- `ANTHROPIC_API_KEY`: optional. If missing, the app runs with honest provider-not-configured states.
- `ANTHROPIC_MODEL`: defaults to `claude-haiku-4-5`
- `DAILY_AI_TOKEN_LIMIT`: defaults to `50000`; configured AI chat and image analysis are blocked after this daily token budget is spent.
- `VITE_API_BASE_URL`: optional frontend setting for a non-default backend URL.

## Current Scope

Included:

- Local FastAPI backend
- SQLite persistence
- React/Vite frontend
- AI provider abstraction with Anthropic Claude implementation and no-key fallback
- Core coaching engine with safety-first intent dispatch for workout plan creation, workout logging, meal logging, and fallback chat
- Source-backed coaching knowledge context for general fitness rules, progression, adherence, nutrition uncertainty, and safety boundaries
- Structured memory and summaries
- Safety guardrails
- Local upload storage with type allow-list, image signature checks, and a 5 MB meal-image cap
- Dashboard backed by persisted state
- Settings export/reset controls
- Usage metadata and a daily token budget gate for provider-backed chat and image analysis

## API Surface

- `GET /api/health`
- `GET/POST /api/onboarding`
- `POST /api/chat`
- `POST /api/chat/sessions`
- `GET /api/chat/messages`
- `POST /api/workout-plans`
- `GET /api/workout-plans/current`
- `POST /api/workout-logs`
- `POST /api/meals/upload`
- `POST /api/meals/{meal_id}/analyze`
- `POST /api/meals/manual`
- `GET /api/summaries/daily`
- `GET /api/summaries/weekly`
- `GET /api/dashboard`
- `GET /api/settings`
- `GET /api/settings/export`
- `POST /api/settings/reset`
- `GET /api/usage`

Not included:

- WhatsApp integration
- Payments
- Cloud deployment
- Mobile app
- Medical diagnosis or clinical guidance
- Multi-user authentication or public-user data isolation
- Full image sanitization, EXIF stripping, malware scanning, or upload retention cleanup

## Test

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```
