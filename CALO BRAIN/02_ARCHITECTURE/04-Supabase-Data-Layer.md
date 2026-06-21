---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-21
related_paths:
  - supabase/migrations/202606210001_calo_core_schema.sql
  - backend/app/auth.py
  - backend/app/services/file_storage_service.py
notes: >-
  Supabase data/auth/storage layer for production-oriented persistence.
---

# Supabase Data Layer

Supabase is the data/auth/storage layer only. CALO coach behavior stays in backend services: intent routing, safety, workout planning, memory extraction, meal estimation, dashboard calculation, and usage budgeting.

## Runtime split

- Local development can keep SQLite with `SUPABASE_AUTH_REQUIRED=false`.
- Supabase mode requires `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `DATABASE_URL`, and `SUPABASE_AUTH_REQUIRED=true`.
- Frontend stores a Supabase access token after email/password auth and sends it as `Authorization: Bearer ...`.
- Backend resolves the token through Supabase Auth, maps `auth.users.id` to `users.auth_user_id`, and passes the internal `users.id` to existing services.

## Persistence

The Supabase migration creates RLS-protected tables for users, fitness profiles, chat sessions/messages, workout plans/workouts/exercises/logs, meal logs/items/image analyses, coaching memories, memory summaries, body metrics, safety events, usage events, weekly summaries, and pending actions.

Meal images move from `data/uploads` to the private `meal-images` Supabase Storage bucket when Supabase Auth is configured.

## Security

Use publishable keys in the browser only. Keep secret keys server-side and rotate any secret key that was shared in chat before production use.
