# CALO Coach

Local-first AI fitness coach foundation.

This first version is a desktop/web app that runs locally. It focuses on a real creative product loop for fitness coaching: onboarding, coach chat, structured memory, workout planning/logging, meal logging with optional image analysis, summaries, dashboard, safety guardrails, and usage tracking.

## Run Locally

```powershell
npm install
npm --prefix frontend install
python -m pip install -r backend/requirements.txt
npm run dev
```

Backend: `http://127.0.0.1:8000`  
Frontend: `http://127.0.0.1:5173` by default. If that port is already taken, Vite will use the next free port.

## Environment

Copy `.env.example` to `.env.local` or set environment variables directly.

- `DATABASE_URL`: defaults to `sqlite:///./data/app.db`
- `BACKEND_CORS_ORIGINS`: defaults to local Vite ports `5173` and `5174`
- `ANTHROPIC_API_KEY`: optional. If missing, the app runs with honest provider-not-configured states.
- `ANTHROPIC_MODEL`: defaults to `claude-haiku-4-5`

## Current Scope

Included:

- Local FastAPI backend
- SQLite persistence
- React/Vite frontend
- AI provider abstraction with Anthropic Claude implementation and no-key fallback
- Structured memory and summaries
- Safety guardrails
- Local upload storage
- Dashboard backed by persisted state
- Settings export/reset controls
- Usage metadata for chat, image analysis, and summaries

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

## Test

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```
