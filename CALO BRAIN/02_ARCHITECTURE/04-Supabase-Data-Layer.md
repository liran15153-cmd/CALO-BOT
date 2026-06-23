---
type: architecture
status: active
source_of_truth: true
updated: 2026-06-23
related_paths:
  - supabase/migrations/202606210001_calo_core_schema.sql
  - backend/app/auth.py
  - backend/app/services/readiness_service.py
  - backend/app/services/file_storage_service.py
  - scripts/verify_supabase_live.py
notes: >-
  Supabase data/auth/storage layer for production-oriented persistence.
---

# Supabase Data Layer

Supabase is the data/auth/storage layer only. CALO coach behavior stays in backend services: intent routing, safety, workout planning, meal estimation, dashboard calculation, and usage budgeting.

## Runtime split

- Local development can keep SQLite with `SUPABASE_AUTH_REQUIRED=false`.
- Supabase mode requires `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWKS_URL`, non-SQLite `DATABASE_URL`, and `SUPABASE_AUTH_REQUIRED=true`.
- Frontend stores a Supabase access token after email/password auth and sends it as `Authorization: Bearer ...`.
- Backend validates the token locally with JWKS, maps `auth.users.id` to `users.auth_user_id`, and passes the internal `users.id` to existing services.
- `/api/readiness` reports non-secret production readiness for DB/Auth/JWKS/Storage and rejects SQLite when Supabase Auth is required.

## Persistence

The Supabase migration creates RLS-protected tables for users, fitness profiles, chat sessions/messages, pending actions, workout plans/workouts/exercises/logs, meal logs/items/image analyses, body metrics, safety events, and usage events. A later cleanup migration removes legacy personalization/state and summary tables from older deployments.

Meal images move from `data/uploads` to the private `meal-images` Supabase Storage bucket when Supabase Auth is configured. Local upload storage is allowed only for SQLite/no-auth development.

## Security

Use publishable keys in the browser only. Keep secret keys server-side and rotate any secret key that was shared in chat before production use.
`npm run scan:secrets` checks source/docs/log text for secret-like Supabase, Anthropic, JWT, and Postgres URL values. `npm run verify:supabase` is optional live proof: it requires two real Supabase Auth test users, verifies Data API RLS read/update/delete isolation when it owns the row, verifies private Storage read/delete isolation, and cleans up only verifier-created data.
