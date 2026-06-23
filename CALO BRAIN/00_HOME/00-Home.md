---
type: home
status: active
source_of_truth: true
updated: 2026-06-23
---

# CALO Coach

Local-first AI fitness coach foundation.

The current `main` branch focuses on the core product loop: onboarding, coach chat, structured workout plans, workout logging, meal logging with optional image analysis, body metrics, dashboard, safety guardrails, settings export/reset, and usage tracking.

Legacy personalization/state and generated-summary systems were removed from active code. Do not add old personalization or summary routes, services, or tables back while stabilizing `main`; the cleanup migration is the historical reference for their exact names.

## Run Locally

```powershell
npm run install:all
npm run dev
```

Backend: `http://127.0.0.1:8000`
Frontend: `http://127.0.0.1:5173` by default. If that port is taken, Vite uses the next free port.

## Environment

Copy `.env.example` to `.env.local` or set environment variables directly.

- `DATABASE_URL`: defaults to `sqlite:///./data/app.db`
- `BACKEND_CORS_ORIGINS`: local Vite origins by default
- `ANTHROPIC_API_KEY`: optional; missing keys must produce honest not-configured states
- `ANTHROPIC_MODEL` / `ANTHROPIC_CHAT_MODEL`: provider model settings
- `DAILY_AI_TOKEN_LIMIT`: daily budget for provider-backed AI calls
- `VITE_API_BASE_URL`: optional frontend backend URL override
- `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`: browser-safe Supabase values only

## Active API Surface

- `GET /api/health`
- `GET/POST /api/onboarding`
- `POST /api/chat`
- `POST /api/chat/sessions`
- `POST /api/chat/sessions/{session_id}/reset`
- `GET /api/chat/messages`
- `GET /api/pending-actions/current`
- `POST /api/pending-actions/{action_id}/resolve`
- `POST /api/workout-plans`
- `GET /api/workout-plans/current`
- `POST /api/workout-plans/{plan_id}/activate`
- `DELETE /api/workout-plans/{plan_id}`
- `GET /api/workouts/next`
- `POST /api/workout-logs`
- `GET /api/workout-logs/recent`
- `GET /api/meals/recent`
- `POST /api/meals/upload`
- `POST /api/meals/{meal_id}/analyze`
- `POST /api/meals/manual`
- `POST /api/body-metrics`
- `GET /api/body-metrics/recent`
- `GET /api/body-metrics/latest`
- `GET /api/dashboard`
- `GET /api/settings`
- `GET /api/settings/export`
- `POST /api/settings/reset`
- `GET /api/usage`

## Test

```powershell
npm run scan:secrets
python -m pytest backend/tests --basetemp=.pytest-tmp
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test -- --run
```

Supabase live verification is separate from local tests:

```powershell
npm run verify:supabase
```

It requires real Supabase Auth test users in `.env.local`.
