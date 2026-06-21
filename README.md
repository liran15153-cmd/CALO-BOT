# CALO Coach

AI fitness coach product foundation with structured onboarding, chat, workout plans, workout logs, meal logs, dashboard state, safety checks, and usage tracking.

## Local Setup

1. Copy `.env.example` to `.env.local`.
2. Fill Supabase values only in `.env.local`:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SECRET_KEY` only for trusted server-side/admin work
   - `DATABASE_URL` with the Supabase Postgres connection string when using Supabase
3. Keep `SUPABASE_AUTH_REQUIRED=false` for local SQLite development. Set it to `true` when running against Supabase Auth.
4. Run:

```powershell
npm run install:all
npm test
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

Manual user-isolation check:

1. Create two Supabase Auth users.
2. Run the backend with `SUPABASE_AUTH_REQUIRED=true`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and Supabase Postgres `DATABASE_URL`.
3. Sign in as user A and create onboarding, chat, workout log, meal log, body metric, and memory summary.
4. Sign in as user B and confirm user A data is not returned by API routes or by direct Data API requests with user B's JWT.

## Security Notes

- Do not commit `.env.local`.
- Do not expose `SUPABASE_SECRET_KEY` in the frontend. Only `VITE_SUPABASE_PUBLISHABLE_KEY` is browser-safe.
- If any Supabase secret key was sent in chat, rotate it in Supabase before production use and delete the old key.
- Supabase is the data/auth/storage layer. Coach intent routing, safety rules, workout planning, meal estimation, memory extraction, and usage limits remain backend services.
- Local meal-image file storage is a development fallback for SQLite/no-auth mode only. Production should run with Supabase configured and `SUPABASE_AUTH_REQUIRED=true` so meal images go through the private `meal-images` bucket.
