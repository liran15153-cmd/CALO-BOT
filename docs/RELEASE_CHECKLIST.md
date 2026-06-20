# Release Checklist

## Current Release Target

CALO Coach is ready for local-first use and continued product testing on a trusted machine.

It is not ready for public internet deployment until the blockers below are addressed.

## Verified Local Gates

- Backend tests pass.
- Frontend tests pass.
- Frontend production build passes.
- Root lint command passes.
- Frontend production dependency audit reports no known vulnerabilities.
- Root production dependency audit reports no known vulnerabilities.
- Provider-backed chat and meal image analysis stop before external calls when the daily token budget is spent.

## Public Release Blockers

- Add authentication and per-user ownership checks.
- Replace the default local-user resolver with a real identity boundary.
- Protect export and reset routes behind authentication and user ownership.
- Add database migrations instead of relying only on `create_all`.
- Add deployment config and production environment guidance.
- Harden uploads with image re-encoding, metadata stripping, retention cleanup, and malware scanning if exposed publicly.
- Add stronger Python linting/static analysis such as Ruff and a Python dependency audit such as `pip-audit`.
- Decide whether Supabase/RLS is part of the product. No Supabase code exists in this repo today.
- Expand the safety layer beyond v1 keyword rules before marketing this as a broad wellness safety system.

## WhatsApp Readiness

The current backend is adapter-friendly because the web UI talks to services through APIs and the coach engine owns intent dispatch. A WhatsApp adapter should call the same services, but it must first add channel identity mapping and user ownership.
