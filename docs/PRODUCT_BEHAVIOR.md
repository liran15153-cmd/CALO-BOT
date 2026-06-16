# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

## Data Controls

Settings exposes provider status, usage totals, JSON export, and local reset. It must not expose secrets.
