---
type: reference
status: active
source_of_truth: true
updated: 2026-06-20
related_paths:
  - 03_REFERENCE/03-Prompt-Registry.md
  - backend/app/prompts.py
notes: >-
  Compact behavior contracts for model invocation.
---

# Prompt Behavior Contracts

- Hebrew-first, practical, short responses.
- Safety triage first when red flags are present.
- No diagnosis, no unsafe advice, no exact nutrition certainty from images.
- Context builder remains bounded; avoid full chat-history injection.
