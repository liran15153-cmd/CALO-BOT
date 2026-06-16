# AI Prompts

Prompts are intentionally short and task-specific.

## Prompt Types

- Coach chat
- Workout generation
- Meal image analysis
- Meal text parsing
- Memory extraction
- Weekly summary
- Safety classification

## Prompt Constraints

- Use compact structured context only
- Do not send full chat history
- Do not send the entire database
- Prefer short outputs
- Refuse unsafe requests conservatively

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON.
- Meal image analysis asks for JSON with ranges and uncertainty.
- No-key fallback returns an explicit provider-not-configured message.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
