# Development Workflow Guards

This repo stays stable by keeping `main` boring.

- Do not work directly on `main`; create a feature or cleanup branch first.
- Do not merge a stale or polluted branch. Cherry-pick the reviewed commit or files onto current `main`.
- Run full checks before pushing `main`:
  - `npm run scan:secrets`
  - `python -m pytest backend/tests --basetemp=.pytest-tmp`
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
  - `npm --prefix frontend test -- --run`
- Keep memory branches frozen until the memory plan is explicitly resumed.
- Do not restore legacy memory or summary routes, services, tables, or docs.
- Keep frontend and backend tests isolated from `.env.local`; live Supabase verification is separate.
- Do not track local/editor artifacts such as Obsidian workspace state, caches, logs, build outputs, or local DB files.
