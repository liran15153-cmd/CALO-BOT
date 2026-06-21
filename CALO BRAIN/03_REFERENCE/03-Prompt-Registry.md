---
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Provider-backed coach chat now passes through `token_budgeting.build_optimized_chat_request()`: the runtime keeps the `context.coaching_knowledge` contract but removes duplicate current-message history, trims memory/history/plan fields, and records a legacy full-context baseline so token savings are measured instead of guessed.
- Usage logging records token categories for `system_prompt`, `history`, `memory`, `tools`, `message`, and `output`; configured Anthropic calls use provider usage totals and `messages.count_tokens` for component counts when available, with local estimates only as fallback.
- Default configured chat model is `claude-haiku-4-5`; `ANTHROPIC_CHAT_MODEL` is only an explicit override.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
type: reference
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
status: active
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
source_of_truth: true
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
updated: 2026-06-20
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
related_paths:
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
  - backend/app/prompts.py
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
notes: >-
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
  Prompt constraints and provider context guidance
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.
---
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
- Require Hebrew-first user-facing output, allowing short English fitness/nutrition terms inside otherwise Hebrew responses
- Require natural Israeli fitness Hebrew, not literal translation. Use terms such as סטים, חזרות, דילואד/שבוע הורדת עומס, RPE, RIR, DOMS, full-body, Zone 2, and progressive overload when they are clearer than forced Hebrew.
- Avoid broken literal phrasing such as מערכות for sets, הישנויות for reps, פריקת עומס for deload, or long translated definitions in ordinary chat.
- If the user asks not to be addressed in masculine or feminine language, use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms.
- Prefer short outputs
- Refuse unsafe requests conservatively
- Use `coaching_knowledge` as bounded general coaching knowledge
- Keep coaching knowledge compact; retrieve decision rules, not long manuals
- Include compact program-design, deload, and technique-cue summaries for workout planning questions
- Include compact program-quality audit language inside `program_design_summary`; do not send the full `program_quality_audit_protocols` table to the model
- Include compact `program_adaptation_summary` for workout-plan and workout-log contexts; do not send the full adaptation protocol table to the model
- Include goal-metric and trend language inside `assessment_tracking_summary`; do not send the full `progress_measurement_protocols` table to the model
- Include compact `goal_programming_summary` for workout-plan and workout-log contexts; do not send the full `goal_specific_programming` table to the model
- Include compact `profile_programming_summary` for workout-plan and workout-log contexts; do not send the full `client_profile_programming` table to the model
- Include compact `limitation_adaptation_summary` for workout-plan and workout-log contexts; do not send the full `movement_limitation_adaptations` table to the model
- Include compact `special_population_summary` for workout-plan and workout-log contexts; do not send the full `special_population_programming` table to the model
- Include compact `instruction_coaching_summary` for workout-plan and workout-log contexts; do not send the full `coaching_instruction_protocols` or `exercise_setup_safety_protocols` tables to the model
- Include compact `weekly_structure_summary` for workout-plan and workout-log contexts; do not send the full `weekly_structure_protocols` table to the model
- Include compact `volume_progression_summary` for workout-plan and workout-log contexts; do not send the full `volume_progression_protocols` table to the model
- Include advanced strength/hypertrophy language inside `volume_progression_summary`; do not send the full `advanced_strength_hypertrophy_protocols` table to the model
- Include compact `load_prescription_summary` for workout-plan and workout-log contexts; do not send the full `load_prescription_protocols` table to the model
- Include compact `concurrent_training_summary` for workout-plan and workout-log contexts; do not send the full `concurrent_training_protocols` table to the model
- Include compact `equipment_substitution_summary` for workout-plan and workout-log contexts; do not send the full `equipment_substitution_protocols` table to the model
- Include compact `session_structure_summary` for workout-plan and workout-log contexts; do not send the full `session_structure_protocols` table to the model
- Include compact `readiness_recovery_summary` for workout-plan and workout-log contexts; do not send the full `readiness_recovery_protocols` table to the model
- Include advanced recovery/readiness language inside `readiness_recovery_summary`; do not send the full `advanced_recovery_readiness_protocols` table to the model
- Include program lifecycle language inside `periodization_summary`; do not send the full `program_lifecycle_protocols` table to the model
- Include compact `field_assessment_summary` for workout-plan and workout-log contexts; do not send the full `field_assessment_protocols` table to the model
- Include compact exercise-science foundation language inside `exercise_prescription_summary`; do not send the full `exercise_science_foundations` table to the model
- Include compact speed/agility/plyometric language inside `exercise_prescription_summary`; do not send the full `speed_agility_plyometric_protocols` table to the model
- Include compact `cardio_programming_summary` for workout-plan and workout-log contexts; do not send the full `cardio_programming` table to the model
- Include compact walking/running language inside `cardio_programming_summary`; do not send the full `walking_running_protocols` table to the model
- Include compact `daily_activity_summary` for general-chat contexts; do not send the full `daily_activity_neat_protocols` table to the model
- Include compact `environment_training_summary` for general-chat contexts; do not send the full `environment_training_risk_protocols` table to the model
- Keep workout environment guidance as a single compact cue inside `cardio_programming_summary`; do not add a separate workout environment section without compressing another summary
- Include compact `fueling_risk_summary` for general-chat contexts; do not send the full `low_energy_availability_protocols` table to the model
- Fold one under-fueling cue into workout-log readiness and meal body-composition summaries instead of adding bulky provider sections
- Include compact warmup/cooldown guidance inside `warmup_mobility_summary`; do not send the full `warmup_cooldown_protocols` table to the model
- Include exercise-prescription, periodization, cardiorespiratory, and warmup/mobility summaries only for workout-plan and workout-log contexts
- Include compact adherence coaching in all provider contexts because motivation and missed-workout questions may be classified as general chat
- Include compact `adherence_micro_summary` for general-chat contexts only; do not send the full `adherence_micro_protocols` table to the model
- Include compact Hebrew-language behavior rules through `coaching_behavior`; do not send the full `hebrew_coaching_language_protocols` table to the model
- Include compact `fitness_myths_summary` for general-chat contexts only; do not send the full `common_fitness_myth_protocols` table to the model
- Include only `exercise_library_summary`, not the full structured `exercise_library`, in provider context
- Include only compact muscle-pattern language inside `exercise_library_summary`; do not send the full `anatomy_muscle_map` table to the model
- Include compact sports-nutrition and body-composition summaries only for meal and meal-image contexts
- Include compact `body_recomposition_summary` for general-chat, meal-log, and meal-image contexts; do not send the full `body_composition_strategy_protocols` table to the model
- Include compact `practical_nutrition_summary` only for meal and meal-image contexts; do not send the full `practical_nutrition_protocols` table to the model
- Include compact `supplement_education_summary` for general-chat and meal contexts; do not send the full `supplement_education_protocols` table to the model
- Do not claim the coach is certified or clinically qualified

## Current Implementation Notes

- Coach chat uses a short coach prompt plus bounded context JSON, including compact `coaching_knowledge` with program design variables, deload rules, safety boundaries, and technique cue summaries.
- Coach chat now carries a compact Hebrew style contract: write natural Israeli Hebrew, do not sound machine-translated, do not translate fitness terms literally, keep normal gym terms where Israeli users expect them, honor explicit neutral-address requests, and stay plain text without raw Markdown.
- Common Hebrew fitness-term questions such as RPE/RIR, DOMS, deload, progression, hypertrophy, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image uncertainty are handled locally before provider routing when a deterministic short answer is enough.
- Provider-backed chat now passes the current user message into the context builder so `coaching_knowledge` can add compact query-specific `retrieved_knowledge` hits. The model should use those hits as the most relevant coaching knowledge for the immediate answer, while still respecting safety and Hebrew-first response rules.
- Full protocol tables are still kept out of prompts. `retrieved_knowledge` is a small runtime selection layer, not a dump of `coaching_knowledge.py`.
- Workout contexts include compact program-quality audit language so the coach can review an existing plan for goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise selection, adherence feasibility, and safety scope without receiving the full audit table.
- Workout contexts include `goal_programming_summary` for strength, hypertrophy, muscular endurance, power, beginner foundation, and fat-loss support.
- Workout contexts include `profile_programming_summary` so the coach can choose a planning path by user type, goal, available time, and equipment without receiving the full protocol table.
- Workout contexts include `limitation_adaptation_summary` so the coach can modify common painful or limited movement patterns with range, load, angle, and exercise swaps without diagnosing injury.
- Workout contexts include `special_population_summary` for youth, pregnancy/postpartum, chronic conditions/disabilities, and older-adult multicomponent training without sending clinical protocols to the model.
- Workout contexts include `instruction_coaching_summary` for session flow, show-tell-do teaching, cue choice, feedback frequency, setup/safeties/bracing reminders, and safety technique checks without sending the full protocol tables to the model.
- Workout contexts include `weekly_structure_summary` so the coach can choose between full-body, upper/lower, push/pull/legs, or simpler weekly structures by availability, training history, recovery, and target muscle-group frequency.
- Workout contexts include `volume_progression_summary` so the coach can decide whether to add reps, load, sets, or recovery using weekly volume, 2-for-2/double progression, and RIR/RPE instead of guessing.
- Workout contexts include compact advanced strength/hypertrophy guidance through `volume_progression_summary`: use failure sparingly, treat specialization as temporary, troubleshoot plateau by changing one variable, and keep specificity when rotating exercises.
- Workout contexts include `load_prescription_summary` so the coach can choose starting loads, adjust between sets, set next-session load, and treat e1RM as an estimate rather than pushing max testing.
- Workout contexts include `concurrent_training_summary` so the coach can combine strength and aerobic work by goal priority, order same-day sessions, and manage interference without fear-based “cardio kills gains” language.
- Workout contexts include `equipment_substitution_summary` so the coach can keep the same training intent when the user only has bodyweight, bands, dumbbells, machines/cables, or no load increase available.
- Workout contexts include `session_structure_summary` so the coach can order exercises, set rest, use tempo, choose supersets/circuits, and preserve warmup/ramp sets without receiving the full protocol table.
- Workout contexts include `readiness_recovery_summary` so the coach can decide whether to progress, maintain, reduce load, or switch to a technical/recovery version from RPE, sleep, DOMS, stress, and red-flag boundaries.
- Workout contexts include compact advanced recovery/readiness language for sleep debt, stress, DOMS, illness return, travel/maintenance weeks, and accumulated-load signs without receiving the full protocol table.
- Workout contexts include program lifecycle language through `periodization_summary`: normal week, deload, maintenance, test week, taper, and plateau decisions should be selected from logs and goals, not improvised as generic motivation.
- Workout contexts include `field_assessment_summary` so the coach can pick one to three repeatable baselines, such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots, while treating results as personal tracking rather than diagnosis.
- Workout contexts include progress-measurement language through `assessment_tracking_summary`: pick metrics by goal, use strength/cardio/body-composition trends, and translate weekly review into one next action.
- Workout contexts include compact exercise-science foundations through `exercise_prescription_summary`: energy systems, motion planes, load vectors, stability, fatigue, and cueing should inform decisions without becoming a lecture.
- Workout contexts include compact speed/agility/plyometric guidance through `exercise_prescription_summary`: jumps and sprints should be high-quality work before fatigue, with landing control and progression before more impact.
- Workout contexts include `cardio_programming_summary` for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, and endurance-event distribution.
- General-chat contexts include `daily_activity_summary` for step baselines, gradual step targets, sitting breaks, movement snacks, and calorie-burn uncertainty without receiving the full NEAT protocol table.
- General-chat contexts include `environment_training_summary` for heat, AQI/air quality, cold and wind-chill adjustments without receiving the full environmental risk table. Workout contexts only carry one compact environment cue inside `cardio_programming_summary`.
- General-chat contexts include `fueling_risk_summary` for REDs/low-energy-availability caution. Workout-log and meal contexts only carry compact folded cues for תדלוק/אכילה so prompt size stays bounded.
- Workout contexts include precise warmup/cooldown guidance: dynamic warmup and ramp sets before demanding work, static stretching for flexibility when appropriate, and no promise that cooldown/stretching prevents DOMS.
- Workout contexts add compact full-coach guidance for FITT-VP prescription, periodization, aerobic intensity, warmups, mobility, and reassessment.
- Workout contexts intentionally omit generic `nutrition_coaching_rules` to keep prompt headroom; general and meal contexts carry nutrition/body-composition guidance instead.
- Workout contexts include `program_adaptation_summary` so the coach can interpret logs and adjust one variable at a time for progression, fatigue, plateau, missed sessions, exercise substitution, or return after a break.
- All provider contexts include compact behavior-change coaching: ABC conversation, barrier handling, tracking, if-then fallback plans, and low-friction return after missed actions.
- General-chat contexts include `adherence_micro_summary` for OARS-style short coaching, identifying one barrier, if-then/minimum viable actions, and offering two safe choices without controlling language.
- General-chat contexts include `fitness_myths_summary` for common myth questions: spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk. The coach should correct the misconception briefly and redirect to one practical action.
- All provider contexts include compact Hebrew-language behavior rules: natural Hebrew, one action, no shame/mandatory tone, and untranslated fitness terms such as RPE/RIR/DOMS/HIIT/Zone 2 when they are clearer with a short explanation.
- Workout contexts add a compact exercise-library summary for major movement patterns, muscles, cues, regressions, progressions, and common errors.
- Workout contexts include compact anatomy language through `exercise_library_summary`: quads/glutes/hamstrings for lower body, chest/shoulders/triceps for push, back/scapula/biceps for pull, and core as a stabilizing system rather than a spot-reduction promise.
- Meal contexts add compact sports-nutrition guidance for protein, carbohydrates, hydration, meal timing, and body-composition coaching without sending a long nutrition manual.
- General-chat and meal contexts add `body_recomposition_summary` for מאזן קלורי, גירעון/עודף, ריקומפ, חיטוב/מסה, מגמת משקל, and non-scale progress without sending the full strategy table.
- Meal contexts add `practical_nutrition_summary` for plate structure, protein anchors, fiber/produce, hydration, meal-prep fallback, and uncertainty language without sending the full protocol table.
- General-chat and meal contexts add `supplement_education_summary` for creatine, caffeine/pre-workout, protein powder, electrolytes, low-evidence products, and supplement quality/scope boundaries.
- Configured coach chat has a response guard: provider text with no Hebrew characters is replaced by a Hebrew retry message.
- Configured coach chat also rejects dominant-English provider text, generic English headings, and generic English phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, and `protein timing`. It still allows professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, and progressive overload inside otherwise natural Hebrew responses.
- Configured coach chat also rejects provider text that violates an explicit neutral-address request. If the intent has a vetted local answer, the local Hebrew answer is returned; otherwise the user sees a neutral retry message and the offending provider text is not stored as the coach response.
- Configured coach chat strips common Markdown markers from provider text before language validation and storage because the chat UI renders plain text.
- Common creatine questions and knee-sensitive squat substitution requests are local deterministic chat intents, so they do not depend on provider output quality for basic safe coaching.
- Meal image analysis asks for JSON with ranges, uncertainty, and Hebrew-first user-facing strings.
- Parsed image-analysis payloads are sanitized so non-Hebrew or dominant-English provider text is not shown directly to the user.
- No-key fallback returns an explicit Hebrew provider-not-configured message.
- Safety classification also carries the Hebrew-first output guard, even though the current local safety layer handles most classifications without an external model.
- Workout and summary flows are deterministic in v1 where that is safer than pretending AI output exists.

