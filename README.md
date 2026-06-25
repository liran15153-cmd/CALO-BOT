# CALO Coach

AI fitness coach product foundation with structured onboarding, chat, workout plans, workout logs, meal logs, dashboard state, safety checks, and usage tracking.

## Local Setup

1. Copy `.env.example` to `.env.local`.
2. Fill Supabase values only in `.env.local`:
   - `SUPABASE_URL`
   - `SUPABASE_JWKS_URL` (`https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`)
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SECRET_KEY` only for trusted server-side/admin work
   - `DATABASE_URL` with the Supabase Postgres connection string when using Supabase
3. Keep `SUPABASE_AUTH_REQUIRED=false` for local SQLite development. Set it to `true` when running against Supabase Auth; production auth uses local JWKS JWT validation, not a fallback Auth REST lookup.
4. Run:

```powershell
npm run install:all
npm test
npm run scan:secrets
npm run dev
```

## Supabase

Apply all SQL files under `supabase/migrations/` to the Supabase project before pointing the app at Supabase Postgres. The migrations create the core CALO tables, add body metric detail fields, enable RLS, grant authenticated access, and create the private `meal-images` Storage bucket policies.

`supabase/seed.sql` is development-only sample data. It does not create a real Supabase Auth user.

### Live Supabase Verification

This repo can be verified against a real Supabase project with `DATABASE_URL`. Do not claim the live project is verified until these commands have run against that project.

```powershell
$env:DATABASE_URL="postgresql://..."
psql $env:DATABASE_URL -f supabase/migrations/202606210001_calo_core_schema.sql
psql $env:DATABASE_URL -f supabase/migrations/202606210002_add_body_metric_details.sql
psql $env:DATABASE_URL -f supabase/verify_schema_rls.sql
```

The verification query should show every expected `public` table with `table_exists=true`, `rls_enabled=true`, and at least one policy. It should also return the `body_metrics` columns `body_fat_percent`, `measurements_json`, and `source`, plus the private `meal-images` bucket.

Runtime readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/readiness
```

`/api/readiness` returns non-secret status for database, Supabase Auth, JWKS config, Storage config, `auth_required`, and `production_ready`. It must not expose keys, tokens, `DATABASE_URL`, or JWKS contents.

Automated user-isolation and Storage check:

```powershell
$env:SUPABASE_URL="https://<project-ref>.supabase.co"
$env:SUPABASE_PUBLISHABLE_KEY="sb_publishable_..."
# Optional server-side admin key: creates or repairs the two verifier Auth users before sign-in.
$env:SUPABASE_SECRET_KEY="<server-side-service-role-key>"
$env:SUPABASE_TEST_USER_A_EMAIL="a@example.com"
$env:SUPABASE_TEST_USER_A_PASSWORD="..."
$env:SUPABASE_TEST_USER_B_EMAIL="b@example.com"
$env:SUPABASE_TEST_USER_B_PASSWORD="..."
npm run verify:supabase
```

`npm run verify:supabase` signs in two real Supabase Auth users, uses an existing user A `public.users` row or inserts a verifier-owned row, verifies user B cannot read it, checks user B update/delete isolation only for a row the verifier created, uploads one private `meal-images` object under user A's auth id, verifies user B cannot read or delete it, and cleans up only verifier-created data. If `SUPABASE_SECRET_KEY` is set, the verifier first creates missing Auth users or resets their passwords and confirms their emails through Supabase Auth Admin. If required env vars are missing, it reports `skipped`; that is not live proof.

Manual API user-isolation check:

1. Create two Supabase Auth users.
2. Run the backend with `SUPABASE_AUTH_REQUIRED=true`, `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_PUBLISHABLE_KEY`, and Supabase Postgres `DATABASE_URL`.
3. Sign in as user A and create onboarding, chat, workout log, meal log, and body metric.
4. Sign in as user B and confirm user A data is not returned by API routes or by direct Data API requests with user B's JWT.

## Security Notes

- Do not commit `.env.local`.
- Do not expose `SUPABASE_SECRET_KEY` in the frontend. Only `VITE_SUPABASE_PUBLISHABLE_KEY` is browser-safe.
- If any Supabase secret key was sent in chat, rotate it in Supabase before production use and delete the old key.
- Supabase project URLs are public config; `DATABASE_URL`, secret keys, and JWKS validation internals stay server-side. The frontend may receive only `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`.
- Supabase is used backend-only for CALO data tables. Do not add direct client-side Data API table access without a separate RLS/grants/user-isolation review.
- Supabase Auth access tokens are validated locally against `SUPABASE_JWKS_URL`; the JWKS URL must belong to the same project ref as `SUPABASE_URL`.
- Supabase Storage meal images must stay in a private bucket under `<auth_user_id>/<date>/<uuid>.<ext>`. Browser access should use short-lived signed URLs through the backend, not public object URLs.
- Coach intent routing, safety rules, workout planning, meal estimation, safety memory facts, context assembly, and usage limits remain backend services.
- Local meal-image file storage is a development fallback for SQLite/no-auth mode only. Production or `SUPABASE_AUTH_REQUIRED=true` must use the private Supabase `meal-images` bucket.
