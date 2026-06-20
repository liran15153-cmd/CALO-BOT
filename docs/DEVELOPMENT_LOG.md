# Development Log

## 2026-06-20

- Fixed the coaching knowledge runtime gap: provider context was previously selected only by `intent`, so the current user message could not retrieve specific protocol knowledge from `coaching_knowledge.py`.
- Ran browser-based product QA against the local app covering onboarding, chat, plan creation, missed-workout adaptation, pain safety, extreme dieting, supplement guidance, workout logging, meal logging, image upload analysis, dashboard, usage tracking, and Chrome/in-app browser availability.
- Stopped chat screen mounts from creating empty duplicate chat sessions; the first real message now creates the backend session unless the user explicitly starts a new chat.
- Expanded safety detection for extreme dieting so numeric requests such as 900 calories/day or 6+ kg/month rapid loss are blocked before provider calls and recorded as safety events.
- Improved workout log parsing for exercise-first English/Hebrew phrasing and RPE extraction so logs can feed adaptation instead of staying only in free-text notes.
- Improved deterministic manual meal estimates to aggregate recognized simple items such as protein shake, Greek yogurt, and banana into separate `MealItem` rows and summed ranges.
- Tightened provider chat instructions to avoid raw Markdown headings/bold/table formatting in the current plain-text chat UI.
- Added backend stripping for common Markdown markers in provider chat responses after live QA still produced raw bold markers.
- Expanded Hebrew structured memory extraction for short workouts, after-work/evening schedule, Tuesday/Thursday evenings, dumbbells, bands, dislike of running, no jumps, plant-based/lactose notes, and knee pain/sensitivity.
- Added `caution_notes` to provider context for sensitive safety memories while filtering sensitive memories out of dashboard coach notes.
- Added deterministic local responses for common creatine guidance and knee/squat substitution requests to reduce provider cost and avoid unsafe or low-quality model wording.
- Added deterministic query-aware `retrieved_knowledge` selection for provider-backed chat, with compact topic/guidance/action/avoid/source hits and hard prompt-budget fitting.
- Wired the user message through `CoachEngine` and `ContextBuilder` into `CoachingKnowledgeService.for_provider_context(query=...)` without changing database schema or local-tool behavior.
- Added a deterministic `WorkoutPlanBuilder` for saved workout plans. It supports 1-4 week multi-week plans and one-off `single_session` workouts, stores planner metadata in `plan_json`, includes URL-bearing source references, and keeps one-off workouts from replacing the active current plan.
- Expanded workout plan schemas with `plan_type`, `duration_weeks`, `training_split`, day focus, estimated duration, exercise movement patterns, progressions, regressions, safety notes, `decision_inputs`, and `source_refs`.
- Connected recent workout-log adaptation signals to one-off planning so high effort, skipped sessions, or pain can reduce load before progression.
- Fixed QA-found Hebrew chat routing gaps: feminine workout-plan requests such as "תבני לי תוכנית" now use the local structured plan tool, and daily/weekly summary requests now use `SummaryService` instead of falling through to provider chat.
- Fixed false pain handling for workout logs with negated pain phrases such as "בלי כאב", so they no longer create safety overrides or saved `pain_flag=true` logs.
- Changed weekly summary persistence to reuse the current user/week row instead of creating duplicate `WeeklySummary` records on repeated reads.
- Expanded structured memory extraction for feminine lactose-sensitivity phrasing such as "רגישה ללקטוז".
- Updated product and coaching-knowledge docs with the deterministic planner rules and source-backed behavior.

## 2026-06-15

- Initialized local-first CALO Coach project.
- Chosen stack: FastAPI, SQLite, SQLAlchemy, React, Vite, TypeScript.
- Locked v1 scope to AI Fitness Coach only.
- Deliberately excluded WhatsApp, payments, cloud deployment, mobile, and medical claims from v1.
- Implemented onboarding, chat persistence, safety events, memory extraction, workout plans/logs, meal upload/manual logging, summaries, dashboard, settings export/reset, and usage tracking.
- Verified no-key AI behavior stays explicit instead of faking coach or vision output.

## 2026-06-16

- Added deterministic coach intent dispatch for workout plan creation, workout logging, and meal logging before generic AI chat.
- Made workout plan generation use saved profile availability, equipment, session length, preferred days, and limitations when the request is open-ended.
- Persisted generated workout days and exercises into row-level `Workout` and `WorkoutExercise` records in addition to `plan_json`.
- Added intent-aware memory filtering in the context builder.
- Moved dashboard aggregation and next-action logic into `DashboardService`.
- Changed empty dashboard nutrition estimates to return and render an empty state instead of `null-null`.
- Hardened meal image uploads with a 5 MB cap and image signature checks.
- Normalized configured image-analysis JSON into persisted meal calorie/macro ranges and detected `MealItem` rows.
- Hydrated the workouts UI from the current persisted plan and removed demo-filled workout form defaults.
- Displayed configured meal image ranges, detected items, and follow-up questions in the meals UI.
- Added `docs/RELEASE_CHECKLIST.md` to separate local-first readiness from public release blockers.
- Added `DAILY_AI_TOKEN_LIMIT`, budget-exceeded handling for configured chat and image analysis, and Settings visibility for remaining AI token budget.
- Added frontend error handling for failed local data export.
- Expanded safety guardrails for dangerous stimulant, steroid, or diuretic requests.

## 2026-06-19

- Switched user-visible coach responses, safety/fallback messages, local tool responses, dashboard actions, and frontend UI copy to Hebrew.
- Added RTL Hebrew app metadata while keeping API field names, provider statuses, model names, URLs, and environment variables as technical English identifiers.
- Added a versioned `CoachingKnowledgeService` with source-backed general fitness rules for activity targets, resistance training, progression, adherence, nutrition uncertainty, and safety boundaries.
- Injected `coaching_knowledge` through the context builder for provider-backed chat and updated the coach prompt to use it without claiming certification.
- Added Hebrew intent detection for workout-plan, workout-log, and meal-log requests.
- Expanded deterministic local workout plans with fuller movement-pattern coverage, progression, recovery, alternatives, and safety notes.
- Added compact goal playbooks, scenario adjustments, and exercise-selection rules to `CoachingKnowledgeService`.
- Made local workout-plan generation adjust basic reps, rest, progression and recovery notes by goal.
- Added preparticipation screening and referral rules to compact provider context.
- Mapped technical provider statuses to Hebrew labels in the UI while preserving API identifiers.
- Added Hebrew parsing for workout logs and Hebrew-safe local meal estimates.
- Sanitized image-analysis payloads so non-Hebrew provider text is not displayed directly.
- Translated upload/API error details that can surface to users.
- Expanded `CoachingKnowledgeService` with program-design variables, technique cues for major movement patterns, and deload/load-management rules.
- Kept provider context compact by sending summaries of the new knowledge instead of the full technique dataset.
- Added research-backed load monitoring and population-adjustment knowledge to `CoachingKnowledgeService`.
- Added `TrainingAdaptationService` and included `training_status` in provider context so the coach can adapt from recent workout logs without adding a new blocking path.
- Added research-backed sports-nutrition and body-composition knowledge for meal contexts: protein ranges, carbohydrate fueling, hydration, meal timing, and non-scale progress signals.
- Added full-coach workout knowledge for exercise prescription, simple periodization, cardiorespiratory intensity, warmup/mobility, reassessment, and adherence coaching.
- Added a structured exercise library for major movement patterns with muscles, coaching cues, common errors, regressions, progressions, and safety notes, while sending only a compact summary to provider context.
- Added goal-specific programming knowledge for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support, while sending only `goal_programming_summary` to provider context.
- Added structured cardio programming knowledge for aerobic base, aerobic efficiency, intervals, fat-loss support, and endurance-event preparation, while sending only `cardio_programming_summary` to workout provider context.
- Added session-structure coaching knowledge for exercise order, rest intervals, tempo, supersets/circuits, and warmup/ramp sets, while sending only `session_structure_summary` to workout provider context.
- Added readiness/recovery coaching knowledge for green/yellow/red-day decisions using RPE, sleep, stress, DOMS, performance trends, and safety boundaries, while sending only `readiness_recovery_summary` to workout provider context.
- Added load-prescription coaching knowledge for starting load selection, RIR/RPE calibration, set-to-set adjustments, next-session load decisions, submax/e1RM estimates, and heavy-load safety gates, while sending only `load_prescription_summary` to workout provider context.
- Added field-assessment coaching knowledge for repeatable baseline checks, including 6MWT, 2MST, chair stand, balance, TUG, and movement snapshots, while sending only `field_assessment_summary` to workout provider context.
- Added concurrent-training coaching knowledge for combining strength and aerobic work by goal priority, same-day order, interference management, modality choice, and recovery spacing, while sending only `concurrent_training_summary` to workout provider context.
- Added practical non-clinical nutrition coaching knowledge for plate building, protein anchors, produce/fiber habits, hydration, meal-prep fallback, workout-adjacent meals, and food-image uncertainty, while sending only `practical_nutrition_summary` to meal provider context.
- Added adherence micro-protocol knowledge for OARS-style coaching, barrier-to-plan mapping, implementation intentions, minimum viable workouts, self-monitoring feedback, relapse recovery, and autonomy-supportive choices, while sending only `adherence_micro_summary` to general-chat provider context.
- Added warmup/cooldown coaching knowledge for pulse raising, dynamic prep, ramp sets, static-stretching dosage, cooldown truthfulness, and DOMS framing, while keeping provider context compact through `warmup_mobility_summary`.
- Added program lifecycle coaching knowledge for normal weeks, reassessment cadence, plateau decisions, deload, maintenance, taper, test weeks, and controlled exercise changes, while keeping provider context compact through `periodization_summary`.
- Added exercise setup and equipment-safety coaching knowledge for machine adjustment, rack safeties, spotting, simple bracing/breathing, stable variation defaults, switching exercises when cueing fails, and equipment misuse checks, while keeping provider context compact through `instruction_coaching_summary`.
- Added progress-measurement coaching knowledge for goal-based metrics, strength/cardio/body-composition trends, adherence dashboard review, and reassessment decisions, while keeping provider context compact through `assessment_tracking_summary`.
- Added anatomy and muscle-map coaching knowledge for lower body, push, pull, core, accessories, and program balance by movement pattern, while keeping provider context compact through `exercise_library_summary`.
- Added supplement-education coaching knowledge for creatine, caffeine/pre-workout, protein powder, beta-alanine, electrolytes, low-evidence/high-risk products, and quality/scope boundaries, while keeping provider context compact through `supplement_education_summary`.
- Added advanced strength/hypertrophy coaching knowledge for volume landmarks, proximity to failure, failure dosage, top-set/back-off structures, specialization blocks, plateau troubleshooting, and exercise rotation/specificity, while keeping provider context compact through `volume_progression_summary`.
- Hid unknown internal UI identifiers for dashboard goals and workout log status/confidence behind Hebrew fallback labels.
- Added advanced recovery/readiness coaching knowledge for sleep debt, high-stress days, DOMS, conservative illness return, travel/maintenance weeks, overreaching signs, and recovery-priority ordering, while keeping provider context compact through `readiness_recovery_summary`.
- Added Hebrew coaching-language knowledge for terminology, one-action response shape, autonomy-supportive plain language, jargon policy, and non-punitive correction patterns, while keeping provider context compact through `coaching_behavior`.
- Added exercise-science foundation knowledge for energy systems, planes of motion, joint actions/levers, force vectors, stability, fatigue, and motor learning, while keeping provider context compact through `exercise_prescription_summary`.
- Added program-quality audit knowledge for reviewing existing workout plans by goal fit, weekly structure, movement-pattern coverage, volume/recovery, progression logic, exercise selection, adherence feasibility, and safety scope, while keeping provider context compact through `program_design_summary`.
- Added walking/running coaching knowledge for run-walk starts, easy-run intensity, running-volume progression, long-run management, intervals/hills, runner strength support, cadence/surface changes, and missed-run adjustment, while keeping provider context compact through `cardio_programming_summary`.
- Added speed/agility/plyometric coaching knowledge for landing mechanics, low-level jump entry, jump progression, sprint acceleration, deceleration/change of direction, reactive agility, rest/order, impact volume, and surface selection, while keeping provider context compact through `exercise_prescription_summary`.
- Added daily activity/NEAT coaching knowledge for step baselines, gradual step targets, movement breaks, movement snacks, post-meal walks, active errands/commute, low-impact days, fat-loss support, and calorie-burn uncertainty, while keeping provider context compact through general-chat-only `daily_activity_summary`.
- Added environmental training risk knowledge for heat, heat acclimatization, heat-illness warning signs, AQI/air quality, cold/wind chill, and outdoor-session decisions, while keeping provider context compact through general-chat `environment_training_summary` plus one short workout cardio cue.
- Added body-composition strategy coaching knowledge for energy balance, fat-loss phases, muscle-gain phases, recomposition, scale trends, optional non-scale measures, plateau review, and maintenance phases, while keeping workout provider contexts unchanged and sending only compact `body_recomposition_summary` to general/meal contexts.
- Added common fitness-myth coaching knowledge for spot reduction, DOMS, sweat, fasted cardio, and strength-training bulky fear, while keeping provider context compact through general-chat-only `fitness_myths_summary`.
- Removed generic `nutrition_coaching_rules` from workout provider contexts to restore prompt headroom while preserving nutrition guidance in general and meal contexts.
