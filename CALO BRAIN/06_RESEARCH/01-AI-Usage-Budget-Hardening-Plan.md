---
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
type: plan
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
status: archived
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
source_of_truth: true
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
updated: 2026-06-20
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
related_paths:
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
  - backend/app/services/usage_service.py
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
notes: >-
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
  Task-level hardening plan and implementation history
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.
---
# AI Usage Budget Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal daily AI token budget gate so configured provider calls can be blocked before spending continues.

**Architecture:** Keep the gate inside backend services, not prompts. `UsageService` owns usage totals and budget checks; `CoachEngine` and `MealService` call it before provider-backed chat and image analysis. The frontend only displays usage and remaining budget.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic settings/schemas, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Daily Token Budget

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/usage_service.py`
- Modify: `backend/tests/test_usage_api.py`

- [ ] **Step 1: Write failing usage API test**

Add assertions that `/api/usage` returns `estimated_tokens_total`, `daily_ai_token_limit`, and `tokens_remaining`.

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: FAIL because the response schema does not expose those fields yet.

- [ ] **Step 2: Implement minimal usage budget fields**

Add `daily_ai_token_limit` to settings, extend `UsageResponse`, and return total/remaining tokens from `UsageService.daily_totals()`.

- [ ] **Step 3: Verify usage tests**

Run: `python -m pytest backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 2: Provider Call Budget Gate

**Files:**
- Modify: `backend/app/services/coach_engine.py`
- Modify: `backend/app/services/meal_service.py`
- Modify: `backend/tests/test_coach_engine.py`
- Modify: `backend/tests/test_meal_upload_api.py`

- [ ] **Step 1: Write failing chat budget test**

Set `ANTHROPIC_API_KEY` and `DAILY_AI_TOKEN_LIMIT`, seed usage over the limit, then assert a general chat request returns `provider_status: budget_exceeded` and saves a budget usage event without calling the provider.

Run: `python -m pytest backend/tests/test_coach_engine.py -q`
Expected: FAIL because the engine currently attempts the provider path.

- [ ] **Step 2: Write failing image budget test**

Set the same budget env, seed usage over the limit, upload a meal image, then assert image analysis returns `provider_status: budget_exceeded` and persists an analysis record without fake detected items.

Run: `python -m pytest backend/tests/test_meal_upload_api.py -q`
Expected: FAIL because image analysis currently attempts the provider path.

- [ ] **Step 3: Implement budget gate**

Use `UsageService.is_daily_ai_token_budget_exceeded()` before configured provider chat and image analysis. Return honest budget-exceeded messages, record `UsageEvent` rows with provider `budget_exceeded`, and do not generate fake meal detections.

- [ ] **Step 4: Verify targeted backend tests**

Run: `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_meal_upload_api.py backend/tests/test_usage_api.py -q`
Expected: PASS.

### Task 3: Frontend Visibility And Docs

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/SettingsPanel.tsx`
- Modify: `frontend/src/SettingsPanel.test.tsx`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/PRODUCT_BEHAVIOR.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/RELEASE_CHECKLIST.md`

- [ ] **Step 1: Write failing settings UI test**

Update the settings mock usage payload and assert the UI renders remaining daily AI token budget.

Run: `npm --prefix frontend test -- --run src/SettingsPanel.test.tsx`
Expected: FAIL until the UI renders the new usage fields.

- [ ] **Step 2: Implement frontend usage fields**

Extend `UsageState` and render estimated token use plus remaining daily budget in Settings.

- [ ] **Step 3: Update docs**

Document `DAILY_AI_TOKEN_LIMIT`, the budget-exceeded behavior, and the fact that this is a local-first cost-control foundation rather than production billing.

- [ ] **Step 4: Verify full gates**

Run:

```powershell
npm run test:backend
npm run test:frontend
npm --prefix frontend run build
npm run lint
```

Expected: all pass.

