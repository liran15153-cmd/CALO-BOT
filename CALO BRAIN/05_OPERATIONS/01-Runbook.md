---
type: operations
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - package.json
  - backend/app/main.py
  - frontend/src/App.tsx
notes: >-
  Daily and weekly operations checklist.
---

# Runbook

`powershell
npm run install:all
npm run dev
`

`powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
`

- If the API key is missing, verify provider-not-configured path is intentional.
