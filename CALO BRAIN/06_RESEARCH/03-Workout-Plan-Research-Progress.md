# Workout Plan Research Progress

Status: active. Do not close this research loop until the user writes "סיים את ה-RESEARCH" or "FINISH RESEARCH".

## Loop 1 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training guidelines update: major muscle groups at least twice per week, consistency before complexity, goal-specific loading, and home/band/bodyweight validity.
- CDC adult physical activity guidelines: 150 minutes moderate or 75 minutes vigorous aerobic activity weekly plus 2 days strength for major muscle groups.
- NSCA resistance training frequency guidance: frequency depends on exercise selection, muscle groups per session, volume, intensity, training status, and real schedule constraints.
- HPRC/NSCA exercise-order guidance: power/technical and multi-joint exercises before accessory work; balance push/pull and upper/lower demands.
- Schoenfeld et al. 2021 loading review: hypertrophy can occur across broad loads when effort is sufficient; moderate loads are often practical.
- Grgic et al. 2022 training-to-failure review: failure is not required for strength or hypertrophy in most practical plans.
- Exercise is Medicine low-back-pain guidance: avoid symptom-provoking movement, return gradually, and use conservative strength exposure.
- Mayo Clinic exercise warning symptoms: stop for dizziness, unusual shortness of breath, chest pain, or irregular heartbeat and seek appropriate professional help.

### Rules extracted

- Separate plan horizons in app state: `single_workout`, `weekly_plan`, `two_week_plan`, `monthly_plan`.
- A single workout is saved as a one-off and must not become or replace the active program.
- Weekly plans are execution schedules, not full periodization.
- Two-week plans should keep the same base split and progress one variable in week 2.
- Monthly plans should use a simple four-week arc: baseline, small progression, small progression, then maintenance/deload/check based on logs.
- Ask only for missing critical information: goal, equipment/location, days, session duration, experience, and pain/limitation. Otherwise infer conservatively and state assumptions.
- Hebrew limitation language such as "ברך רגישה" should be treated as a soft safety/limitation signal, not ignored.

### Changes made

- Updated the workout plan schema to accept and emit the four canonical plan horizons while keeping old `single_session` and `multi_week` request aliases compatible.
- Reworked `WorkoutPlanBuilder` inference for English and Hebrew horizon terms, including today/one-off, weekly, two-week, and monthly requests.
- Updated `WorkoutService` so single workouts are not active plans and persistent plans only replace other persistent plans.
- Updated chat and workout-plan API replacement logic to use persistent-plan semantics instead of checking only `multi_week`.
- Added compact horizon rules to `CoachingKnowledgeService` without breaking provider-context budget tests.
- Updated frontend plan-type labels for `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan`.
- Expanded soft pain/limitation detection for Hebrew sensitivity phrasing such as "ברך רגישה".

### Tests and checks

- `python -m pytest backend/tests/test_workout_plan_builder.py backend/tests/test_workout_schema.py backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_intent_service.py backend/tests/test_coach_engine.py backend/tests/test_context_builder.py backend/tests/test_token_optimization.py backend/tests/test_coaching_knowledge.py -q` -> 272 passed.
- `python -m pytest backend/tests/test_safety_service.py backend/tests/test_coach_engine.py backend/tests/test_workout_plan_builder.py backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_intent_service.py backend/tests/test_coaching_knowledge.py -q` -> 253 passed.
- `python -m pytest backend/tests -q` -> 424 passed.
- `npm.cmd --prefix frontend test -- --run src/WorkoutsPanel.test.tsx` -> 14 passed.
- `npm.cmd run build` -> passed.

### Manual Hebrew probes

- "תן לי אימון זריז להיום בבית, 20 דקות, בלי ציוד" -> `single_workout`, duration 1, days 1, not current, no pending replacement.
- "תבנה לי תוכנית קצרה לשבוע הקרוב, 20 דקות ביום" -> `weekly_plan`, duration 1, days 3, current when no persistent plan exists.
- "תבנה לי תוכנית לשבועיים עם משקולות יד למתחיל" -> `two_week_plan`, duration 2, saved as replacement candidate when a weekly plan is active.
- "תבני לי תוכנית חודשית למכון, 4 ימים בשבוע, עם ברך רגישה" -> `monthly_plan`, duration 4, limitation saved as "רגישות בברך", safety acknowledgement included.

### Failures and fixes

- Initial knowledge-center patch exceeded strict provider-context budget. Fixed by keeping detailed horizon rules retrievable and compressing always-sent summaries.
- Initial manual probe showed a one-off workout became the active plan. Fixed by preventing `single_workout` from setting `is_current`.
- Initial manual probe showed "ברך רגישה" was not passed into plan limitations. Fixed by expanding soft limitation detection and adding a regression assertion.

### Next research target

- Loop 2 should deepen goal-specific programming quality: hypertrophy vs strength vs fat-loss support vs endurance/mobility, including volume landmarks, cardio placement, home/dumbbell/bodyweight substitutions, and Hebrew natural-language output shape for each goal.

## Loop 2 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training update: strength uses heavier loading, hypertrophy is more volume-driven, power uses moderate load moved quickly, and bands/bodyweight/home training can be effective.
- NSCA frequency guidance: beginners often fit 2-3 full-body sessions; intermediate users can use 3-4 sessions and split routines; total workload and non-training stress must constrain frequency.
- HPRC/NSCA exercise selection: organize by power, multi-joint, then assistance; alternate upper/lower or push/pull when useful; balance push and pull in 4-6 exercise sessions.
- CDC adult activity guidance: fat-loss support and general fitness should include aerobic activity plus 2+ days of strengthening.
- Schoenfeld et al. 2021: strength is load-specific for 1RM, hypertrophy can occur across broad loading zones, moderate loads are often most practical, and very heavy high-volume hypertrophy work can increase joint stress.
- Grgic et al. 2022: training to failure is not required for most strength or hypertrophy gains.

### Rules extracted

- Hypertrophy: prioritize weekly volume the user can recover from; keep most sets near 1-3 RIR, not constant failure.
- Strength: place main lifts early, use longer rests, and progress load only when technique and pain status are clean.
- Fat-loss support: preserve strength and consistency; add walking/aerobic work gradually; do not frame training as punishment.
- Endurance: build easy/moderate base first using talk-test/RPE logic; add duration/frequency before intensity.
- Mobility: progress usable range, control, breathing, and pain-free movement before external load.
- Equipment constraints: substitute by movement pattern rather than by exercise name.

### Changes made

- Expanded Hebrew/English goal inference for hypertrophy, strength, fat-loss slang such as "חיטוב", endurance phrases such as "לב ריאה", and mobility phrases such as "מוביליטי" and "גמישות".
- Added mobility-specific training-variable overrides so mobility plans produce range-of-motion progression, conservative rest, and no-pain recovery notes.
- Added `goal_specific_plan_protocols` to the knowledge center for hypertrophy, strength, fat-loss support, endurance, mobility, and equipment constraints.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_plan_builder.py backend/tests/test_coaching_knowledge.py backend/tests/test_coach_engine.py backend/tests/test_safety_service.py -q` -> 216 passed.

### Manual Hebrew probes

- "תבנה לי תוכנית חיטוב ביתית לשבוע" -> `goal=lose_fat`, `plan_type=weekly_plan`, includes light cardio/walking and non-punitive progression.
- "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה" -> `goal=improve_endurance`, `plan_type=two_week_plan`, progresses duration/frequency before intensity.
- "תן לי תוכנית מוביליטי חודשית עם משקל גוף" -> `goal=improve_fitness`, `plan_type=monthly_plan`, progression centers on range of motion, control, breathing, and no sharp pain.

### Failures and fixes

- No Loop 2 test failures after implementation.

### Next research target

- Loop 3 should improve actual exercise selection by equipment and goal: gym machines vs dumbbells vs bodyweight, beginner/intermediate/advanced exercise substitutions, and whether monthly plans need explicit week-by-week progression metadata instead of only a single progression rule.

## Loop 3 - 2026-06-24

### Sources carried forward

- ACSM, NSCA, Schoenfeld et al., and Grgic et al. support progression that changes one variable at a time, preserves recovery, and does not require constant failure or complex periodization for general users.

### Rules extracted

- A monthly plan needs a visible week-by-week arc, not only a general progression sentence.
- A two-week plan should show week 1 as calibration and week 2 as one conservative progression if logs are stable.
- A weekly plan should focus on execution and tracking, not progression complexity.
- A single workout should include tracking guidance but should not imply an active multi-week program.

### Changes made

- Added `progression_schedule: list[str]` to `StructuredWorkoutPlan`.
- Added generated progression schedules for `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan`.
- Kept schedules inside saved `plan_json`, so plans remain structured app data.
- Updated frontend `WorkoutPlan` type to accept `progression_schedule`.

### Tests and checks

- `python -m pytest backend/tests/test_workout_schema.py backend/tests/test_workout_plans_api.py backend/tests/test_workout_plan_builder.py backend/tests/test_coach_engine.py -q` -> 98 passed.
- `npm.cmd run build` -> passed.

### Manual Hebrew probes

- "תוכנית לשבוע הקרוב עם משקל גוף" -> `weekly_plan`, schedule length 1.
- "תוכנית לשבועיים עם משקולות" -> `two_week_plan`, schedule length 2 with "שבוע 2" progression.
- "תוכנית חודשית למכון" -> `monthly_plan`, schedule length 4 with week 4 check/maintenance/deload logic.

### Failures and fixes

- No Loop 3 failures after implementation.

### Next research target

- Loop 4 should improve exercise selection by equipment and goal: gym machine choices, dumbbell-only substitutions, bodyweight progression, beginner/intermediate/advanced complexity, and explicit substitutions in generated plans.

## Loop 4 - 2026-06-24

### Sources carried forward

- ACSM 2026: bands, bodyweight and home routines can produce meaningful strength, hypertrophy and function benefits when effort and progression are appropriate.
- NSCA frequency guidance: beginner, intermediate and advanced users tolerate different frequencies and split complexity; total workload and life stress constrain progression.
- HPRC/NSCA exercise selection: full-body, upper/lower and muscle-group splits are valid for different contexts; sessions should balance push/pull and can alternate upper/lower or push/pull for recovery.

### Rules extracted

- Substitute by movement pattern first: squat, hinge, horizontal push, horizontal pull, vertical push/pull, single-leg and core.
- Beginner bodyweight plans should start with stable, supported options before complex variants.
- Dumbbell-only plans should not leak machine/cable alternatives.
- Gym plans can use machines/cables for stability, but machines are not required for progress.
- Advanced bodyweight plans can progress via unilateral work, slower tempo and pauses.

### Changes made

- Added equipment-mode mapping inside the existing exercise catalog: `gym`, `dumbbells`, `bands`, `bodyweight`.
- Added experience-aware exercise names for beginner/intermediate/advanced users.
- Replaced generic alternatives with equipment-specific substitutions by movement pattern.
- Added `experience_level` rules to `goal_specific_plan_protocols`.
- Cleaned visible exercise names to keep Hebrew-first wording.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py backend/tests/test_coach_engine.py backend/tests/test_workout_schema.py -q` -> 205 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 131 passed after Hebrew wording cleanup.

### Manual Hebrew probes

- Beginner no-equipment weekly plan -> starts with `סקוואט לקופסה`, `שכיבת סמיכה בשיפוע`, `משיכת מגבת איזומטרית`, and bodyweight alternatives.
- Dumbbells-only two-week plan -> uses dumbbell squat, floor press, row, and RDL variants without machine names.
- Gym monthly plan -> uses machine/cable-friendly options and gym alternatives.
- Advanced bodyweight weekly plan -> uses harder bodyweight variants such as split squat, slow push-up and single-leg hinge.

### Failures and fixes

- Manual probe exposed visible `RDL` English abbreviation. Replaced it with Hebrew-first `דדליפט רומני`.

### Next research target

- Loop 5 should improve how generated plans communicate substitutions and assumptions to the user: critical missing-info policy, explicit assumptions, and natural Hebrew summaries without long questionnaires.

## Loop 5 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- CDC adult physical activity guidelines: https://www.cdc.gov/physical-activity-basics/guidelines/adults.html
- NSCA resistance training frequency guidance: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- HPRC/NSCA exercise selection and order: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training

### Rules extracted

- A useful plan can start before every preference is known, but missing defaults must be conservative and visible.
- Critical info for plan quality remains goal, equipment/location, weekly availability, session duration, experience level, and pain/limitation status.
- If safety-critical symptoms or strong pain signals appear, the bot should adapt or stop; if ordinary plan inputs are missing, it should infer and state assumptions instead of opening a long questionnaire.
- User-facing Hebrew should expose only the most important assumptions, while the saved plan should keep the full assumption list for auditability.

### Changes made

- Added structured `assumptions` to `WorkoutPlanningInput` and persisted them under `decision_inputs.assumptions`.
- `WorkoutService.generate_plan` now records when it defaults plan horizon, goal, days per week, session length, equipment, and experience level.
- Chat workout-plan responses now include a short Hebrew `הנחות:` line with up to two assumptions.
- Updated the coaching knowledge center critical-info policy to require saved assumptions and concise Hebrew surfacing.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request backend/tests/test_coaching_knowledge.py -q` -> 133 passed.
- `python -m pytest backend/tests -q` -> 429 passed.

### Manual Hebrew probes

- "תבנה לי תוכנית אימונים" -> `monthly_plan`, response includes two assumptions, saved plan includes six conservative assumptions.
- "תן לי אימון אחד להיום בבית בלי ציוד, 25 דקות" -> `single_workout`, no active-plan replacement, response states only missing goal and experience assumptions.
- "תבנה לי תוכנית חודשית למכון, 4 ימים בשבוע, יש לי כאב ברך קל" -> pain-aware response, monthly candidate behavior preserved, assumptions saved.

### Failures and fixes

- First manual probe command exited nonzero because Windows kept the temporary SQLite file locked during cleanup. Closed the DB/session, disposed the engine, removed the leftover temp directory, and reran successfully.

### Next research target

- Loop 6 should improve plan output usability: substitutions/tracking guidance by horizon, what the user sees in saved plan details, and whether weekly/monthly plans expose progression and replacements clearly enough for real use.

## Loop 6 - 2026-06-24

### Sources reviewed

- CDC intensity and talk-test/RPE guidance: https://www.cdc.gov/physical-activity-basics/measuring/index.html
- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- NSCA resistance training frequency guidance: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- HPRC/NSCA exercise selection and order: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training

### Rules extracted

- A saved plan needs execution feedback loops, not only exercises: completion status, RPE, pain, key lift performance, and short notes.
- Tracking should match plan horizon: one workout records what happened, weekly plans check adherence, two-week plans decide whether week 2 can progress, monthly plans review each week before load/volume changes.
- Substitutions should be visible near exercises so the plan can be used when equipment, pain, or time changes.
- Natural Hebrew matters in generated plan text; English exercise shorthand should not leak into user-visible alternatives.

### Changes made

- Added `tracking_guidance` to `StructuredWorkoutPlan` and generated it by plan horizon.
- Included `tracking_guidance` and `progression_schedule` in compact current-plan context.
- Updated the workout-plan knowledge center with a `tracking_guidance_policy`.
- Updated the frontend `WorkoutPlan` type and workouts panel to show exercise notes, alternatives, progression schedule, and tracking guidance.
- Replaced generated `step-up` wording with natural Hebrew `עלייה נמוכה למדרגה` / `עלייה למדרגה עם משקולות`.

### Tests and checks

- `python -m pytest backend/tests/test_workout_schema.py backend/tests/test_workout_plans_api.py backend/tests/test_context_builder.py -q` -> 47 passed.
- `npm.cmd run build` -> passed.
- First `python -m pytest backend/tests -q` after the frontend/API change failed once with Windows `WinError 10055` while creating a TestClient event loop after 428 tests had passed. The isolated failed test passed.
- Final `python -m pytest backend/tests/test_workout_schema.py backend/tests/test_workout_plans_api.py backend/tests/test_context_builder.py backend/tests/test_coaching_knowledge.py -q` -> 158 passed.
- Final `python -m pytest backend/tests -q` -> 429 passed.

### Manual Hebrew probes

- Weekly bodyweight plan -> progression schedule length 1, tracking guidance includes RPE/pain/completion, first exercise alternatives are Hebrew.
- Two-week dumbbell plan -> week 2 progression remains conditional on stable logs, tracking guidance references week 1 to week 2 decision.
- Monthly gym plan -> tracking guidance includes weekly review of completion, RPE, pain and sleep; alternatives no longer include `step-up`.

### Failures and fixes

- Manual probe exposed `step-up נמוך` in generated alternatives. Replaced generated alternatives with Hebrew-first wording and added a regression assertion.
- The one full-suite failure was a transient Windows socket resource error, not a code assertion; rerun passed.

### Next research target

- Loop 7 should inspect whether the plan builder asks or infers correctly for pain/injury and red-flag cases across single/weekly/two-week/monthly requests, including when to refuse progression and when to recommend professional help.

## Loop 7 - 2026-06-24

### Sources reviewed

- Mayo Clinic exercise warning symptoms: https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/exercise-and-chronic-disease/art-20046049
- Exercise is Medicine low-back pain guidance: https://exerciseismedicine.org/assets/page_documents/EIM%20Rx%20series_Exercising%20with%20Lower%20Back%20Pain.pdf
- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/

### Rules extracted

- Chest pain, dizziness, fainting, unusual shortness of breath, and similar warning symptoms should stop plan generation and route to a conservative safety response.
- Soft musculoskeletal pain can continue only as adapted wellness coaching, with the body area carried into limitations and no instruction to push through pain.
- Safety behavior must apply to both chat and direct API plan creation; otherwise the product has an unsafe bypass.

### Changes made

- Added safety classification at the direct `/api/workout-plans` boundary before generating/saving a plan.
- Direct API red flags now record a `SafetyEvent`, return HTTP 400 with the safety response, and save no workout plan.
- Direct API soft pain now records an advisory `pain_signal`, extracts the pain area, and passes it into `WorkoutPlanRequest.limitations` so the saved plan contains context such as `רגישות בברך`.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_blocks_red_flag_symptoms_before_saving_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan backend/tests/test_coach_engine.py::test_chat_endpoint_red_flag_blocks_plan_even_with_plan_request backend/tests/test_safety_service.py -q` -> 14 passed.
- `python -m pytest backend/tests -q` -> 431 passed.

### Manual Hebrew probes

- Direct API "יש לי כאב בחזה וסחרחורת, תבנה לי תוכנית כוח" -> HTTP 400, no saved plan, `dangerous_symptoms` event.
- Direct API "יש לי כאב ברך קל, תבנה לי תוכנית שבועית בלי ציוד" -> `weekly_plan`, saved `decision_inputs.limitations` is `רגישות בברך`, `pain_signal` event.
- Chat "יש לי כאב בחזה, תבנה לי תוכנית חודשית" -> safety override still wins.

### Failures and fixes

- First direct soft-pain implementation recorded the event but did not pass the knee area into plan limitations. Reused `extract_pain_area()` at the API boundary and strengthened the test.

### Next research target

- Loop 8 should inspect the actual generated exercise dosage by goal and level: whether beginner/intermediate/advanced plans differ enough in sets, reps, rest, RPE/RIR, and split complexity without overloading beginners.

## Loop 8 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- NSCA resistance training frequency guidance: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- Schoenfeld et al. loading recommendations review: https://www.mdpi.com/2075-4663/9/2/32
- Grgic et al. failure vs non-failure meta-analysis: https://www.sciencedirect.com/science/article/pii/S2095254621000077

### Rules extracted

- Beginner dosage should be lower and more conservative: stable exercises, fewer sets, RPE 5-7 and 2-4 RIR.
- Intermediate dosage can keep the current default of 2-3 sets and RPE 6-8 while progressing from logs.
- Advanced users can tolerate more sets and higher effort, but most work still does not need repeated failure.
- Strength, hypertrophy and endurance differ primarily through reps/rest/effort and recoverable weekly volume, not through random exercise variety.

### Changes made

- Added experience-aware set and effort variables inside `WorkoutPlanBuilder`.
- Beginner plans now generate 2 main sets, 2 upper/hinge sets, 1-2 accessory sets, and RPE 5-7 guidance.
- Intermediate plans keep the existing moderate dosage.
- Advanced plans now generate 4 main sets, 3 upper/hinge/core sets, 2-3 accessory sets, and RPE 7-9 guidance.
- Updated `goal_specific_plan_protocols.experience_level` with the dosage rules.
- Updated workout-log adaptation tests to assert reduced sets relative to the saved plan instead of the old hardcoded value.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_goal_specific_plan_protocols -q` -> 3 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 134 passed.
- First full-suite run exposed two old workout-log expectations that assumed reduced sets always become `2`.
- `python -m pytest backend/tests/test_workout_logs_api.py::test_next_workout_api_repeats_after_skipped_or_pain_log backend/tests/test_workout_logs_api.py::test_next_workout_execution_plan_reduces_after_high_rpe_log -q` -> 2 passed after fixing expectations.
- `python -m pytest backend/tests -q` -> 431 passed.

### Manual Hebrew probes

- "תבנה לי תוכנית למתחיל בלי ציוד לשבוע" -> beginner/full-body, first exercise `2` sets, tracking guidance includes RPE 5-7 and 2-4 RIR.
- "תבנה לי תוכנית בינוני לשבוע עם משקולות" -> intermediate/full-body, first exercise `3` sets, tracking guidance includes RPE 6-8 and 1-3 RIR.
- "תבנה לי תוכנית מתקדם עם משקל גוף לשבוע" -> advanced/full-body, first exercise `4` sets, harder bodyweight variant, tracking guidance includes RPE 7-9 without repeated failure.

### Failures and fixes

- Reducing beginner base sets from 3 to 2 made recovery/adherence execution plans reduce to 1 set. This is the intended minimum-version behavior, so tests now compare against the saved plan instead of a fixed old value.

### Next research target

- Loop 9 should inspect the generated monthly and two-week progression schedules against actual dosage: whether week 2/3 progression changes only one variable and whether beginner monthly plans stay conservative enough.

## Loop 9 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- NSCA resistance training frequency guidance: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- Schoenfeld et al. loading recommendations review: https://www.mdpi.com/2075-4663/9/2/32
- Grgic et al. failure vs non-failure meta-analysis: https://www.sciencedirect.com/science/article/pii/S2095254621000077

### Rules extracted

- Progression must change one variable at a time and must depend on logs, pain, RPE and recovery.
- Beginner monthly plans should not add sets in week 2; first progression should usually be clean reps or repeating the same work.
- Advanced plans can progress more aggressively, but still only one lever at a time and without repeated failure.

### Changes made

- Made `progression_schedule` generation experience-aware.
- Beginner two-week plans now use week 1 as movement learning and week 2 as rep-only progression or hold.
- Beginner monthly plans now start with 2 sets, forbid added sets in week 2, allow one set on one main exercise in week 3 only if recovery is good, and use week 4 as review/hold.
- Advanced two-week/monthly plans can add load or one accessory set only when logs are stable.
- Updated plan-horizon knowledge rules for beginner and advanced progression.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols -q` -> 3 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 135 passed.
- `python -m pytest backend/tests -q` -> 432 passed.

### Manual Hebrew probes

- "תבנה לי תוכנית חודשית למתחיל בלי ציוד" -> monthly beginner schedule says week 1 has 2 sets, week 2 adds clean reps only and does not add sets, week 3 allows one set to one main exercise only if recovery is good.
- "תבנה לי תוכנית חודשית למתקדם עם משקל גוף" -> monthly advanced schedule uses RPE 7-9, one small progression in week 2, and one accessory set or small load increase in week 3 if logs are stable.

### Failures and fixes

- Initial test exposed that beginner month wording did not explicitly say "לא להוסיף סטים" in week 2. Added that phrase to the generated schedule.

### Next research target

- Loop 10 should inspect generated Hebrew wording and field labels for remaining English/technical leakage in workout plans and knowledge summaries, then fix only user-visible leaks.

## Loop 10 - 2026-06-24

### Sources reviewed

- Existing workout-plan research rules from Loops 1-9.
- Local code inspection: `WorkoutPlanBuilder`, `CoachIntentService`, chat routing tests, workout-plan API tests, and frontend workout equipment labels.

### Rules extracted

- User-visible Hebrew plan guidance should not leak raw English exercise names when there is a natural Hebrew fitness term.
- Internal enum/storage values such as `bodyweight` can stay stable if the UI translates them; changing stored API values would be unnecessary churn.
- Hebrew chat routing must treat natural phrases like `תוכנית שבועית` and `אימון יחיד` as deterministic workout-plan requests, not provider-routed general chat.
- Manual probes must preserve UTF-8 Hebrew; PowerShell stdin can create false negatives if the text is not passed intact.

### Changes made

- Replaced visible raw English exercise guidance:
  - `תרגול hip hinge` -> `תרגול היפ הינג'`
  - `hip thrust לספסל` -> `דחיפת אגן על ספסל`
  - `pull-through בכבל` -> `משיכת כבל בין הרגליים`
  - `פייק פוש-אפ מוגבה` -> `שכיבת סמיכה פייק מוגבהת`
- Expanded the English-leak regression helper to scan exercise alternatives as visible plan output.
- Added forbidden raw terms to the guidance regression: `hip hinge`, `hip thrust`, `pull-through`, `step-up`, `push-up`, and `RDL`.
- Added chat regression coverage for natural Hebrew `תוכנית שבועית` without the word `אימון`.
- Fixed chat intent classification for Hebrew single-workout phrases: `אימון יחיד`, `אימון בודד`, `אימון חד פעמי`, and `אימון חד-פעמי`.
- Added a chat regression for `יש לי כאב ברך קל, תבנה לי אימון יחיד בבית`, verifying local routing, advisory pain handling, saved `single_workout`, and knee limitations.

### Tests and checks

- `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_weekly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_hebrew_single_workout_with_soft_pain backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_workout_plans_api.py::test_single_session_plan_is_saved_without_replacing_current_multi_week_plan -q` -> 4 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_context_builder.py backend/tests/test_workout_schema.py -q` -> 234 passed.
- `python -m pytest backend/tests -q` -> 434 passed.
- An earlier full-suite run failed once with Windows `WinError 10055` while TestClient tried to allocate a socket pair. The failed test passed in isolation and the full suite passed on rerun.

### Manual Hebrew probes

- Chat `תבנה לי תוכנית שבועית למתקדם בלי ציוד` -> `provider_status=local_tool`, saved `weekly_plan`.
- Chat `יש לי כאב ברך קל, תבנה לי אימון יחיד בבית` -> `provider_status=local_tool`, no hard safety block, saved `single_workout`.
- Direct API `תבנה לי תוכנית חודשית בחדר כושר לחיטוב` -> `monthly_plan`.
- Combined visible-output leak scan for `hip hinge`, `hip thrust`, `pull-through`, `step-up`, `push-up`, and `RDL` -> no leaks.

### Failures and fixes

- Initial manual chat probe through PowerShell stdin falsely showed Hebrew weekly chat falling through to the provider. A direct classifier check with intact UTF-8 text returned `workout_plan`, so no classifier change was made for that phrase; a regression test was added.
- The corrected probe exposed a real gap for `אימון יחיד`: the builder understood it, but chat intent detection did not. Added the phrase variants to `CoachIntentService`.
- Manual probe attempts also hit PowerShell quoting and temp SQLite path issues. The final probe used a workspace `tmp` SQLite file and passed.

### Next research target

- Loop 11 should inspect the actual day-by-day split design and exercise ordering for weekly, two-week, and monthly plans: whether full-body, upper/lower, and push/pull/legs are selected appropriately by days per week and experience level, and whether monthly plans avoid repeating the same day structure without reason.

## Loop 11 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- NSCA resistance training frequency guidance: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- HPRC exercise selection and resistance-training optimization: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training
- Schoenfeld et al. loading recommendations review: https://www.mdpi.com/2075-4663/9/2/32

### Rules extracted

- Beginners and users training 2-3 days per week usually fit best with full-body training because it keeps exposure frequent and simple.
- Intermediate users around 4 days per week can use upper/lower to increase volume while preserving recovery between similar muscle groups.
- Advanced users with 5-6 available days can use push/pull/legs-style splits, but only when recovery and adherence support it.
- Full-body does not need to mean identical days. A 3-day full-body plan can rotate emphasis/order while keeping the basic movement patterns.
- Compound or skill-heavy work should appear early in a session; accessories and core can follow.

### Changes made

- Updated `WorkoutPlanBuilder._day_specs()` so `full_body` plans rotate:
  - `full_body`
  - `full_body_lower`
  - `full_body_upper`
- Added exercise-order handling for the new full-body emphasis values:
  - lower-emphasis day starts squat/hinge before push/pull
  - upper-emphasis day starts push/pull before squat/hinge
  - balanced day keeps the existing squat/push/pull/hinge/core order
- Added Hebrew labels for the new day emphases:
  - `גוף מלא - דגש רגליים`
  - `גוף מלא - דגש פלג עליון`
- Updated `weekly_structure_protocols.beginner_full_body` in the knowledge center with the rotated full-body rule.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py::test_full_body_plan_rotates_day_emphasis_without_losing_balance backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_weekly_structure_protocols -q` -> 2 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 136 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_context_builder.py backend/tests/test_workout_schema.py -q` -> 235 passed.
- `python -m pytest backend/tests -q` -> 435 passed.

### Manual Hebrew probes

- Chat `תבנה לי תוכנית שבועית למתחיל בלי ציוד, 3 ימים` -> `provider_status=local_tool`, saved `weekly_plan`, split `full_body`, day focus order `full_body`, `full_body_lower`, `full_body_upper`.
- Direct API `תבנה לי תוכנית חודשית לבינוני בחדר כושר` with 4 days -> split `upper_lower`, focus order `upper_body`, `lower_body`, `upper_body`, `lower_body`.
- Direct API `תבנה לי תוכנית חודשית למתקדם עם משקל גוף` with 5 days -> split `push_pull_legs`, focus order `push`, `pull`, `legs`, `push`, `pull`.

### Failures and fixes

- No test failures in this loop.
- Product risk found and fixed: 3-day full-body plans previously repeated the same day focus and order, which made weekly/monthly plans feel more generic than necessary.

### Next research target

- Loop 12 should inspect exercise substitution quality by equipment and pain context: whether home/bodyweight/dumbbell/gym alternatives preserve the same movement pattern, avoid unsafe substitutions, and stay natural in Hebrew.

## Loop 12 - 2026-06-24

### Sources reviewed

- HPRC exercise order and exercise selection guidance: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training
- NSCA resistance training frequency guidance: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- Existing knowledge-center movement limitation rules, especially `knee_sensitive_lower_body`.

### Rules extracted

- Substitutions should preserve the movement pattern or training intent, not swap in a random hard exercise.
- Exercise order should keep more technical multi-joint work before assistance work, while fatigue is lower.
- Pain context should narrow the default exercise menu. For knee sensitivity, do not make single-leg lunge work a primary default exercise.
- Knee-sensitive plans can still train lower body through controlled squat range, hip hinge, and glute bridge patterns, with pain-free range and lower load.

### Changes made

- Passed raw `limitations` text into the exercise selection path while keeping user-visible limitation wording sanitized.
- Added `_adapt_selection_for_limitations()` and `_has_knee_limitation()`.
- Knee-sensitive lower-body selections now remove `lunge` as a primary exercise.
- Existing squat, hinge, glute bridge, and core work remain available so the lower-body day is adapted rather than deleted.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py::test_knee_sensitive_plan_avoids_primary_lunge_work backend/tests/test_workout_plans_api.py::test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_movement_limitation_adaptations -q` -> 3 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 137 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_context_builder.py backend/tests/test_workout_schema.py -q` -> 236 passed.
- `python -m pytest backend/tests -q` -> 436 passed.

### Manual Hebrew probes

- Chat `יש לי כאב ברך קל, תבנה לי תוכנית חודשית לבינוני בחדר כושר, 4 ימים` -> `provider_status=local_tool`, split `upper_lower`, lower-body days contain `squat`, `hip_hinge`, `glute_bridge`, `core_anti_extension`, and no `single_leg`.
- Direct API `תבנה לי תוכנית חודשית לבינוני בחדר כושר` with the same 4-day structure and no knee pain -> lower-body days still include `single_leg`.

### Failures and fixes

- No test failures in this loop.
- Product risk found and fixed: pain-adapted plans previously carried knee context in notes but could still keep primary lunge work on lower days.

### Next research target

- Loop 13 should inspect the generated alternatives/regressions/safety notes as a single coaching surface: each exercise should expose one clear easier option, one realistic substitution, and a safety note that matches the user’s equipment and limitation context.

## Loop 13 - 2026-06-24

### Sources reviewed

- HPRC exercise order and fatigue-risk guidance: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training
- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- Existing knowledge-center movement limitation rules, especially `knee_sensitive_lower_body`.

### Rules extracted

- Alternatives and regressions are part of the coaching plan, not decoration.
- For pain-sensitive contexts, alternatives should become narrower and safer, not just carry a generic warning.
- Knee-sensitive squat alternatives should bias toward controlled range and supported patterns, such as box squat, short-range leg press, and sit-to-stand.
- Step-up or split-squat style options can be reasonable for general plans, but should not be the default alternative when the user just reported knee pain.

### Changes made

- Added catalog-level limitation adaptation for knee-sensitive plans.
- Knee-sensitive squat exercises now get:
  - alternatives: `סקוואט לקופסה`, `לחיצת רגליים בטווח קצר`, `ישיבה-קימה מכיסא` for gym mode
  - an explicit safety note: `ברך רגישה: להקטין עומק ולשמור ברך במסלול כף הרגל.`
  - a regression that points to box squat, sit-to-stand, or short pain-free range
- Normal non-pain plans keep the broader alternatives such as low step-up where appropriate.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plans_api.py::test_knee_sensitive_plan_avoids_primary_lunge_work backend/tests/test_workout_plans_api.py::test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan -q` -> 2 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py -q` -> 26 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_context_builder.py backend/tests/test_workout_schema.py -q` -> 236 passed.
- `python -m pytest backend/tests -q` -> 436 passed.

### Manual Hebrew probes

- Knee-sensitive gym plan squat alternatives -> `סקוואט לקופסה`, `לחיצת רגליים בטווח קצר`, `ישיבה-קימה מכיסא`.
- Normal gym plan squat alternatives -> still includes broader non-pain option `עלייה נמוכה למדרגה`.

### Failures and fixes

- First manual probe command failed because Python function definitions cannot be placed after semicolons in a one-liner. Re-ran with direct comprehensions.
- No app test failures in this loop.

### Next research target

- Loop 14 should inspect how workout-plan output is surfaced in chat: whether the chat response gives one clear next action, enough plan summary to orient the user, and no fake “saved” wording when a plan is only a replacement candidate.

## Loop 14 - 2026-06-24

### Sources reviewed

- Existing product rule: coach responses should usually be short, grounded, and end with one clear next action.
- Local code inspection: `CoachEngine._workout_plan_saved_response()`, pending replacement flow, and chat routing tests.

### Rules extracted

- A saved active plan response should not only say “plan ready”; it should tell the user exactly where to start.
- A single workout should clearly remain one-off and should tell the user what to do and what to track.
- A replacement candidate should not imply it is active. It should ask for confirmation and name the exact reply options.

### Changes made

- Added `_first_workout_next_action()` to build a grounded next action from the first workout day and first exercise.
- Active saved plans now say which day to start from, name the first exercise, and ask the user to track `RPE/כאב`.
- Single-workout responses now say to start the one-off workout today and track `RPE/כאב`.
- Replacement-candidate responses now explicitly say the next replies: `כן להחליף` or `להשאיר קיימת`.

### Tests and checks

- `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_workout_plan_intent_to_module backend/tests/test_coach_engine.py::test_chat_new_multi_week_plan_with_current_creates_candidate_and_asks_for_replacement backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_session_workout_plan_without_replacing_current -q` -> 3 passed.
- `python -m pytest backend/tests/test_coach_engine.py -q` -> 73 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_context_builder.py backend/tests/test_workout_schema.py -q` -> 236 passed.
- `python -m pytest backend/tests -q` -> 436 passed.

### Manual Hebrew probes

- Chat `תבנה לי תוכנית שבועית למתחיל בלי ציוד` -> `provider_status=local_tool`, response includes `תרגיל ראשון` and `RPE/כאב`.
- Replacement-candidate chat after an existing current plan -> `provider_status=local_tool`, response includes `כן להחליף` and `להשאיר קיימת`.

### Failures and fixes

- No test failures in this loop.
- Product weakness fixed: responses had correct persistence behavior but did not always give a concrete first action.

### Next research target

- Loop 15 should inspect workout logging against generated plans: whether completed, partial, skipped, modified, RPE/RIR, pain flags, and exercise-level logs feed the next-workout recommendation clearly enough.

## Loop 15 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training update: https://acsm.org/resistance-training-guidelines-update-2026/
- Local implementation review: `backend/app/services/workout_service.py`, `backend/app/services/training_adaptation_service.py`, `backend/app/services/coaching_knowledge.py`, `backend/tests/test_workout_logs_api.py`.
- Existing safety and limitation rules in the knowledge center, especially pain, progression gates, and movement substitutions.

### Rules extracted

- Logged pain is not just a generic "reduce load" signal. If the body area is available, the next workout should preserve that area as structured adaptation context.
- Existing plans must still adapt safely after a pain log; the system cannot rely only on generating new pain-aware plans.
- For knee pain, lower-body substitutions should narrow toward supported, controlled-range options such as box squat, short-range leg press, or sit-to-stand.
- Pain adaptation should reduce sets/load and ask for tracking of RPE and pain response, without diagnosing injury.
- Provider context must stay compact; adding safety detail cannot push workout-plan context over the prompt budget.

### Changes made

- Added `pain_area` extraction to `TrainingAdaptationService` from workout log notes and exercise-level notes.
- Added knee/shoulder/back area detection for pain logs, with knee used by the next-workout execution plan.
- Updated `WorkoutService._build_execution_plan()` so pain-caution execution plans can narrow alternatives using the adaptation payload.
- Added knee-pain substitution filtering for next workouts:
  - removes step-up, split-squat, and lunge-style alternatives when the logged pain area is knee
  - keeps or falls back to `סקוואט לקופסה` and `ישיבה-קימה מכיסא`
- Updated the knowledge center with a `logged_pain_next_workout` protocol and a compact workout-log-only summary rule.
- Kept the new logged-pain summary out of `workout_plan` provider context after a prompt-budget regression.

### Tests and checks

- `python -m pytest backend/tests/test_workout_logs_api.py -q` -> 17 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> first run failed because `workout_plan` provider context grew from the added summary line and exceeded the `<8350` prompt-budget assertion.
- Fixed by adding the logged-pain compact summary only for `workout_log`, not `workout_plan`.
- `python -m pytest backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_program_adaptation_protocols backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_program_adaptation_summary_for_workouts_only -q` -> 2 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> 227 passed.
- `python -m pytest backend/tests -q` -> 437 passed.

### Manual Hebrew probes

- First Hebrew chat probe failed because PowerShell piped Hebrew into Python with the wrong output encoding; the app received corrupted text and correctly asked the user to rewrite clearly.
- Re-ran with PowerShell output encoding forced to UTF-8.
- Chat request: `תבנה לי תוכנית אימונים חודשית של 4 ימים בחדר כושר להיפרטרופיה, אני ברמה בינונית`.
- The chat created a `monthly_plan`.
- Logged: `כאב ברך בסקוואט, עצרתי אחרי סט ראשון` against a lower-body exercise.
- `/api/workouts/next` returned:
  - `load_signal=pain_caution`
  - `pain_area=knee`
  - reduced sets to `1`
  - alternatives narrowed to `סקוואט לקופסה`, `ישיבה-קימה מכיסא`
  - execution note: choose an easier variation or stop if pain returns.

### Failures and fixes

- Encoding failure in the manual Hebrew probe was a test harness issue, not app logic. Fixed by forcing UTF-8 output encoding before piping the script to Python.
- Initial combined test run failed on provider-context budget for `workout_plan`. Fixed by keeping the new logged-pain compact rule scoped to `workout_log`.
- No remaining test failures after the fix.

### Next research target

- Loop 16 should inspect natural Hebrew workout-plan intent coverage again. The first manual attempt with `תוכנית חודשית` but without explicit `אימון/אימונים` did not create an active workout plan, so the next loop should decide whether monthly-plan Hebrew routing is still too brittle or whether the clarification behavior is acceptable.

## Loop 16 - 2026-06-24

### Sources reviewed

- Local routing code: `backend/app/services/coach_intent_service.py`.
- Local orchestration code: `backend/app/services/coach_engine.py`.
- Existing full-path chat tests in `backend/tests/test_coach_engine.py`.
- Existing plan horizon inference in `backend/app/services/workout_plan_builder.py`.

### Rules extracted

- Hebrew horizon phrases such as `תוכנית שבועית`, `תוכנית לשבועיים`, and `תוכנית חודשית` should route to workout-plan generation even when the user does not explicitly write `אימון` or `אימונים`.
- Do not broaden intent routing if the real classifier already handles the phrase; add a regression test instead.
- Manual Hebrew probes through PowerShell must force UTF-8 output encoding before piping scripts into Python, otherwise the app may receive corrupted Hebrew and the probe is invalid.

### Changes made

- Added a full `/api/chat` regression test for: `תבנה לי תוכנית חודשית של 4 ימים בחדר כושר להיפרטרופיה, אני ברמה בינונית`.
- Verified that the existing classifier already routes this phrase to `workout_plan`.
- No classifier code change was needed.

### Tests and checks

- `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word -q` -> 1 passed.
- `python -m pytest backend/tests/test_coach_engine.py -q` -> 74 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> 228 passed.
- `python -m pytest backend/tests -q` -> 438 passed.

### Manual Hebrew probes

- Chat request with UTF-8 shell encoding: `תבנה לי תוכנית חודשית של 4 ימים בחדר כושר להיפרטרופיה, אני ברמה בינונית`.
- Result:
  - `provider_status=local_tool`
  - response included saved-plan wording
  - active plan created
  - `plan_type=monthly_plan`
  - `days_per_week=4`
  - `goal=build_muscle`
  - `experience_level=intermediate`
  - first day: `יום 1 פלג גוף עליון`

### Failures and fixes

- The suspected routing issue was not a product bug. It came from a previous manual probe that corrupted Hebrew through the PowerShell-to-Python pipe.
- The missing product guard was test coverage, not classifier logic.

### Next research target

- Loop 17 should inspect whether the system asks for missing critical info correctly. The bot should infer safely for non-critical gaps, but it should not generate risky plans when the prompt lacks a critical constraint such as pain/limitations after a safety signal, usable equipment, or available time.

## Loop 17 - 2026-06-24

### Sources reviewed

- Local safety parser: `backend/app/services/pain_text.py`.
- Local safety classification: `backend/app/services/safety_service.py`.
- Local chat orchestration: `backend/app/services/coach_engine.py`.
- Local workout plan API: `backend/app/api/workouts.py`.
- Local workout-plan knowledge center: `backend/app/services/coaching_knowledge.py`.
- Existing regression tests for coach routing, workout plans, and provider-context prompt budgets.

### Rules extracted

- Missing non-critical fields such as exact session duration, precise equipment list, or plan horizon can be handled with conservative assumptions and those assumptions should be stated.
- A vague pain signal is critical safety information. If the user asks for a plan and says only that they have pain, the bot must ask one safety clarification before creating a plan.
- The clarification should ask where the pain is and whether it is sharp, worsening, or movement-limiting.
- The bot should not save a workout plan until vague pain is clarified.
- Specific mild pain, such as mild knee pain, can still generate a conservative plan with limitations and safety notes, as long as red-flag symptoms are absent.
- Compact provider-context summaries must stay inside the existing prompt-budget guard; new safety rules need to replace or compress text, not just add bloat.

### Changes made

- Added `vague_pain_plan_clarification_response()` to centralize the Hebrew safety clarification text.
- Updated chat workout-plan handling so vague pain + plan request returns one Hebrew safety question and saves no plan.
- Updated `/api/workout-plans` so vague soft-pain requests return `400` instead of creating an unsafe plan.
- Preserved the existing behavior where specific soft pain is converted into a plan limitation and a conservative adapted plan.
- Added the vague-pain critical-info rule to the workout-plan knowledge center.
- Added compact provider-context wording for the rule without exceeding the workout-plan prompt budget.

### Tests and checks

- `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving backend/tests/test_workout_plans_api.py::test_workout_plan_api_requires_pain_area_for_vague_soft_pain backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_full_coach_summaries_for_workout_plan backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols -q` -> 4 passed.
- `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 213 passed.
- First wide workout/chat/knowledge run failed once with Windows `WinError 10055` while Starlette was creating a test event loop. The focused failing test passed immediately afterward, and the same wide suite then passed. This was treated as a transient local socket-resource failure, not a product regression.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> 230 passed.
- `python -m pytest backend/tests -q` -> 440 passed.

### Manual Hebrew probes

- Invalid first probe: PowerShell mangled Hebrew input into question marks before Python received it, so the app correctly asked for a clearer Hebrew message. Re-ran with Unicode escape strings.
- Chat request: "I have pain, build me a strength plan" in Hebrew.
  - `status_code=200`
  - `provider_status=local_tool`
  - response asked where the pain is and whether it is sharp, worsening, or movement-limiting
  - no workout plan was saved
  - `SafetyEvent.event_type=pain_signal`
- Chat request: "I have mild knee pain, build me a 2-day strength plan without equipment" in Hebrew.
  - `status_code=200`
  - `provider_status=local_tool`
  - response acknowledged knee pain and gave conservative safety guidance
  - saved plan created with `plan_type=monthly_plan`, `days_per_week=2`, `duration_weeks=4`, `goal=improve_strength`
  - `SafetyEvent.event_type=pain_signal`

### Failures and fixes

- Initial focused run failed with an indentation error in `coaching_knowledge.py`; fixed the indentation before changing behavior further.
- Related tests initially failed because the added compact knowledge line pushed `workout_plan` provider context over the `<8350` guard. Fixed by shortening the summary to keep the new safety rule without prompt bloat.
- Manual probe initially failed because the test harness used a nonexistent direct `WorkoutPlan.plan_type` column; corrected the probe to read `plan_json["plan_type"]`.

### Next research target

- Loop 18 should return to external programming evidence and inspect whether two-week and monthly progression rules are sufficiently different. The current builder distinguishes horizons, but it may still be too generic around week-to-week loading, deload behavior, and beginner vs. intermediate progression.

## Loop 18 - 2026-06-24

### Sources reviewed

- ACSM position stand metadata: "Progression models in resistance training for healthy adults", Med Sci Sports Exerc, 2009, PMID 19204579, DOI 10.1249/MSS.0b013e3181915670.
- Schoenfeld et al. weekly volume meta-analysis metadata: "Dose-response relationship between weekly resistance training volume and increases in muscle mass", J Sports Sci, 2017, PMID 27433992, DOI 10.1080/02640414.2016.1210197.
- Loading review abstract: "Muscle hypertrophy and strength gains after resistance training with different volume-matched loads", Appl Physiol Nutr Metab, 2022, PMID 35015560, DOI 10.1139/apnm-2021-0515.
- Training-to-failure review abstract: "Effects of resistance training performed to repetition failure or non-failure on muscular strength and hypertrophy", J Sport Health Sci, 2022, PMID 33497853, DOI 10.1016/j.jshs.2021.01.007.
- Repetition-continuum review metadata: "Loading Recommendations for Muscle Strength, Hypertrophy, and Local Endurance", Sports (Basel), 2021, PMID 33671664, DOI 10.3390/sports9020032.
- NSCA journal metadata: Rhea/Peterson dose-response JSCR papers, PMIDs 16287373 and 15142003. PubMed did not expose abstracts for these records, so they were used only as source metadata.

### Rules extracted

- Progression should be conditional, not automatic. The decision gate is completion, technique, RPE/RIR, pain, and performance trend.
- Two-week plans should use Week 1 as calibration and Week 2 as either a small progression or a hold/reduction based on logs.
- Monthly plans should use a simple 4-week pattern: calibration, small progression, hold/small progression, then check/maintenance/reduction before the next block.
- Beginners should progress conservatively: add clean reps before sets or load, and avoid extra sets until the movement and logs are stable.
- Intermediate and advanced users can progress load or add a small accessory set, but not if RPE rises, performance drops, pain accumulates, or workouts are missed.
- The bot should say what to do when conditions are not met: hold the load, reduce volume, or use maintenance. Without this, plans sound falsely linear.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py` progression schedules:
  - two-week beginner Week 2 now explicitly says not to progress if Week 1 was not stable.
  - two-week intermediate/advanced plans now include hold or volume-reduction fallbacks.
  - monthly beginner Week 4 now includes a 20-30% volume reduction fallback when pain, missed workouts, or high RPE show up.
  - monthly intermediate/advanced Week 4 now includes a 20-40% volume-reduction fallback before another block.
- Updated `backend/app/services/coaching_knowledge.py` with `progression_fallback_policy` under `plan_horizon_protocols`.
- Added tests for conditional fallback language in generated schedules and knowledge center protocols.

### Tests and checks

- Focused first run failed because the new test expected `20-40%` for a beginner monthly plan created from the default onboarding profile. Fixed the assertion to require a percentage-based volume fallback, while separate advanced tests still check `20-40%`.
- `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols -q` -> 3 passed.
- First broad run hit Windows `WinError 10055` during `TestClient` event-loop socket creation. The named test passed in isolation; after a short pause the same broad suite passed. This is the repeated local socket-resource issue, not a plan behavior regression.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> 213 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> 230 passed.
- `python -m pytest backend/tests -q` -> 440 passed.

### Manual Hebrew probes

- Chat request: "Build me a two-week beginner plan without equipment, 3 days" in Hebrew.
  - `provider_status=local_tool`
  - saved `plan_type=two_week_plan`, `duration_weeks=2`, `days_per_week=3`, `experience_level=beginner`
  - progression schedule includes Week 2 fallback: if Week 1 is not stable, do not progress and do not add sets yet.
- Chat request: "Build me a monthly gym plan at intermediate level, 4 days" in Hebrew.
  - `provider_status=local_tool`
  - saved `plan_type=monthly_plan`, `duration_weeks=4`, `days_per_week=4`, `experience_level=intermediate`
  - Week 4 progression schedule includes 20-40% volume reduction if fatigue, pain, or missed sessions increase.

### Failures and fixes

- PubMed search through the browser was noisy, so NCBI E-utilities was used directly with network approval.
- JSCR/NSCA records did not expose abstracts through PubMed; source metadata was recorded, but implementation rules were grounded mostly in ACSM progression metadata and open abstracts from loading/failure/volume reviews.
- Repeated `WinError 10055` broad-suite failures occurred at Windows socket creation inside Starlette/AnyIO, not inside app assertions. Retried after isolation and a short pause; full backend passed.

### Next research target

- Loop 19 should inspect whether plan output gives enough goal-specific progression differences. Hypertrophy, strength, fat-loss support, endurance, and mobility currently share many schedule mechanics; the next loop should verify whether reps/rest/RPE/progression are distinct enough without making the builder overcomplicated.

## Loop 19 - 2026-06-24

### Sources reviewed

- CDC Adult Activity overview: adults need weekly aerobic activity plus at least 2 days of muscle-strengthening activity; page also emphasizes that activity can be spread through the week.
- CDC Measuring Physical Activity Intensity: relative intensity can use 0-10 effort, moderate is about 5-6, vigorous begins around 7-8, and the talk test is a practical field cue.
- PubMed primary-source check for rest periods: Grgic et al., "Effects of Rest Interval Duration in Resistance Training on Measures of Muscular Strength: A Systematic Review", Sports Med, 2018, PMID 28933024, DOI 10.1007/s40279-017-0788-x.
- Stronger by Science, Greg Nuckols, "The Complete Strength Training Guide": practical coaching source for beginner buy-in, movement proficiency, staying away from failure early, and different priorities for beginner/intermediate/advanced lifters.
- RP Strength, "Training Volume Landmarks for Muscle Growth": practical coaching source for MV/MEV/MAV/MRV, working set assumptions, and volume decisions based on performance/soreness.
- Barbell Medicine, "The Beginner Prescription": practical coaching source for RPE as a learnable autoregulation skill, beginner movement-pattern selection, and conditioning support.
- `yourself` skill diagnostics and planned run:
  - available: Reddit, Hacker News, Polymarket, GitHub, grounding.
  - unavailable/not configured: X/Twitter auth, YouTube/yt-dlp, TikTok/Instagram ScrapeCreators.
  - a planned Reddit/grounding pass was run, but top results were mostly off-target bodyweight challenges and bodybuilding contest posts, so raw dumps were not kept as programming evidence.
- Israeli/Facebook/Instagram broadening:
  - Hebrew web searches and Facebook/Instagram targeted searches were attempted.
  - Facebook/Instagram were not usable as reliable content sources in this environment.
  - IsraelBody opened but the accessible page was primarily commerce/course navigation, not specific programming evidence for sets/reps/rest/RPE.

### Rules extracted

- Goal-specific plans should differ in actual variables, not only labels.
- Strength: prioritize central exercises early, lower rep ranges, longer rest, and load-first progression only after clean sets without pain.
- Hypertrophy: use moderate or broad rep ranges, keep most sets near but not necessarily to failure, and add volume only when recovery/performance support it.
- Fat-loss support: keep strength and technique, add steps/light cardio gradually, and do not turn training into punishment or excessive fatigue.
- Endurance/general conditioning: use talk test or RPE 5-7, shorter rests where appropriate, and progress duration/frequency before intensity.
- Mobility: use fewer sets, slower controlled reps, lower RPE, range/control/breathing before load.
- Beginner overlays must not erase mobility-specific effort language; prompt-specific mobility constraints should win after experience-level volume adjustments.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - strength main rest changed from `120 שניות` to `120-180 שניות`.
  - fat-loss support main rest changed to `60-90 שניות`.
  - endurance main/upper rest changed to `45-60 שניות`.
  - mobility plans now use lower sets, `RPE 4-6`, and effort notes focused on range, control, and breathing.
  - variable composition order changed so experience-level volume applies first, and prompt-specific mobility constraints override effort/rest/reps last.
- Updated `backend/app/services/coaching_knowledge.py`:
  - first added a separate `rest_and_effort_policy`, then removed it after Ponytail Review.
  - folded rest/effort guidance directly into existing goal-specific protocols for strength, hypertrophy, fat-loss support, endurance, and mobility.
- Updated tests:
  - expanded goal-variable assertions for strength, fat-loss support, endurance, and mobility.
  - updated knowledge-center assertions to check goal-specific rules directly after the Ponytail simplification.

### Tests and checks

- Initial focused test failed because mobility effort notes were overwritten by beginner experience defaults. Root cause: `_prompt_training_variables()` ran before `_experience_training_variables()`. Fixed by reversing the order.
- `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_goal_specific_plan_protocols -q` -> 3 passed before Ponytail simplification.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` -> 138 passed.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py -q` -> 230 passed.
- `python -m pytest backend/tests -q` -> 440 passed.
- After Ponytail simplification:
  - focused tests -> 2 passed.
  - workout plans + knowledge -> 138 passed.
  - workout/log/chat/knowledge -> 230 passed.
  - full backend -> 440 passed.

### Manual Hebrew probes

- Strength monthly Hebrew chat:
  - saved `goal=improve_strength`, `plan_type=monthly_plan`
  - first exercise reps `4-6 חזרות`
  - first exercise rest `120-180 שניות`
- Endurance two-week Hebrew chat:
  - saved `goal=improve_endurance`, `plan_type=two_week_plan`
  - first exercise reps `10-15 חזרות`
  - first exercise rest `45-60 שניות`
- Mobility single-workout Hebrew chat:
  - saved `plan_type=single_workout`
  - first exercise reps `8-12 חזרות איטיות`
  - tracking guidance includes `RPE 4-6` and range/control/breathing priority.

### Ponytail Review

- Finding: `coaching_knowledge.py:L1112: shrink: separate rest_and_effort_policy duplicates goal-specific protocols. Fold the rules into each existing goal protocol and delete the extra key/test assertions.`
- Applied the finding immediately.
- Net effect: removed an extra protocol layer while preserving the same knowledge in the places the bot already uses for goal-specific planning.

### Failures and fixes

- The `yourself` engine first ran with deterministic fallback and returned irrelevant Reddit results. Reran with an explicit query plan.
- The planned run initially failed because PowerShell wrote the plan JSON with a UTF-8 BOM. Fixed by writing the JSON with `System.Text.UTF8Encoding(false)`.
- Even with the valid plan, the social/community result set was weak and off-topic; it was logged as a limitation, not used as evidence.
- Israeli/Facebook/Instagram sources were attempted but did not provide usable public programming evidence in this environment.

### Next research target

- Loop 20 should deliberately target Hebrew/Israeli coach sources and public social/video material before code changes. The current environment cannot use X/Twitter, TikTok, Instagram, or YouTube transcripts without extra setup, so the next loop should first find accessible Israeli Hebrew web/video sources or explicitly document that the source class is blocked before changing code.

## Loop 20 - 2026-06-24

### Sources reviewed

- DuckDuckGo HTML search was used because the built-in Hebrew search returned unrelated or empty results for Hebrew programming phrases.
- FitnessIsrael, "סטים וחזרות באימון": Israeli coach-side article by Rubin Yafim. Useful for Hebrew programming language, exercise variables, effort near but not always to failure, rest differences by goal, and not treating one program as universally best.
- FitStreet, "איך לבנות תכנית אימונים כמו מקצוענים": Hebrew coach/business source. Useful for practical plan construction: compounds first, isolation only as needed, 15-30 total sets per session as a broad heuristic, 3-5 sets for main lifts, 2-3 for isolation, use rep ranges rather than exact reps, and treat plans as adjustable guidelines.
- Fitnessophy, "תוכניות אימונים למתחילים ומתקדמים": Hebrew coach source. Useful for FBW/AB framing: FBW is common as a first plan for beginners, 2-4 weekly sessions, rest between sessions, AB usually as a continuation after FBW.
- Stronger, "תוכנית אימון בחדר כושר": Hebrew coach source. Useful for Israeli natural phrasing and split hierarchy: FBW for beginners and advanced users at 2-3 weekly sessions; AB/ABC are not necessary before a base is built; bodyweight can be useful when equipment is limited.
- Wingate, "אימוני כוח ותוחלת חיים ארוכה ובריאה": Israeli institutional source. Useful for health-oriented resistance training: combine aerobic activity with at least 2 weekly strength sessions, resistance work supports lean mass and function, and strength work matters for fat-loss/body-composition support.
- Wingate, "עייפות השריר ויעילות האימון": Israeli institutional source. Useful for safety and effort: general users do not need repeated training to failure; leave reserve, avoid pain/failure as the default, and use fatigue as a cue for intensity rather than a goal.
- Public Facebook/Instagram/YouTube/TikTok searches were attempted with exact and broader Hebrew terms. No usable indexed programming evidence was available in this environment, so these were not used as source-backed rules.

### Rules extracted

- For beginners, do not rush from "more available days" to AB/ABC. Four available days can still use full-body or full-body emphasis days until logs, technique, and recovery are stable.
- Hebrew output should preserve familiar terms such as full-body, AB, סטים, חזרות, רזרבה, RPE/RIR, and avoid sounding like a translated textbook.
- Plan sources should include some Hebrew/Israeli source references, but without expanding provider context beyond the existing prompt-budget guardrails.
- The knowledge center should store this as a weekly-structure rule/source, not as a new routing layer or schema.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py` source references with Hebrew/Israeli programming sources:
  - Wingate strength and longevity.
  - Wingate muscle fatigue and training efficiency.
  - FitStreet Hebrew workout-plan building.
  - Fitnessophy Hebrew FBW/AB plans.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Compact provider weekly-structure summary now says beginners can use 4 days without early AB.
  - `beginner_full_body` now names AB/ABC in its avoid rule.
  - Added Hebrew/Israeli source refs to the beginner full-body protocol and top-level source registry.
- Updated tests:
  - Generated workout plans now assert Wingate appears in plan source refs.
  - Knowledge provider context now asserts the beginner AB guardrail and Hebrew/Israeli source registry entries.

### Tests and checks

- Focused tests: `2 passed`.
- `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py -q` initially failed because the added provider summary line exceeded the existing prompt-budget guardrail (`8418 < 8350` failed). Fixed by compressing the new rule into one short line instead of raising the budget.
- Same suite after compression: `139 passed`.
- Wider chat/log/workout/knowledge suite: `231 passed`.
- Full backend suite: `441 passed`.

### Manual Hebrew probes

- Chat request: "אני מתחיל, יש לי 4 ימים בשבוע, תבנה לי תוכנית חודשית בבית לכוח"
  - `provider_status=local_tool`
  - saved `plan_type=monthly_plan`, `training_split=full_body`, `days_per_week=4`, `experience_level=beginner`
  - response stayed Hebrew and practical, with assumptions and next action.
  - saved plan source refs include Wingate and Fitnessophy.
- Chat request: "מה עדיף למתחיל: full-body או AB? תענה כמאמן ישראלי."
  - response stayed concise, said there is no magic split, and favored full-body for low weekly frequency.
  - did not create a new plan.

### Ponytail Review

- Lean already. Ship.
- Reason: Loop 20 added source metadata and one compact provider rule inside existing knowledge-center structures. No new service, schema, route, or plan type was added.

### Failures and fixes

- Direct social-platform searches returned no usable public source text. Logged as a source limitation instead of using snippets as evidence.
- Initial manual probe failed because it imported `backend.app.database`; fixed by using the repo's actual `backend.app.db`.
- Provider prompt budget failed after adding a new summary line; fixed by compressing the weekly-structure rule rather than increasing the limit.

### Next research target

- Loop 21 should research concrete session templates and exercise ordering from coach references and primary sources, then check whether single-workout outputs should vary more clearly between short/time-limited sessions, beginner first sessions, and gym/home equipment without adding extra plan types.

## Loop 21 - 2026-06-24

### Sources reviewed

- HPRC/NSCA, "Choosing the right exercises to optimize your resistance training": exercise order affects results and safety; place power/multi-joint work before assistance/single-joint work; fatigue degrades form; push/pull or upper/lower alternation can manage fatigue.
- HPRC/NSCA: full-body sessions should cover major movement patterns, while muscle-group splits fit bodybuilding-specific goals better; 4-6 exercises can still balance push and pull.
- NASM, "Resistance Training: The Ultimate Guide": acute variables are sets, reps, rest, intensity, tempo, and frequency; beginner sessions should build a stable base; beginners usually start around 2-3 weekly full-body sessions.
- NASM phase examples: a full-body session starts with warmup and moves through lower, push, pull, hinge, and core categories rather than filling time with low-priority accessories first.
- FitStreet Hebrew workout-plan article: choose movement patterns first, use isolation only if needed, shorten sessions by removing lower-value extras, and treat the plan as adjustable rather than fixed.
- Wingate muscle-fatigue article: general users do not need failure as a default; stop when fatigue becomes pain or form breakdown; keep reps in reserve for safety and consistency.
- Hebrew web/social searches for time-limited session ordering were attempted, but did not add stronger public source text beyond the Israeli sources already reviewed.

### Rules extracted

- A single workout is not a mini monthly plan. It should answer: what should I do today, in this time window, with this equipment?
- For a 30-minute one-off workout, the first four slots should cover squat, push, pull, and hinge before core or isolation.
- For 20-minute one-off workouts, keep the existing hard cap: squat, push, pull is enough. Do not squeeze in extra work that makes logging or execution worse.
- The bot should not create a new builder layer for this. The existing `single_session` focus branch and time-based exercise cap are enough.
- Hebrew chat responses for a single workout should avoid awkward plan-day wording such as "לבצע היום את היום אימון יחיד"; the next action should name the first exercise and logging cue directly.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - `single_session` exercise order now selects squat, horizontal push, horizontal pull, hip hinge, then core.
  - Existing time caps still decide how much is shown, so short sessions stay short.
- Updated `backend/app/services/coach_engine.py`:
  - Single-workout saved responses now say to start with the first exercise, complete the workout in order, and log RPE/pain at the end.
- Updated tests:
  - Single-workout gym/duration inference now asserts the first four movement patterns include hip hinge before core.
  - Single-workout chat response now asserts the awkward Hebrew phrase is not emitted.

### Tests and checks

- Focused single-workout tests: `3 passed`.
- Broader workout/chat/knowledge suite: `214 passed`.
- Full backend suite after the movement-order change: `441 passed`.
- Focused formatter tests after the Hebrew wording fix: `2 passed`.
- Broader workout/chat/knowledge suite after the wording fix: `214 passed`.
- Full backend suite after the wording fix: `441 passed`.

### Manual Hebrew probe

- Chat request: "תן לי אימון אחד להיום בחדר כושר, 30 דקות"
  - `provider_status=local_tool`
  - saved `plan_type=single_workout`, `duration=30`, `split=single_session`
  - generated movement order: `squat`, `horizontal_push`, `horizontal_pull`, `hip_hinge`
  - response says: "הפעולה הבאה: להתחיל בלחיצת רגליים במכונה, לבצע את שאר האימון לפי הסדר, ולתעד RPE/כאב בסוף."
  - the previous awkward phrase "לבצע היום את היום" is gone.

### Ponytail Review

- Lean already. Ship.
- Reason: the loop changed one selection-order list and one formatter branch inside existing code. No new abstraction, schema, route, or prompt protocol was added.

### Failures and fixes

- Manual probing exposed a separate Hebrew phrasing bug in the saved single-workout response. Fixed it in the existing formatter and added a regression assertion.

### Next research target

- Loop 22 should research weekly ordering and recovery spacing: how to arrange full-body, upper/lower, and 4-day beginner weeks so the bot does not stack similar stress too tightly, especially for Hebrew requests like "4 ימים בשבוע" or "ראשון עד רביעי".

## Loop 22 - 2026-06-24

### Sources reviewed

- HPRC/NSCA, "Choosing the right exercises to optimize your resistance training": exercise order matters for safety; alternate push/pull can let worked muscles recover; full-body, upper/lower, and muscle-group splits are different organization choices; 4-6 exercise sessions should balance push and pull.
- NASM, "Resistance Training Exercises & Concepts You Should Use": beginners generally train 2-3 times weekly; intermediate users can use 3 full-body days or 4-day split routines; advanced lifters need appropriate splits to avoid overtraining; full-body sample sessions cover major categories and start from a warmup.
- ODPHP Physical Activity Guidelines "Top 10 Things to Know": adults need 150-300 minutes moderate aerobic activity weekly and muscle-strengthening work at least 2 days weekly.
- Schoenfeld, Grgic, and Krieger 2019 frequency meta-analysis: when weekly volume is equated, hypertrophy differences between higher and lower frequency are not meaningful; frequency can be chosen around schedule and preference.
- Existing Israeli/Hebrew sources from Loops 20-21 remain relevant: Fitnessophy and Stronger favor full-body as a practical beginner base before rushing to AB/ABC; FitStreet treats plans as adjustable guidelines.
- Hebrew DuckDuckGo and Bing searches for 4-day split/recovery/coach pages were attempted. DuckDuckGo returned the shell page instead of usable results; Bing returned irrelevant results. No weak snippets were used as evidence.

### Rules extracted

- Weekly spacing is a recovery and adherence rule, not a separate calendar scheduler.
- For beginners with 4 available days, full-body can still be valid, but the plan must warn against stacking hard similar stress without recovery.
- If the user explicitly asks for consecutive days, the bot should keep the plan practical and add a fallback: reduce volume or use a minimum version on the later days instead of pretending the schedule is ideal.
- Upper/lower should not stack two hard lower-body days back to back; PPL should usually add a light/rest day after 3 consecutive stress days.
- Frequency should serve weekly volume and consistency. More days are not automatically better when volume is matched and recovery is worse.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - Added `_weekly_spacing_guidance()` and `_has_consecutive_day_pressure()`.
  - Saved `weekly_spacing_guidance` in `decision_inputs`.
  - Added spacing guidance into `tracking_guidance` for persistent plans.
  - Handles full-body, upper/lower, PPL, 4-day beginner full-body, and consecutive-day wording such as "ברצף" and "ראשון עד רביעי".
- Updated `backend/app/services/coach_engine.py`:
  - Added `_plan_weekly_spacing_text()`.
  - Hebrew saved-plan responses for 4+ day plans now surface one concise spacing warning immediately, instead of hiding it only inside plan details.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added HPRC/NSCA, NASM frequency, and Schoenfeld frequency meta-analysis source refs to weekly structure entries.
- Updated tests:
  - API regression for a Hebrew 4-day beginner full-body plan requested from Sunday through Wednesday in a row.
  - Chat regression proving the initial Hebrew response mentions weekly spacing and the saved plan contains dense-day/minimum-version guidance.

### Tests and checks

- Focused Loop 22 tests: `2 passed`.
- Plan type builder tests: `5 passed`.
- Workout plan + builder + knowledge suite: `145 passed`.
- Coach engine suite: `76 passed`.
- Manual Hebrew chat probe through the test app:
  - request: "תבנה לי תוכנית חודשית למתחיל בלי ציוד, 4 ימים בשבוע, ראשון עד רביעי ברצף"
  - `status_code=200`, `provider_status=local_tool`
  - saved `plan_type=monthly_plan`, `training_split=full_body`, `days_per_week=4`
  - response contains spacing warning
  - saved plan contains dense-day guidance and minimum-version tracking guidance
- Full backend suite: `443 passed`.

### Ponytail Review

- Lean already. Ship.
- Reason: this loop did not build a scheduler. It added one small plan-guidance helper, one response formatter helper, and direct tests. No schema, route, or new planning service was introduced.
- Tradeoff: exact weekday scheduling is still not implemented because the request schema does not collect explicit preferred days. That should wait until product requirements justify real calendar semantics.

### Failures and fixes

- The first API assertion compared raw `decision_inputs` text to neutralized user-facing tracking text. Fixed the test to assert stable behavior instead of exact string identity.
- The first manual probe exited with a Windows locked SQLite temp-file cleanup error after already proving behavior. Reran with explicit client/DB cleanup and got a clean exit.
- Broad Hebrew search channels were not reliable in this environment; source limitations were logged rather than using weak results.

### Next research target

- Loop 23 should research plan updates after missed/skipped workouts: when to repeat the missed workout, when to move on, when to reduce volume, and how a Hebrew-first coach should respond without guilt or fake "catch-up" volume.

## Loop 23 - 2026-06-24

### Sources reviewed

- CDC, "Overcoming Barriers to Physical Activity": missed activity is often driven by time, energy, motivation, fear of injury, or practical constraints; the response should schedule a realistic activity window, choose an activity that fits available time, and build gradually rather than using all-or-nothing framing.
- NSCA, "Overtraining Syndrome and Recovery": excessive intensity, duration, or frequency beyond adaptation capacity, especially with insufficient recovery, can reduce performance and increase injury risk; recovery between training days is individualized and important.
- GQ with John Raglin PhD and coach Ashley Mateo on missed workouts: do not make up missed sessions by cramming the missed volume; first understand whether the blocker was schedule, fatigue, or recovery, then resume with a manageable next session.
- Existing app inspection: `TrainingAdaptationService` already treats skipped/partial sessions as adherence risk, `WorkoutService.next_workout()` can repeat the skipped day or return a reduced execution plan, and the dashboard already surfaces a minimum-version cue after a skipped workout.
- Hebrew web search for missed-workout coaching returned irrelevant AI/ML results in this environment, so no weak Hebrew snippets were used as evidence.

### Rules extracted

- Missing one workout should not reset the plan.
- The bot should explicitly reject "catch-up" volume after a miss.
- If the miss was because of schedule/time, resume with the next workout or the missed workout in a short version.
- If the miss was because of fatigue, bad sleep, pain, or unusually poor recovery, use a minimum version, fewer sets, and no load increase.
- The next action should be one concrete nearby window plus a logging cue: record what blocked the session so future plans can adapt.
- This guidance belongs in the existing missed-workout response and adaptation knowledge; no new missed-workout service is justified yet.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - `_missed_workout_guidance_response()` now distinguishes time blockers from fatigue/pain/sleep blockers.
  - The response now says not to return all missed volume at once.
  - The next action asks the user to choose one nearby window, finish a short version, and log the blocker.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added source references for missed-session adaptation: CDC barriers, NSCA overtraining/recovery, and the GQ missed-workout coaching article.
- Updated tests:
  - Chat regression now asserts the Hebrew missed-workout response mentions time, fatigue, and no catch-up volume.
  - Knowledge regression now asserts missed-session rules cite NSCA overtraining/recovery.

### Tests and checks

- Focused missed-workout chat test: `1 passed`.
- Focused knowledge test: `1 passed`.
- Training adaptation service suite: `6 passed`.
- Broader coach/knowledge suite: `188 passed`.
- Training adaptation + workout logs + dashboard suites: `30 passed`.
- Full backend suite: `443 passed`.

### Manual Hebrew probe

- Chat request: `פספסתי שני אימונים השבוע כי הייתי עייף. איך לחזור?`
  - `status_code=200`
  - `provider_status=local_tool`
  - response rejected catch-up volume, used the fatigue path, recommended a minimum version, and gave one concrete next action.

### Ponytail Review

- Lean already. Ship.
- Reason: the loop reused the existing intent, adaptation, logging, and dashboard paths. It changed one static guidance response, added source refs, and tightened tests. No new route, schema, service, or duplicate adaptation protocol was introduced.
- Tradeoff: the general chat answer is still static unless the user has logged the miss. That is acceptable for now because logged misses already flow through `TrainingAdaptationService` and `WorkoutService.next_workout()`.

### Failures and fixes

- Hebrew web search was not useful for this specific topic in the current environment. Logged the limitation instead of using weak search snippets.
- No runtime failures after the code change. The full backend suite passed.

### Next research target

- Loop 24 should research returning after a longer break or repeated missed sessions: how much to reduce volume/intensity, when to repeat the prior week, when to resume progression, and how to phrase this in Hebrew without guilt or unsafe "make-up" training.

## Loop 24 - 2026-06-24

### Sources reviewed

- ACSM position stand, "Progression Models in Resistance Training for Healthy Adults" (Med Sci Sports Exerc, 2009, PMID 19204579): progressive resistance training should be goal-specific and adjusted to training status; novice training commonly uses 8-12RM loading; load increases should be small when the trainee exceeds the target by 1-2 reps; recommendations must be applied in context.
- Halonen et al. 2024, "Does Taking a Break Matter-Adaptations in Muscle Strength and Size Between Continuous and Periodic Resistance Training" (PMID 39364857): a 10-week training, 10-week break, 10-week retraining group regained detraining losses rapidly during retraining; short breaks should not cause panic in lifelong strength training.
- Ogasawara et al. 2013, "Comparison of muscle hypertrophy following 6-month of continuous and periodic strength training" (PMID 23053130): 3-week detraining / 6-week retraining cycles produced similar overall hypertrophy and strength results to continuous training after 24 weeks.
- Blocquiaux et al. 2020, older men detraining/retraining study (PMID 32017951): 12 weeks detraining caused modest strength/power losses, while less than 8 weeks of retraining restored 1RM to the post-training level.
- Hwang et al. 2017, trained men short-term detraining study (PMID 28328712): strength gains were maintained after 2 weeks of detraining in trained young men.
- ODPHP / Physical Activity Guidelines safe-activity guidance: choose activity appropriate to current fitness and increase gradually; inactive people should start low and progress slowly.

### Rules extracted

- A longer break is not a reset to zero, but it is also not permission to resume old numbers immediately.
- Do not prescribe catch-up training after a break. The first goal is re-entry: restore rhythm, technique, and recoverability.
- For several weeks off, a practical first-week heuristic is about 60-80% of prior volume or load, RPE 5-7, and 2-4 reps in reserve.
- Resume progression only after 2-3 clean logs without unusual pain, unusual fatigue, or technique breakdown.
- If the break was caused by illness, pain, bad sleep, or a stressful life period, start lower than the normal re-entry dose.
- If the user asks for a saved "return plan", route to the workout-plan builder and persist a plan. If the user asks "how do I come back?", answer with guidance and do not create fake plan state.

### Changes made

- Updated `backend/app/services/coach_intent_service.py`:
  - Added `return_after_break_guidance` detection for Hebrew/English longer-break wording.
  - Kept workout-plan detection ahead of this guidance path so "build me a return plan" still creates a saved plan.
  - Added "חזרה אחרי" and "אחרי הפסקה" as workout-plan vocabulary so Hebrew return-plan requests are not lost as generic chat.
- Updated `backend/app/services/coach_engine.py`:
  - Added `_return_after_break_guidance_response()` with Hebrew-first re-entry guidance: no compensation workout, 60-80% volume/load, RPE 5-7, 2-4 RIR, log RPE/pain/fatigue, progress after 2-3 clean sessions.
  - Wired the new intent into the existing local-tool and provider-fallback maps.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added the 60-80% re-entry rule and research source refs to `program_adaptation_protocols.return_after_break`.
- Updated tests:
  - Intent tests cover "לא התאמנתי חודש", feminine "חוזרת אחרי הפסקה", and saved return-plan routing.
  - Chat test verifies no plan is saved for a guidance-only return-after-break question.
  - Knowledge test verifies the new rule and source refs.

### Tests and checks

- Focused intent test: `1 passed`.
- Focused return-after-break chat test: `1 passed`.
- Focused knowledge adaptation test: `1 passed`.
- Intent suite: `23 passed`.
- Return/missed chat focused tests: `2 passed`.
- Coach engine + intent suite: `100 passed`.
- Coaching knowledge suite: `112 passed`.
- Full backend suite: `444 passed`.

### Manual Hebrew probe

- Chat request: `לא התאמנתי חודש, איך לחזור לחדר כושר בלי להיפצע?`
  - `status_code=200`
  - `provider_status=local_tool`
  - response contained `60-80%`, `RPE 5-7`, and `2-3 אימונים נקיים`
  - response rejected a compensation workout and gave one next action: short basic workout plus RPE/pain/fatigue logging.

### Ponytail Review

- Lean already. Ship.
- Reason: Loop 24 added one intent detector, one local response, one existing knowledge-node update, and direct tests. It did not create a new route, schema, service, scheduler, or separate return-to-training engine.
- Tradeoff: the 60-80% rule is a conservative product heuristic derived from gradual-progression and detraining evidence, not a universal clinical prescription. The response phrases it as "בערך" and routes pain/illness caution conservatively.

### Failures and fixes

- Initial intent test exposed a real routing bug: `תבנה לי תוכנית חזרה אחרי חודש הפסקה בבית` fell through to `general_chat`. Fixed by adding return-after-break terms to workout-plan language.
- First manual probe returned exit code 1 because Windows held a temporary SQLite file during cleanup. Reran with cleanup errors ignored and got a clean verification result.
- A literal Hebrew token in the probe assertion encoded inconsistently in PowerShell; reran with Unicode escapes and verified all expected response tokens.

### Next research target

- Loop 25 should research how the bot should modify a saved monthly or two-week plan after repeated missed sessions: when to reduce days per week, when to switch to minimum-version days, and when to ask one critical follow-up instead of rebuilding the whole plan.

## Loop 25 - 2026-06-24

### Sources reviewed

- Peng et al. 2022, "The Effectiveness of Planning Interventions for Improving Physical Activity in the General Population" (PMID 35742582): planning interventions improved physical activity behavior overall, with stronger effects in some contexts and when reinforcement/follow-up was used.
- Lin et al. 2022, "Making Specific Plan Improves Physical Activity and Healthy Eating for Community-Dwelling Patients With Chronic Conditions" (PMID 35664117): implementation intentions/specific action plans had small but significant effects on physical activity and diet behavior.
- Kompf 2020, "Implementation Intentions for Exercise and Physical Activity: Who Do They Work For?" (PMID 31923898): implementation intentions help some users translate intention into behavior, especially when intention/self-efficacy already exist; they are not magic for everyone.
- Yang et al. 2025 meta-analysis on the exercise intention-behavior gap (PMID 40470022): intention-behavior relationship is moderate; action planning, coping planning, and action control mediate behavior.
- Nicolson et al. 2017 BJSM review on therapeutic-exercise adherence (PMID 28087567): booster sessions, motivational strategies, and behavioral graded exercise can support adherence in pain/older-adult contexts; action/coping plans alone were not consistently enough.
- Schoenfeld et al. 2017 dose-response meta-analysis on weekly resistance-training volume (PMID 27433992): higher weekly volume tends to produce greater hypertrophy, but the presence of a dose-response also supports reducing volume when adherence is failing rather than chasing maximal volume.

### Rules extracted

- Repeated missed/partial sessions are a plan-fit signal, not a motivation failure.
- After two or more recent missed/partial sessions, do not immediately rebuild the whole program. First reduce the plan surface area.
- Practical adaptation: temporarily reduce one training day per week or convert one day into a minimum-version day.
- Ask one critical follow-up only: identify the recurring blocker as time, fatigue, pain, or equipment.
- Keep pain and high-RPE safety signals higher priority than adherence shrinkage.
- The saved plan should not be auto-mutated yet. The app should expose a structured recommendation so the UI/coach can confirm the change before editing plan state.

### Changes made

- Updated `backend/app/services/training_adaptation_service.py`:
  - Repeated adherence events (`skipped + partial/modified >= 2`) now return a stronger `adherence_risk` summary.
  - Added structured `plan_adjustment` with:
    - `type=reduce_plan_before_rebuild`
    - `recommendation=reduce_days_or_add_minimum_day`
    - `reduce_days_per_week_by=1`
    - `use_minimum_version_days=true`
    - one critical question about the recurring blocker.
- Updated `backend/app/services/workout_service.py`:
  - `/api/workouts/next` execution plan now includes `plan_adjustment`.
- Updated `backend/app/services/dashboard_service.py`:
  - Dashboard `next_workout` summary now includes `plan_adjustment`.
  - `next_recommended_action` naturally surfaces the stronger repeated-miss adjustment.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added repeated-miss adaptation rule and source refs under `program_adaptation_protocols.missed_sessions`.
- Updated tests:
  - Training adaptation service checks the structured plan adjustment.
  - Next-workout API checks the structured recommendation is returned.
  - Dashboard checks the user-visible next action includes the reduction recommendation and one critical question.
  - Knowledge test checks the repeated-miss rule and planning source refs.

### Tests and checks

- Focused training adaptation suite: `6 passed`.
- Focused next-workout repeated-miss API test: `1 passed`.
- Focused dashboard test: `1 passed`.
- Focused knowledge adaptation test: `1 passed`.
- Adaptation + workout logs + dashboard suites: `31 passed`.
- Coaching knowledge suite: `112 passed`.
- Full backend suite: `445 passed`.

### Manual Hebrew probe

- Flow:
  - Chat request: `תבנה לי תוכנית חודשית 3 ימים בשבוע בבית למתחיל`
  - Logged first workout as skipped.
  - Logged second workout as partial.
  - Read `/api/workouts/next` and `/api/dashboard`.
- Result:
  - plan created with `provider_status=local_tool`
  - saved `plan_type=monthly_plan`, `days_per_week=3`
  - next workout `load_signal=adherence_risk`
  - `plan_adjustment.type=reduce_plan_before_rebuild`
  - dashboard action says the plan is probably too large right now, suggests reducing one day or using a minimum-version day, and asks one blocker question: time, fatigue, pain, or equipment.

### Ponytail Review

- Lean already. Ship.
- Reason: no auto-migration, no new route, no plan-rewrite engine, and no schema change. The loop added one structured field to an existing adaptation summary and exposed it through existing next-workout/dashboard responses.
- Tradeoff: the saved plan is not modified automatically. That is deliberate: two failed logs are enough to recommend a smaller plan, not enough to silently mutate product state.

### Failures and fixes

- No code test failures in Loop 25.
- The first manual probe assumed serialized chat-created plan days included `workout_id`. That was not true in the local DB object used by the probe. Fixed the probe by reading `Workout` rows for the saved plan.

### Next research target

- Loop 26 should research when the bot should ask a follow-up question before plan generation versus infer defaults: identify truly critical missing info for single workout, weekly, two-week, and monthly plans, and make the Hebrew prompts shorter without losing safety.

## Loop 26 - 2026-06-24

### Sources reviewed

- Whitfield et al. 2017, applying the ACSM preparticipation screening algorithm to U.S. adults (PMID 28557860): the updated ACSM screen aims to reduce unnecessary medical-clearance barriers while still considering current activity, known cardiovascular/metabolic/renal disease, symptoms, and desired intensity.
- ACSM progression model evidence from earlier loops remains relevant: exercise prescription should be contextual and based on training status rather than forcing every user through a full questionnaire.
- ODPHP / Physical Activity Guidelines safe-activity guidance remains relevant: inactive or uncertain users should start low and progress gradually.
- Exercise is Medicine and Mayo warning-symptom guidance from prior loops remains the safety boundary: pain location/quality and red-flag symptoms are critical; missing convenience fields are not.

### Rules extracted

- Critical missing info is safety-relevant info: unclear pain, red-flag symptoms, illness/injury context, or a request that implies unsafe intensity.
- Missing duration, equipment, goal, or experience level should usually be inferred conservatively and stored as assumptions instead of triggering a questionnaire.
- For a single workout, missing duration should default shorter than a persistent plan. A 30-minute one-off is more practical and safer than a 45-minute default when the user just asks for "an workout today".
- Persistent weekly/two-week/monthly plans can keep the existing 45-minute conservative default because they are meant to be editable stored plans, not an immediate session.
- The user-facing Hebrew response should show only a small number of assumptions, not the full internal assumption list.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - Single-workout requests without explicit/profile/inferred duration now default to `30` minutes.
  - Persistent plans still default to `45` minutes.
  - Assumptions now say `לא צוין משך אימון, הנחתי 30 דקות לאימון יחיד.` for one-off workouts.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added a critical-info policy rule that single-workout missing duration is not a reason to ask a question.
  - Added ACSM preparticipation screening and ODPHP safe-activity source refs.
- Updated tests:
  - API test proves `תן לי אימון יחיד להיום` becomes a 30-minute `single_workout`, is not current, and stores the 30-minute assumption.
  - Knowledge test proves the critical-info policy includes the single-workout 30-minute rule and ACSM source ref.

### Tests and checks

- Focused single-workout default test: `1 passed`.
- Focused knowledge critical-info test: `1 passed`.
- Workout-plan + coach engine suites: `106 passed`.
- Coaching knowledge suite: `112 passed`.
- Full backend suite: `446 passed`.

### Manual Hebrew probe

- Chat request: `תן לי אימון יחיד להיום`
  - `status_code=200`
  - `provider_status=local_tool`
  - response did not ask a follow-up question
  - response showed only two assumptions: general fitness goal and 30-minute one-off duration
  - saved `plan_type=single_workout`
  - saved `is_current=false`
  - saved `session_length_minutes=30`
  - stored assumptions include bodyweight, beginner, and missing profile defaults internally.

### Ponytail Review

- Lean already. Ship.
- Reason: one default branch, one assumption phrase, one knowledge rule, and two tests. No new questionnaire layer, prompt protocol, service, schema, or route.
- Tradeoff: this does not solve all missing-info policy for weekly/two-week/monthly plans. It handles the most user-visible over-questioning risk first: one-off Hebrew workout requests.

### Failures and fixes

- No code or test failures in Loop 26.

### Next research target

- Loop 27 should research and implement how follow-up questions should work for plan changes/replacements: when to ask confirmation, when to create a candidate, and how to avoid accidental replacement of the active plan in Hebrew chat.

## Loop 27 - 2026-06-24

### Sources reviewed

- Nielsen Norman Group, "10 Usability Heuristics for User Interface Design": visibility of system status, speaking the user's language, user control/freedom, and error prevention. The relevant product rule is that high-cost destructive actions should be prevented or confirmed before committing, while the interface should stay focused and not over-explain.
- Existing CALO BOT pending-action flow: `PendingActionService` already supports candidate plans, explicit activation, decline/removal, and preserving the current active plan until confirmation.

### Rules extracted

- Creating a new persistent workout plan while another persistent plan is active should create a candidate, not silently replace the current plan.
- Confirmation must be explicit enough for a destructive state change. A plain short `כן` can confirm inside an already pending confirmation state, but ambiguous Hebrew like `כן אבל...` should not activate or delete anything.
- Decline must also be explicit enough. A plain short `לא` can decline inside the pending confirmation state, but `לא בטוח...` should keep the candidate pending because it is a question, not a decision.
- The bot should use natural Hebrew commands in the confirmation prompt: `כן להחליף` and `להשאיר קיימת`.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - Added `_normalize_plan_replacement_decision`.
  - Tightened `_confirms_plan_replacement` so ambiguous `כן אבל...` does not activate a candidate plan.
  - Tightened `_declines_plan_replacement` so ambiguous `לא בטוח...` does not delete the candidate.
  - Kept the existing candidate-plan architecture instead of adding a new route or schema.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added `plan_replacement_policy` under `plan_horizon_protocols`.
  - Documented candidate-vs-active behavior, explicit approval wording, ambiguous yes/no handling, and decline behavior.
- Updated tests:
  - Added a pending replacement test for ambiguous Hebrew yes.
  - Added a pending replacement test for ambiguous Hebrew no.
  - Extended the knowledge-center test to require the plan replacement policy.

### Tests and checks

- Pending replacement focused tests: `4 passed`.
- Focused knowledge plan-horizon test: `1 passed`.
- Affected suites (`coach_engine`, `coaching_knowledge`, `workout_plans_api`): `220 passed`.
- Full backend suite: `448 passed`.

### Manual Hebrew probe

- Flow:
  - Created an active current plan.
  - Chat request: `תבנה לי תוכנית חדשה חודשית 4 ימים בשבוע להיפרטרופיה`
  - Pending candidate was created while the current plan remained active.
  - Ambiguous reply: `כן אבל יש לי שאלה על RPE`
  - Explicit reply after that: `כן להחליף`
- Result:
  - `pending_initial=pending`
  - ambiguous response answered the RPE question and did not activate the candidate
  - `pending_after_ambiguous=pending`
  - `candidate_is_current_after_ambiguous=False`
  - explicit `כן להחליף` activated the candidate
  - `activated_is_current=True`

### Ponytail Review

- Lean already. Ship.
- Reason: the loop changed two matcher functions, added one small normalization helper, and documented the rule in the existing knowledge center. It did not add a second pending-action system, extra database state, a new router, or a speculative plan-replacement workflow.
- Tradeoff: the matcher is still phrase-based. That is acceptable here because the pending action is narrow, stateful, and covered by focused Hebrew ambiguity tests.

### Failures and fixes

- No code or test failures in Loop 27.

### Next research target

- Loop 28 should research how to handle scoped edits to an existing plan versus full replacement: for example `תחליף לי רק את יום הרגליים`, `אין לי ספסל`, or `תוריד נפח מהתוכנית`. The goal is to avoid rebuilding a whole plan when the user asked for a smaller plan update.

## Loop 28 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training guideline update: consistency, individualization, home equipment/bodyweight validity, strength loading around 80% 1RM for many strength goals, and hypertrophy volume around 10 sets per muscle as a practical anchor rather than a hard target.
- NSCA resistance training frequency guidance: training status, workload, schedule, and recovery should shape frequency; novice plans usually favor 2-3 nonconsecutive days, while intermediate split routines can distribute stress across body parts or movement patterns.
- HPRC/NSCA exercise selection guidance: exercise order and selection should respect goal, safe technique, movement categories, and push/pull balance.
- NASM resistance training guidance: home/bodyweight training can be valid when difficulty is scaled and technique is preserved.
- FitStreet Hebrew workout-plan guide: define the goal, choose a sustainable weekly frequency, use movement patterns such as squat/pull/press/hinge, avoid exercises that currently cause joint pain, and treat the plan as a guideline that can be changed later.
- Fitnessophy Hebrew plans: advanced splits and bodyweight circuits can be useful, but weekly frequency and rest still need to match recovery and level.
- Nielsen Norman Group usability heuristics: destructive or high-cost changes need user control and error prevention; vague requests should trigger a focused clarification rather than a silent rebuild.

### Rules extracted

- A scoped edit to the active plan is not a new plan. Do not create a candidate plan or rerun the whole builder when the user asks for a narrow equipment, exercise, day, or volume change.
- If the user says equipment is missing, mutate only affected exercises and alternatives while preserving the movement pattern.
- If the user asks for less volume because of fatigue/load, reduce one set from existing exercises before changing exercise selection or replacing the plan.
- If the request is vague, ask one targeted question: exercise/equipment, volume, or specific day.
- Persist edits in both `WorkoutPlan.plan_json` and the derived `Workout` / `WorkoutExercise` rows so dashboard, next-workout, and logging stay consistent.

### Changes made

- Updated `backend/app/services/coach_intent_service.py`:
  - Added `workout_plan_edit` routing for active-plan edit language in Hebrew and English.
  - Kept this before full workout-plan generation so scoped edits do not become replacement candidates.
- Updated `backend/app/services/workout_service.py`:
  - Added `apply_scoped_plan_edit`.
  - Added no-bench scoped edits that remove bench requirements, filter bench alternatives, preserve movement pattern, and sync plan rows.
  - Added reduce-volume scoped edits that lower sets by one where possible and sync plan rows.
  - Added one-question clarification for vague edit requests.
  - Added `plan_edit_history` entries inside `plan_json`.
- Updated `backend/app/services/coach_engine.py`:
  - Routed `workout_plan_edit` to `WorkoutService.apply_scoped_plan_edit`.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added `scoped_plan_edit_policy` under `plan_horizon_protocols`.
- Updated tests:
  - Intent detection for scoped active-plan edits.
  - Chat/API no-bench edit without replacement.
  - Chat/API reduce-volume edit without replacement.
  - Vague edit clarification without changing the plan.
  - Knowledge-center assertions for scoped edit policy.

### Tests and checks

- Focused scoped edit tests after fixes: `3 passed`.
- Focused intent + knowledge tests: `2 passed`.
- Affected suites (`coach_intent_service`, `coach_engine`, `coaching_knowledge`, `workout_plans_api`): `247 passed`.
- Full backend suite after Ponytail cleanup: `452 passed`.

### Manual Hebrew probe

- Flow:
  - Created a current 3-day dumbbell plan with bench.
  - Chat request: `אין לי ספסל בתוכנית, תחליף רק את מה שצריך`.
  - Chat request: `תוריד נפח מהתוכנית השבוע, אני עייף`.
  - Chat request: `תשנה לי את התוכנית`.
- Result:
  - `plans_count=1`
  - `pending_actions=0`
  - no-bench response used `provider_status=local_tool`
  - no-bench response mentioned scoped editing with `בלי לבנות חדשה`
  - `bench_in_equipment=false`
  - `bench_word_in_plan_json=false`
  - `bench_word_in_row_alternatives=false`
  - reduce-volume response used `provider_status=local_tool`
  - `sets_before_reduce=2`
  - `sets_after_reduce=1`
  - `first_row_sets_after_reduce=1`
  - vague edit response used `provider_status=local_tool`
  - vague edit asked one targeted question
  - `vague_changed_plan=false`

### Ponytail Review

- Finding: `backend/app/services/workout_service.py:L187-L192,L242-L246: yagni: apply_scoped_plan_edit returned serialized workout_plan even though the only caller discarded it. Cut the payload and serialization.`
- Finding: `backend/app/services/workout_service.py:L203: delete: changed_exercises was initialized before both branches assigned it. Cut the dead assignment.`
- Applied both cuts.
- Net: `-3` lines plus one avoided serialization pass.

### Failures and fixes

- Initial scoped edit tests failed because `WorkoutExercise` was referenced without importing it in `backend/tests/test_coach_engine.py`; fixed the import.
- The first manual probe was invalid because inline PowerShell mangled Hebrew text and chat fell through to the configured provider. Re-ran with Unicode-escaped Hebrew and explicit no-key environment.
- The first manual probe also hit a Windows SQLite temp-file cleanup lock; re-ran using a persistent disposable temp DB path and closed the client/session explicitly.

### Next research target

- Loop 29 should research and implement pain-specific scoped edits inside an active plan: for example `כואבת לי הברך בסקוואט שבתוכנית, תחליף רק את זה`. The goal is to preserve the plan, ask only for missing critical pain location/severity when needed, replace only the affected movement with safer alternatives, and keep safety/audit behavior tied to the edit.

## Loop 29 - 2026-06-24

### Sources reviewed

- ACSM 2026 resistance training guideline update: individualization and safety matter more than rigid templates; a plan that is too demanding or unsafe to maintain loses effectiveness.
- NSCA resistance training frequency guidance: workload, stress, and recovery influence training frequency; pain or high stress should reduce workload rather than trigger a maximal plan.
- HPRC/NSCA exercise selection guidance: multi-joint movements are useful but technique and fatigue affect safety; substitutions should preserve exercise category where possible.
- Mayo Clinic patellofemoral pain syndrome guidance: knee pain often increases with squatting; rest from aggravating movements, rehabilitation, knee alignment, and slower build-up are safer than pushing through.
- AAFP Management of Patellofemoral Pain Syndrome: PFPS is linked with patellofemoral overload, squatting can multiply knee load, physical therapy is first-line, and training errors/overuse matter.
- Men's Health / Ebenezer Samuel C.S.C.S. box squat reference: box squat can replace a standard squat for people with knee issues by using a controlled stop and more vertical shin angle.
- Tom's Guide / Sam Hopes trainer page with E3 Rehab Spanish squat reference: isometric squat variants can build quad/knee capacity with less joint motion, and beginners can start with shallower holds.
- FitStreet Hebrew workout-plan guide: Hebrew coaching language should preserve movement patterns such as squat/pull/press/hinge and choose exercises the user can currently do safely.
- Facebook/general social search: searched public Facebook/trainer-style results for knee pain + squat replacement in Hebrew/English; no stable accessible public post was usable as a source, so I did not encode rules from unverifiable social snippets.

### Rules extracted

- Clear pain edit inside an active plan is not a rebuild. If the user says the knee hurts in a squat in the current plan, edit only the squat-pattern exercise.
- Keep the movement pattern when safe: squat pattern becomes a safer squat regression, not a random replacement.
- For knee/squat pain, use conservative substitutions first: box squat / short-range squat / sit-to-stand, reduce one set, remove aggressive step/lunge alternatives, and add safety notes.
- Vague pain is missing critical safety information. Ask one question about pain location and whether it is sharp/worsening before changing the plan.
- Red flags remain safety-layer work, not plan editing: chest pain, dizziness, fainting, unusual shortness of breath, sharp/worsening pain.
- Persist the edit in `WorkoutPlan.plan_json`, sync `WorkoutExercise` rows, and record the soft pain event through the existing `SafetyEvent` path.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - Added pain-aware scoped edit detection for active-plan edits.
  - Added `pain_clarification` for pain without a clear area.
  - Added `pain_substitution` for clear knee/squat edits.
  - Added a knee/squat mutation that renames squat work to `סקוואט לקופסה בטווח קצר`, reduces sets by one, removes risky step/lunge alternatives, adds sit-to-stand as an alternative, and adds safety notes.
  - Reused existing plan row syncing so `WorkoutExercise` rows match the edited plan JSON.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added scoped pain-edit rules and sources under `scoped_plan_edit_policy`.
- Updated tests:
  - Intent detection for `כואבת לי הברך בסקוואט שבתוכנית, תחליף רק את זה`.
  - Chat/API test for knee/squat scoped edit with no replacement candidate.
  - Chat/API test for vague pain asking one safety question without changing the plan.
  - Knowledge-center assertions for pain edit rules and medical/coaching sources.

### Tests and checks

- Focused Loop 29 chat tests after fixes: `2 passed`.
- Focused intent + knowledge tests: `2 passed`.
- Affected suites (`coach_intent_service`, `coach_engine`, `coaching_knowledge`, `workout_plans_api`, `workout_logs_api`, `training_adaptation_service`): `273 passed`.
- Full backend suite after Ponytail cleanup: `454 passed`.

### Manual Hebrew probe

- Flow:
  - Created a current 4-day intermediate gym hypertrophy plan.
  - Chat request: `כואבת לי הברך בסקוואט שבתוכנית, תחליף רק את זה`.
  - Chat request: `כואב לי בתוכנית, תחליף את התרגיל`.
- Result:
  - `plans_count=1`
  - `pending_actions=0`
  - `safety_events=2`
  - pain edit response used `provider_status=local_tool`
  - `pain_safety_flagged=false`
  - response mentioned `בלי לבנות תוכנית חדשה`
  - response mentioned `טווח ללא כאב`
  - target row name includes `קופסה`
  - `sets_before=3`
  - `row_sets_after=2`
  - risky step/lunge alternatives removed from the row
  - `edit_history_type=pain_substitution`
  - vague pain response used `provider_status=local_tool`
  - vague pain asked for pain location and sharp/worsening severity
  - `vague_changed_plan=false`

### Ponytail Review

- Finding: `backend/app/services/workout_service.py:L840-L847: shrink: one-use _is_knee_area and _text_targets_squat wrappers. Inline the two substring checks inside _apply_pain_substitution_to_days.`
- Applied the cut.
- Net: `-8` lines possible; actual net reduction applied inside the loop.

### Failures and fixes

- Initial pain edit test assumed every squat in the plan had the same starting set count as the first target squat. Fixed the test to assert exact set reduction on the synced target row and only stable safety invariants across all squat-pattern exercises.

### Next research target

- Loop 30 should research and implement scoped edits for non-knee pain areas with clear exercise targets, starting with shoulder pain in pressing exercises and lower-back pain in hinge/deadlift patterns. The goal is to reuse the same scoped-edit architecture without creating a broad injury diagnosis engine.

## Loop 30 - 2026-06-24

### Sources reviewed

- Men's Health landmine press coaching reference: overhead shoulder mobility can be too much for beginners or people with prior shoulder issues; landmine press changes the press angle up/forward, eases joint load, and half-kneeling helps avoid lumbar arching.
  - https://www.menshealth.com/fitness/a66328946/landmine-press-shoulder-benefits/
- GQ deadlift expert-trainer guide: deadlift success depends on a hip hinge, straight spine, bracing/lats, bar close to body, and avoiding the common lower-back stress pattern where hips rise too fast or the lifter leans back at lockout.
  - https://www.gq.com/story/how-to-deadlift-with-perfect-form-according-to-expert-trainers
- Verywell Health deadlift back-pain medical review: lower-back pain after deadlifts is often tied to improper form, too much load, inadequate warm-up, overtraining, weak core/glutes, mobility limits, or prior back problems; severe/persistent pain and radiating/numbness/weakness signs need care.
  - https://www.verywellhealth.com/lower-back-pain-after-deadlift-8674741
- Mayo Clinic back-pain guidance: persistent back pain should be evaluated, and movement/yoga-style activities may need adjustment if symptoms worsen.
  - https://www.mayoclinic.org/diseases-conditions/back-pain/diagnosis-treatment/drc-20369911
- Existing CALO knowledge center: already had shoulder-sensitive push/pull and lower-back-sensitive hinge protocols, so the implementation reused those rules instead of adding a parallel injury system.
- Hebrew/Facebook/general search: searched Hebrew and social-style results for shoulder press pain, lower-back deadlift pain, landmine press, and hinge regressions. Stable public Israeli coach pages/posts were not accessible enough to encode as sources, so no unverifiable social snippets were turned into product rules.

### Rules extracted

- Clear pain + clear exercise target remains a scoped edit, not a full plan replacement.
- Shoulder pain in a press should edit only the named push pattern: vertical press becomes a friendlier angled press such as landmine/half-kneeling; horizontal press can move to incline push-up or neutral-grip floor press.
- Shoulder substitutions should reduce one set, keep RPE around 5-7, keep range pain-free, prefer neutral grip/angle changes, and stop with sharp/worsening pain, weakness, numbness, or radiating symptoms.
- Lower-back pain in deadlift/hinge should edit only hip-hinge work: regress to wall hip hinge / glute bridge / light pull-through, reduce one set, keep neutral spine and short range.
- `הגב התחתון` is natural Hebrew and must be detected as `גב תחתון`.
- Structured `movement_pattern` should be authoritative for push and hinge matching; text fallback is only for older/unstructured exercises. Knee/squat remains slightly broader because split-squat style names can contain `סקוואט` even when the movement pattern is `lunge`.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - Added scoped pain substitutions for shoulder/press and lower-back/deadlift-hinge requests.
  - Added targeted matching so `לחיצת כתפיים` changes vertical press and does not mutate chest press.
  - Added lower-back hinge regression to `היפ הינג' לקיר` with glute-bridge/light pull-through alternatives and safety notes.
  - Tightened matching so structured movement patterns win over fuzzy text for push/hinge cases.
- Updated `backend/app/services/pain_text.py`:
  - Added lower-back Hebrew aliases for `הגב התחתון` and `גב התחתון`.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added shoulder-press and lower-back-hinge scoped edit rules and source references to `scoped_plan_edit_policy`.
- Updated tests:
  - Intent detection for Hebrew shoulder and lower-back active-plan edit phrases.
  - Chat/API persisted-plan test for shoulder press pain that keeps the active plan, edits vertical press, and leaves chest press unchanged.
  - Chat/API persisted-plan test for lower-back deadlift pain that edits hip hinge and removes heavy RDL alternatives.
  - Knowledge-center assertions for new scoped pain-edit rules and source references.

### Tests and checks

- Initial focused run used the wrong knowledge-test name and collected no knowledge test; reran with the exact test name.
- Focused Loop 30 tests after fixes: `6 passed`.
- Affected suites (`coach_intent_service`, `coach_engine`, `coaching_knowledge`, `workout_plans_api`, `workout_logs_api`, `training_adaptation_service`): `275 passed`.
- Full backend suite after final matcher cleanup: `456 passed`.
- `git diff --check`: exit code `0`; only existing CRLF conversion warnings.

### Manual Hebrew probe

- Flow:
  - Created a current 4-day intermediate gym hypertrophy plan.
  - Chat request: `כואבת לי הכתף בלחיצת כתפיים שבתוכנית, תחליף רק את זה`.
  - Chat request: `כואב לי הגב התחתון בדדליפט שבתוכנית, תחליף רק את זה`.
  - Chat request: `כואב לי בתוכנית, תחליף את התרגיל`.
- Result:
  - `plans_count=1`
  - `pending_actions=0`
  - `safety_events=["pain_signal","pain_signal","pain_signal"]`
  - shoulder response used `provider_status=local_tool`
  - `shoulder_safety_flagged=false`
  - vertical press row changed to `לחיצת לנדמיין חצי כריעה`
  - chest press row stayed unchanged for a shoulder-press request
  - lower-back response used `provider_status=local_tool`
  - `back_safety_flagged=false`
  - hinge row changed to `היפ הינג' לקיר`
  - hinge alternatives became `גשר ישבן`, light cable pull-through, and stick hip hinge
  - vague pain response used `provider_status=local_tool`
  - `vague_changed_plan=false`

### Ponytail Review

- Pre-review cleanup: changed `_exercise_matches` so an existing `movement_pattern` is authoritative, with text fallback only for older/unstructured exercises.
- Formal Ponytail Review after cleanup: Lean already. Ship.
- Net: no further useful deletion found.

### Failures and fixes

- Shoulder edit initially changed chest press too because the fallback text matcher treated generic `לחיצ` as enough. Fixed by deriving vertical vs horizontal push targets from the user phrase.
- Lower-back edit initially asked for clarification because `הגב התחתון` did not match the existing `גב תחתון` aliases. Fixed in `pain_text.py`.
- A matcher cleanup initially missed split-squat variants in the knee test. Fixed by keeping named squat variants eligible for knee/squat scoped edits while preserving movement-pattern authority for push/hinge.
- Manual probe initially exited nonzero because Windows held the temporary SQLite file during cleanup. Reran with explicit client/session close and `ignore_cleanup_errors=True`.

### Next research target

- Loop 31 should move from pain-specific edits to named exercise substitutions inside an active plan: for example `תחליף לי את הדדליפט`, `אין לי מכונה לחתירה`, or `שכיבות סמיכה קשות מדי`. Research should cover preserving movement patterns, equipment-mode substitutions, beginner regressions/progressions, and Hebrew slang for exercise names without turning the bot into a broad free-text exercise parser too early.

## Loop 31 - 2026-06-24

### Sources reviewed

- Women's Health movement-pattern strength guide: trainers organize strength work around push, pull, squat, lunge, and hinge patterns; substitutions should preserve the pattern instead of swapping randomly.
  - https://www.womenshealthmag.com/fitness/g27393163/strength-training-exercises/
- Women's Health / Cori Ritchey, C.S.C.S. push-up guidance: push-ups are technically demanding; struggling users can use knees, incline on a bench/table, or slow eccentrics before full push-ups.
  - https://www.womenshealthmag.com/fitness/a65371604/push-up-tips/
- SELF / Jenny McCoy, NASM-CPT, with Evan Williams CSCS/CPT: inverted/bodyweight rows are horizontal pulling alternatives; they can be scaled with bent knees, higher bar angle, suspension straps, sturdy table/chair, or towel setup.
  - https://www.self.com/story/how-to-do-inverted-row
- Existing CALO knowledge center: `equipment_substitution_protocols`, `exercise_substitution`, and structured exercise-library patterns already had the core rule: preserve movement pattern, target muscle, and usable equipment.
- Hebrew/Facebook/general search: searched Hebrew/social-style results for machine row alternatives, push-up regressions, and trainer language around `קשה מדי`. Stable public Israeli coach posts were not accessible enough to encode as source rules, so the loop used verifiable web trainer pages plus existing Hebrew exercise language in the repo.

### Rules extracted

- Named exercise substitution should be narrow and reason-aware, not a general free-text parser.
- If the user says a specific machine is unavailable, replace only exercises/alternatives that require that machine and keep the same movement pattern.
- If an exercise is too hard but not painful, regress the same movement pattern first, reduce one set if needed, and give a simple progression gate.
- If the user asks to replace a major lift without a reason, do not guess. Ask one question about equipment, pain, difficulty, or preference.
- Hebrew phrasing like `שכיבות סמיכה קשות מדי` should trigger an active-plan edit when the message references the plan.

### Changes made

- Updated `backend/app/services/coach_intent_service.py`:
  - Added `קשה מדי`, `קשות מדי`, `קשים מדי`, `too hard`, and `too difficult` as active-plan edit language.
- Updated `backend/app/services/workout_service.py`:
  - Added `replace_row_machine` for `אין לי מכונה לחתירה בתוכנית`.
  - Added `regress_pushup` for `שכיבות סמיכה קשות מדי בתוכנית`.
  - Added `exercise_clarification` for unsupported named replacement such as `תחליף לי את הדדליפט בתוכנית`.
  - Added scoped row substitution to `חתירת משקולת יד בתמיכה` with cable/band/table-row alternatives.
  - Added push-up regression to `שכיבת סמיכה על קיר` with high-incline/knee/incline-plank alternatives.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added named exercise substitution rules to `scoped_plan_edit_policy`.
- Updated tests:
  - Intent tests for row machine unavailable, push-ups too hard, and deadlift replacement without reason.
  - Chat/API persisted-plan tests for row machine substitution and push-up regression.
  - Chat/API clarification test for deadlift replacement without reason.
  - Knowledge-center assertions for the new rules and sources.

### Tests and checks

- Focused Loop 31 tests: `5 passed`.
- Affected suites (`coach_intent_service`, `coach_engine`, `coaching_knowledge`, `workout_plans_api`, `workout_logs_api`, `training_adaptation_service`): `278 passed`.
- Full backend suite after Ponytail cleanup: `459 passed`.

### Manual Hebrew probe

- Flow:
  - Created a current 4-day intermediate gym hypertrophy plan.
  - Chat request: `אין לי מכונה לחתירה בתוכנית, תחליף רק את זה`.
  - Chat request: `תחליף לי את הדדליפט בתוכנית`.
  - Created a separate current 2-day beginner bodyweight plan.
  - Chat request: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
- Result:
  - row response used `provider_status=local_tool`
  - row changed to `חתירת משקולת יד בתמיכה`
  - row alternatives became cable row, band row, and stable-table row
  - deadlift response used `provider_status=local_tool`
  - `deadlift_changed_plan=false`
  - deadlift response asked one reason question: equipment unavailable, too hard, pain, or preference
  - `gym_plans_count=1`
  - `gym_pending_actions=0`
  - push-up response used `provider_status=local_tool`
  - push-up changed to `שכיבת סמיכה על קיר`
  - push-up alternatives became high-incline push-up, knee push-up, incline plank
  - `pushup_pending_actions=0`

### Ponytail Review

- Finding: `backend/app/services/workout_service.py:L827-L855: shrink: three one-use target helpers only wrap substring checks. Inline them in _scoped_plan_edit_type.`
- Applied the cut.
- Net: about `-18` lines possible; applied.

### Failures and fixes

- No functional test failures in Loop 31.
- The first manual probe had a misleading field name for plan count because it reported the second temp DB. Reran with separate `gym_plans_count`, `gym_pending_actions`, and `pushup_pending_actions`.

### Next research target

- Loop 32 should research and improve progression gates after substitutions: when the bot regresses push-ups, swaps rows, or edits pain-sensitive movements, how should the next workout/dashboard decide when to progress back? Focus on simple logged evidence: completion, RPE, pain flag, and technique notes.

## Loop 32 - 2026-06-24

### Sources reviewed

- Health.com progressive-overload guide: progression should be gradual; increases in load, reps, intensity, or time should stay conservative, often around 10% or less per week, and should wait for proper form and recovery.
  - https://www.health.com/progressive-overload-8607549
- SELF progressive-overload guide: increase reps/load/time/frequency only when the user can perform the work safely; RPE/RIR and ease of completion are practical readiness signals.
  - https://www.self.com/story/progressive-overload-training
- SELF guide to lifting heavier weights: use clean reps as the trigger, make small increases, and distinguish normal soreness from pain/injury signals.
  - https://www.self.com/story/guide-to-lifting-heavier-weights
- Women's Health easy-workouts/RPE discussion: harder training around RPE 7-8 drives strength gains, while easier sessions can support recovery and consistency when soreness, fatigue, or aches are present.
  - https://www.womenshealthmag.com/fitness/a71088407/do-easy-workouts-build-strength/
- Existing CALO knowledge center: progression gates, RPE/RIR guidance, movement limitation adaptation, and logged workout adaptation already supported the "log evidence before progression" rule.
- Hebrew/Facebook/general search: searched for Israeli trainer/social posts around RPE, gradual overload, push-up regressions, and progression after substitutions. No stable public source was reliable enough to encode as a rule in this loop, so the implemented rule stayed tied to verifiable coaching sources and the app's logged data model.

### Rules extracted

- Do not auto-return to a harder exercise immediately after a substitution or regression.
- A clean log is the minimum evidence: completed status, no pain flag, and RPE 8 or lower.
- Even after a clean log, progress only one step: do not jump from a wall push-up straight back to the hardest version.
- If the user has pain, high RPE, partial completion, or a skipped workout, existing recovery/adherence rules override the progression gate.
- The next workout should expose the gate as tracking guidance, not silently mutate the plan again.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - Added `substitution_progression_gate` inside the existing execution-plan path.
  - When a clean completed log would normally trigger `small_progression`, edited exercises with substitution/regression notes now get a conservative Hebrew gate instead.
  - The gate says to progress one step only after a clean log, RPE 8 or lower, and no pain; otherwise keep the current version.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added the knowledge-center rule that substitutions/regressions require logged evidence before returning to a harder version.
- Updated tests:
  - Added a route-level workout-log test that creates a beginner bodyweight plan, applies the Hebrew push-up regression edit, logs the edited exercise cleanly at RPE 8, and verifies `/api/workouts/next` returns `substitution_progression_gate`.
  - Added a knowledge-center assertion for the RPE 8 / one-step rule.

### Tests and checks

- Focused new test: `1 passed`.
- Focused Loop 32 set (`workout_logs_api`, push-up scoped edit, knowledge rule, training adaptation service): `9 passed`.
- Affected suites first run: `225 passed`, `1 failed` due Windows `WinError 10055` socket-buffer exhaustion while creating a TestClient portal.
- Failed test rerun in isolation: `1 passed`.
- Affected suites rerun: `226 passed`.
- Full backend suite: `460 passed`.

### Manual Hebrew probe

- Flow:
  - Created a current one-day beginner bodyweight weekly plan.
  - Chat request: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Logged the edited push-up variant as completed with `RPE=8`, `RIR=2`, no pain.
  - Requested `/api/workouts/next`.
- Result:
  - `edit_provider_status=local_tool`
  - edited exercise became `שכיבת סמיכה על קיר`
  - edited sets became `1`
  - alternatives became high-incline push-up, knee push-up, and incline plank
  - `log_load_signal=progress_candidate`
  - `next_load_signal=progress_candidate`
  - adjusted exercise used `adjustment=substitution_progression_gate`
  - execution note required a clean log, no pain, `RPE 8` or lower, and `שלב אחד בלבד`
  - `pending_actions_count=0`

### Ponytail Review

- Formal Ponytail Review: Lean already. Ship.
- Net: no useful deletion found. The implementation is a small branch in the existing execution planner and the test exercises the public API path.

### Failures and fixes

- The first manual probe used raw Hebrew through a PowerShell here-string, and the text reached Python as question marks. Reran with Unicode-escaped Hebrew so the API received the actual user message.
- The first manual probe also exited nonzero because Windows held the temporary SQLite file. Reran with explicit TestClient/session cleanup and `ignore_cleanup_errors=True`.
- No code fix was needed from those probe issues.

### Next research target

- Loop 33 should connect plan-edit/progression evidence to user-facing recommendations outside the raw next-workout payload: dashboard next action, weekly summary language, or active-plan view. Research should focus on how coaches communicate progression gates and substitutions without overcomplicating the UI or prompting the user with long questionnaires.

## Loop 33 - 2026-06-24

### Sources reviewed

- ACE Ask-Offer-Ask behavior-change article: client-facing guidance should stay collaborative, factual, neutral, and end with an open invitation rather than a lecture or a defensive correction.
  - https://www.acefitness.org/resources/pros/expert-articles/9146/addressing-client-misconceptions-with-ask-offer-ask/
- WHO physical activity fact sheet: any activity is better than none, all activity counts, and muscle strengthening benefits everyone; this supports concise next actions rather than dashboard guilt.
  - https://www.who.int/news-room/fact-sheets/detail/physical-activity
- ACSM Physical Activity Guidelines resource page: keep physical activity guidance tied to recognized guideline structures and practical application, not app-only motivational copy.
  - https://acsm.org/education-resources/trending-topics-resources/physical-activity-guidelines/
- Loop 32 sources on progressive overload and RPE/RIR remained governing evidence for the actual gate: progress only after clean completion, no pain, and RPE 8 or lower.
- Hebrew/Facebook/general search: searched for Israeli trainer/social references around dashboard-style progression, RPE, and post-regression communication. Results were not stable enough to encode as source rules, so the user-facing rule used ACE behavior-change language plus the existing logged-data gate.

### Rules extracted

- Dashboard guidance must give one practical next action, not a lecture or a new questionnaire.
- If the next workout contains a substitution progression gate, the dashboard should surface that gate directly instead of generic "add a rep/load" advice.
- The dashboard action should mention the edited exercise, one-step progression, RPE 8 or lower, no pain, and tracking RPE/pain after the sets.
- Keep the signal structured so the UI/API can inspect it later, but do not introduce new storage or UI components yet.
- Use neutral Hebrew coaching language: "להתקדם שלב אחד בלבד" and "לתעד RPE וכאב" rather than pressure to return to the original exercise.

### Changes made

- Updated `backend/app/services/dashboard_service.py`:
  - `next_workout` summary now includes an optional structured `progression_gate`.
  - Dashboard `next_recommended_action` now uses the gate when present, e.g. "בשכיבת סמיכה על קיר: להתקדם שלב אחד בלבד...".
  - Kept the implementation read-only over the existing `WorkoutService.next_workout()` payload.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added a dashboard/progression-gate decision rule under `adherence_dashboard_review`.
  - Added `ACE Ask-Offer-Ask` as a source entry.
- Updated `frontend/src/api.ts`:
  - Added the optional `progression_gate` type to `DashboardState.next_workout`.
- Updated tests:
  - Added dashboard API coverage for the Hebrew push-up regression -> clean log -> dashboard progression-gate flow.
  - Extended the coaching knowledge progress-measurement test to assert the dashboard rule and source entry.

### Tests and checks

- Focused dashboard test: `1 passed`.
- Focused dashboard + knowledge tests after knowledge-center update: `2 passed`.
- Affected backend suites before knowledge-center update: `15 passed`.
- Affected backend suites after knowledge-center update and wording cleanup: `127 passed`.
- Frontend build: `npm.cmd run build` passed.
- Full backend suite: `461 passed`.

### Manual Hebrew probe

- Flow:
  - Created a current one-day beginner bodyweight weekly plan.
  - Chat request: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Logged `שכיבת סמיכה על קיר` as completed with `RPE=8`, `RIR=2`, no pain.
  - Requested `/api/dashboard`.
- Result:
  - `edit_provider_status=local_tool`
  - `edited_exercise_name=שכיבת סמיכה על קיר`
  - `dashboard_load_signal=progress_candidate`
  - `dashboard_progression_gate.exercise_name=שכיבת סמיכה על קיר`
  - `dashboard_progression_gate.action=בשכיבת סמיכה על קיר: להתקדם שלב אחד בלבד רק אם אין כאב והמאמץ נשאר עד RPE 8; לתעד RPE וכאב אחרי הסטים.`
  - `dashboard_next_recommended_action=לבצע את יום 1 גוף מלא. בשכיבת סמיכה על קיר: להתקדם שלב אחד בלבד רק אם אין כאב והמאמץ נשאר עד RPE 8; לתעד RPE וכאב אחרי הסטים.`

### Ponytail Review

- Formal Ponytail Review: Lean already. Ship.
- Net: no useful deletion found. Keeping `progression_gate` as structured API state is justified because it is directly used by the dashboard action and avoids burying product state in free text only.

### Failures and fixes

- No functional test failures in Loop 33.
- The only cleanup was a Hebrew fallback wording fix from `התרגיל שהוחלף` to `תרגיל שהוחלף`, so a missing exercise name would render as `בתרגיל שהוחלף`.

### Next research target

- Loop 34 should inspect the active workout screen and workout logging flow. The next risk is that the dashboard now explains the progression gate, but the workout execution/logging UI may still make it too easy to log against the old exercise or miss the RPE/pain tracking requirement.

## Loop 34 - 2026-06-24

### Sources reviewed

- CDC Adding Physical Activity as an Adult: adults can add activity in many ways, any amount has benefit, weekly goals should combine aerobic activity and muscle strengthening, and tracking with an activity diary supports follow-through.
  - https://www.cdc.gov/physical-activity-basics/adding-adults/index.html
- CDC Measuring Physical Activity Intensity: relative intensity can be rated on a 0-10 scale, moderate activity is around 5-6, vigorous activity starts around 7-8, and the talk test is a practical intensity check.
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- ACE Ask-Offer-Ask and the Loop 32 progressive-overload sources still govern the user-facing rule: keep guidance short, collaborative, and tied to logged evidence rather than pressure.
- Hebrew/Facebook/general search: searched for Israeli and trainer-style references around workout tracking and RPE after substitutions. Nothing stable enough to encode as a source rule was found, so the product rule stayed anchored to CDC tracking/intensity and the existing ACSM/ACE progression gate.

### Rules extracted

- A progression gate is not just text in the dashboard. The active workout/logging UI must make the tracking requirement visible at the exercise being logged.
- If an exercise is in `substitution_progression_gate`, the user must log RPE for that attempted exercise, or provide an overall RPE, before the app can treat the log as useful for progression.
- Pain tracking remains binary plus notes: if pain appears, the existing pain-note validation must still force location/context.
- Partial logs should not be blocked by a progression-gate exercise the user did not attempt. The gate applies to attempted gate work, or to a workout marked completed.
- The payload must keep logging against `source_exercise_id`, so the adjusted exercise still maps back to the saved plan object.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - Reused the normalized execution-plan exercises when validating and building the structured log payload.
  - Added a visible Hebrew hint beside progression-gate exercises: log RPE and mark pain if it appeared before deciding whether to advance one step or hold.
  - Added progression-gate validation so attempted gate work cannot be saved without exercise-level or overall RPE.
  - Corrected the validation after Ponytail Review so a partial log can save another exercise without forcing RPE for an untouched progression-gate exercise.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - Added UI coverage that a progression-gate exercise with reps but no RPE is blocked and sends no payload.
  - Added UI coverage that a partial log for a non-gate exercise is allowed when the gate exercise was not attempted.
  - Extended the fixture to include a normal second exercise, keeping the test realistic without another mock shape.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added the self-monitoring rule that a progression gate after substitution/regression needs RPE and pain status before increasing difficulty.
- Updated `backend/tests/test_coaching_knowledge.py`:
  - Added a knowledge-center assertion for the RPE/pain progression-gate rule.

### Tests and checks

- Focused backend knowledge test: `1 passed`.
- Focused frontend progression-gate test before Ponytail correction: `1 passed`.
- Affected frontend file before Ponytail correction: `15 passed`.
- Affected backend set (`test_coaching_knowledge.py`, `test_dashboard_api.py`, progression-gate workout-log test): `121 passed`.
- Frontend production build before Ponytail correction: `npm.cmd run build` passed.
- Full backend suite before the final frontend-only Ponytail correction: `461 passed`.
- Focused frontend progression-gate tests after Ponytail correction: `2 passed`.
- Full `WorkoutsPanel.test.tsx` after Ponytail correction: `16 passed`.
- Frontend production build after Ponytail correction: `npm.cmd run build` passed.
- `git diff --check`: clean; CRLF warnings only.

### Manual Hebrew probe

- Flow:
  - Created a current one-day beginner bodyweight weekly plan.
  - Chat request: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Confirmed chat used `provider_status=local_tool`.
  - Confirmed the edited exercise became `שכיבת סמיכה על קיר` and retained the "קשות מדי" edit note.
  - Logged the edited exercise as completed with `RPE=8`, `RIR=2`, no pain.
  - Requested `/api/workouts/next` and `/api/dashboard`.
- Result:
  - `next_load_signal=progress_candidate`
  - `gate_adjustment=substitution_progression_gate`
  - `gate_note_has_rpe8=True`
  - `gate_note_has_one_step=True`
  - Dashboard progression-gate action named the edited wall push-up and required one-step progression only with no pain and effort up to `RPE 8`.

### Ponytail Review

- Formal Ponytail Review found one useful simplification/correction:
  - The first validation was too broad because it required RPE for every progression-gate exercise on any non-skipped log.
  - That would block a partial log where the user only completed another exercise and did not attempt the gate exercise.
- Fix applied:
  - Require gate RPE only when the workout is marked completed or when that gate exercise has actual input.
  - Added a focused partial-log test for this edge case.
- Net: the implementation remains small and product-relevant. No new service, schema, or dashboard state was needed.

### Failures and fixes

- First manual probe exited nonzero because Windows kept the temporary SQLite file locked during cleanup, although the product assertions had already succeeded.
- Reran the probe with `TestClient` closed, dependency overrides cleared, and the SQLAlchemy engine disposed; it exited cleanly.
- No product-code fix was needed for that probe issue.

### Next research target

- Loop 35 should inspect natural-language workout logging and chat logging around progression gates. The frontend structured form now prevents missing RPE for attempted gate work, but WhatsApp/future chat-style logs may still accept "עשיתי את האימון" without enough RPE/pain detail to decide whether to advance.

## Loop 35 - 2026-06-24

### Sources reviewed

- CDC Adding Physical Activity as an Adult: tracking weekly activity is part of sticking with activity; the product should keep logs useful without turning them into a long questionnaire.
  - https://www.cdc.gov/physical-activity-basics/adding-adults/index.html
- CDC How to Measure Physical Activity Intensity: a 0-10 effort scale is a valid practical way to capture relative intensity, with moderate around 5-6 and vigorous beginning around 7-8.
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Women's Health / trainer and exercise-science expert RIR article: RIR/RPE helps account for day-to-day readiness; RPE 8 is commonly mapped near 2 RIR, but beginners may need simpler effort language first.
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- Search expansion:
  - Searched ACSM/NSCA/RPE/RIR terms, trainer-style sources, Hebrew "דירוג מאמץ/RPE", and general coach content.
  - The stable actionable rule came from CDC intensity/tracking plus the existing Helms/NASM/RPE knowledge-center rules already in the repo.

### Rules extracted

- Free-text logs must support natural Hebrew effort language such as `מאמץ 8 מתוך 10`, not only literal `RPE 8`.
- A free-text chat log that clearly refers to the active workout should attach to that workout; otherwise it cannot affect the saved plan loop.
- For progression gates after substitution/regression, absence of pain text is not the same as explicit no-pain. The bot should ask for pain status instead of assuming silence means safe.
- If a chat log targets a progression-gated workout but misses RPE or explicit pain status, save the log, but do not advance. Ask one short follow-up for the missing tracking fields.
- Generic `Log workout:` remains a standalone log unless it clearly says "the workout", "today's workout", "next workout", or names an execution-plan exercise.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - `_parse_rpe()` now recognizes Hebrew effort phrases like `מאמץ 8 מתוך 10`, `קושי 8/10`, and `דרגת מאמץ 8`.
  - The regex requires effort words near the number so ordinary rep counts are not parsed as RPE.
- Updated `backend/app/services/coach_intent_service.py`:
  - Added natural Hebrew workout-log phrases `עשיתי את האימון` and `סיימתי את האימון`.
- Updated `backend/app/services/coach_engine.py`:
  - Chat workout logs now use `WorkoutService.log_workout()` rather than bypassing validation with `parse_log()`.
  - Free-text logs link to the active next workout only when the text clearly targets it or names an execution-plan exercise.
  - Progression-gate logs missing RPE or explicit pain status now get a one-question Hebrew follow-up and keep the current version.
  - Added explicit pain-status detection for chat logs: pain signal or phrases like `בלי כאב`, `אין כאב`, `no pain`.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added a load-prescription/RPE calibration rule: save free-text logs, but do not open a progression gate until RPE and pain yes/no are known.
- Updated tests:
  - Added Hebrew natural effort parsing coverage in `backend/tests/test_workout_logs_api.py`.
  - Added route-level chat coverage for a Hebrew progression-gate completion log missing RPE/pain status.
  - Added a knowledge-center assertion for the free-text progression-gate tracking rule.

### Tests and checks

- Focused new parser test: `1 passed`.
- Focused progression-gate chat test: `1 passed`.
- Focused workout-log intent subset: `2 passed`.
- Focused knowledge-center load-prescription test after knowledge update: `1 passed`.
- Affected backend group before final Ponytail correction (`test_coach_engine.py`, `test_coach_intent_service.py`, `test_workout_logs_api.py`): `134 passed`.
- Affected backend group before final Ponytail correction (`test_coaching_knowledge.py`, `test_dashboard_api.py`, `test_workout_plans_api.py`): `149 passed`.
- Full backend before final Ponytail correction: `463 passed`.
- Focused tests after pain-status correction: `3 passed`.
- Affected backend after pain-status correction:
  - `test_coach_engine.py`, `test_coach_intent_service.py`, `test_workout_logs_api.py`: `134 passed`.
  - `test_coaching_knowledge.py`, `test_dashboard_api.py`: `120 passed`.
- Full backend after pain-status correction: `463 passed`.

### Manual Hebrew probe

- Flow:
  - Logged `עשיתי לחיצת חזה 3 סטים 10,8,7 חזרות. מאמץ 8 מתוך 10, בלי כאב.`
  - Created a current one-day beginner bodyweight weekly plan.
  - Chat edit: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Logged the edited wall push-up once with `RPE=8`, `RIR=2`, no pain, opening a `substitution_progression_gate`.
  - Chat log: `סיימתי את האימון`.
- Result:
  - Natural Hebrew effort log parsed as `rpe=8`, `pain_flag=False`.
  - Edit response stayed `provider_status=local_tool`.
  - Gate before chat was `substitution_progression_gate` for `שכיבת סמיכה על קיר`.
  - Chat log response stayed `provider_status=local_tool`.
  - Chat response contained missing `RPE` and the pain-status question `האם הופיע כאב`.
  - The chat log was saved against the active workout id, but `rpe=None`, so the bot did not advance from incomplete tracking.

### Ponytail Review

- Formal Ponytail Review found one product bug:
  - The first Loop 35 implementation asked for missing RPE, but if the user supplied RPE and did not mention pain, the bot would treat pain as absent.
  - That is unsafe for a progression gate. Silence is not no-pain.
- Fix applied:
  - Added explicit pain-status detection and included missing pain status in the progression-gate follow-up.
  - Kept it as a small helper in `coach_engine.py`; no schema, route, or persistence change.
- Net: the implementation is still lean. It reuses existing log storage, next-workout payloads, and knowledge-center protocols.

### Failures and fixes

- No test failures in Loop 35.
- Manual probe passed after the final pain-status wording update.

### Next research target

- Loop 36 should decide how much evidence a free-text active-workout log needs when the user says `סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב` but does not provide exercise-level reps. The current system saves and links that log, but progression logic still requires exercise results before treating it as progression evidence.

## Loop 36 - 2026-06-24

### Sources reviewed

- CDC How to Measure Physical Activity Intensity: session effort on a 0-10 scale is a recognized practical measure of relative intensity, but it captures whole-session effort rather than exercise-level performance.
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- CDC Adding Physical Activity as an Adult: tracking helps adherence, and the app should accept simple logs when they are enough for the next decision.
  - https://www.cdc.gov/physical-activity-basics/adding-adults/index.html
- Women's Health trainer/exercise-science RIR reference: RPE/RIR adjusts to day-to-day readiness, but beginners may need simpler effort language and exercise-level form/reps remain more informative when available.
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- Existing repo knowledge-center sources for Helms/NASM/RPE and ACSM progression remained the stronger rule base for one-step progression.

### Rules extracted

- Exercise-level reps/sets remain preferred evidence for progressing a specific exercise.
- A full-workout free-text log can be sufficient only when it clearly says the workout was completed, includes `RPE <= 8`, and explicitly says no pain.
- `RPE 8` without explicit no-pain is not enough.
- If the active workout contains a substituted/regressed exercise, a session-level clean log may open only a one-step progression gate, not an automatic return to the original hard version.
- Replaced exercise notes should surface the gate even when the latest log is workout-level and has no exercise-specific result row.

### Changes made

- Updated `backend/app/services/training_adaptation_service.py`:
  - `_latest_log_supports_progression()` now accepts completed workout-level logs with `RPE <= 8` only when the notes contain an explicit no-pain statement.
  - Added `_log_has_explicit_no_pain()` and then moved the language check into shared pain parsing after Ponytail Review.
- Updated `backend/app/services/workout_service.py`:
  - A `progress_candidate` execution plan now surfaces `substitution_progression_gate` for replaced/regressed exercises even without an exercise-specific adjustment row.
- Updated `backend/app/services/coach_engine.py`:
  - Progression-gate chat responses now distinguish:
    - missing RPE/pain status -> ask for the missing field.
    - RPE/no-pain present -> one-step gate response.
    - high RPE -> hold current version.
  - `_progression_gate_from_next_workout()` now detects edited exercise notes before the gate is formally opened.
- Updated `backend/app/services/pain_text.py`:
  - Added `has_explicit_no_pain_statement()` and `has_explicit_pain_status()` using existing negated-pain regexes.
  - Removed duplicated no-pain phrase lists from coach/adaptation services.
- Updated tests:
  - Added training-adaptation unit coverage for session-level RPE/no-pain progression evidence and RPE-without-pain-status maintain behavior.
  - Added route-level chat coverage for `סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב` opening a `substitution_progression_gate`.
  - Added a knowledge-center assertion for the session-level clean-log rule.

### Tests and checks

- First focused Loop 36 run:
  - Training-adaptation threshold tests: `2 passed`.
  - Knowledge load-prescription test: `1 passed`.
  - Chat route test failed because the response helper only recognized an already-open `substitution_progression_gate`, not an edited exercise that was about to become a gate.
- Fix:
  - `_progression_gate_from_next_workout()` now treats edited/regressed exercise notes as gate-relevant.
- Focused rerun:
  - Loop 36 focused chat/adaptation tests: `4 passed`.
  - Knowledge load-prescription test: `1 passed`.
- Affected backend before Ponytail cleanup:
  - `test_coach_engine.py`, `test_coach_intent_service.py`, `test_training_adaptation_service.py`, `test_workout_logs_api.py`: `143 passed`.
  - `test_coaching_knowledge.py`, `test_dashboard_api.py`, `test_workout_plans_api.py`: `149 passed`.
  - Full backend: `466 passed`.
- Ponytail cleanup focused checks:
  - Training-adaptation threshold tests: `2 passed`.
  - Chat progression-gate tests: `2 passed`.
  - Safety + negated-pain smoke: `12 passed`.
- Affected backend after Ponytail cleanup:
  - `test_coach_engine.py`, `test_coach_intent_service.py`, `test_training_adaptation_service.py`, `test_workout_logs_api.py`: `143 passed`.
  - `test_safety_service.py`, `test_coaching_knowledge.py`, `test_dashboard_api.py`, `test_workout_plans_api.py`: `160 passed`.
  - Full backend: `466 passed`.

### Manual Hebrew probe

- Flow:
  - Created a current one-day beginner bodyweight weekly plan.
  - Chat edit: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Chat log: `סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב`.
  - Requested `/api/workouts/next`.
- Result:
  - `edit_provider_status=local_tool`
  - edited exercise became `שכיבת סמיכה על קיר`
  - chat log stayed `provider_status=local_tool`
  - chat response contained `שלב אחד`
  - last log linked to `workout_id=1`
  - last log had `rpe=8`, `pain_flag=False`
  - next execution plan had `load_signal=progress_candidate`
  - edited exercise had `adjustment=substitution_progression_gate`
  - execution note contained `שלב אחד`

### Ponytail Review

- Formal Ponytail Review found one cleanup:
  - Explicit no-pain phrase lists were duplicated in `coach_engine.py` and `training_adaptation_service.py`.
- Fix applied:
  - Moved pain-status helpers into `backend/app/services/pain_text.py` and reused existing negated-pain regexes.
  - Kept the implementation to shared language parsing plus two small service calls.
- Net: no extra persistence or route surface added.

### Failures and fixes

- One route test failed initially because a substituted exercise is not marked `substitution_progression_gate` until after the qualifying log is saved.
- Fixed by recognizing edited/regressed exercise notes as gate-relevant in the response helper and by surfacing gates for edited exercises under `progress_candidate`.

### Next research target

- Loop 37 should inspect how active-plan edits and workout-level progression gates appear in the frontend active-plan screen and dashboard after the chat-only path. The backend now opens the gate, but the UI may still not make clear that the gate came from a session-level log rather than exercise-level reps.

## Loop 37 - 2026-06-24

### Sources reviewed

- CDC How to Measure Physical Activity Intensity: whole-session effort can be captured with practical perceived-intensity language, but it is still less specific than exercise-level reps/sets.
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- CDC Adding Physical Activity as an Adult: simple tracking is useful for adherence when the next action is clear and not overburdened by a long form.
  - https://www.cdc.gov/physical-activity-basics/adding-adults/index.html
- Existing knowledge-center rules from ACSM/NSCA/NASM/Helms stayed the governing source for conservative one-step progression after substitutions.

### Rules extracted

- A session-level Hebrew log like `סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב` can open only a conservative one-step gate.
- The active workout and dashboard must say when the evidence is a general workout log, not exercise-level reps.
- Structured exercise logs remain stronger evidence. When the user gives only session-level RPE/no-pain, the next action should ask them to track exercise reps/RPE next time.
- If exercise-result rows are malformed or non-dict values, they must not accidentally count as progression evidence.

### Changes made

- Updated `backend/app/services/training_adaptation_service.py`:
  - Added internal `progress_evidence` values:
    - `exercise_log`
    - `session_rpe_no_pain`
    - `completed_streak`
  - Fixed the empty-iterator edge case so invalid `exercise_results` cannot pass progression through `all(...)`.
- Updated `backend/app/services/workout_service.py`:
  - When a substituted/regressed exercise is gated by `session_rpe_no_pain`, the execution note now says the log was general and asks for exercise reps/RPE next time.
  - The structured-log gate note now keeps the explicit instruction to document RPE and pain after sets.
- Updated `backend/app/services/dashboard_service.py`:
  - Dashboard progression gates now reuse the execution note from the active workout instead of a generic gate sentence, so session-level evidence is visible in `next_recommended_action`.
- Updated tests:
  - Added evidence-type assertions in `test_training_adaptation_service.py`.
  - Added invalid exercise-result coverage for progression evidence.
  - Extended the chat route test to assert the active workout note says `לוג`, `כללי`, and `חזרות/RPE`.
  - Added dashboard route coverage for session-level chat logs surfacing the same gate note.

### Tests and checks

- Focused tests:
  - `python -m pytest backend/tests/test_training_adaptation_service.py`: `9 passed`.
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_workout_log_with_session_rpe_no_pain_opens_progression_gate`: `1 passed`.
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_surfaces_session_level_progression_gate_note_after_chat_log`: `1 passed`.
- Affected backend first run:
  - `test_coach_engine.py`, `test_training_adaptation_service.py`, `test_dashboard_api.py`, `test_workout_logs_api.py`, `test_coaching_knowledge.py`: `1 failed, 240 passed`.
- Fix:
  - The dashboard correctly reused `execution_note`, but the default structured gate note no longer included `לתעד RPE וכאב`.
  - Added that tracking phrase back to the shared execution note.
- Focused rerun:
  - Structured dashboard gate test: `1 passed`.
  - Session-level dashboard gate test: `1 passed`.
- Affected backend rerun:
  - `241 passed`.
- Full backend:
  - `python -m pytest backend/tests`: `468 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- First manual attempt accidentally used the configured provider from local `.env.local`, which made it invalid for deterministic local-route evidence.
- Second attempt with provider keys empty still failed because the PowerShell-to-Python stdin path corrupted Hebrew literals enough to miss local intent routing.
- Final valid probe loaded the Hebrew constants from the UTF-8 test source and forced provider keys empty.
- Flow:
  - Created a beginner bodyweight weekly plan.
  - Chat edit: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Chat log: `סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב`.
  - Requested `/api/workouts/next` and `/api/dashboard`.
- Result:
  - `edit_provider=local_tool`
  - `chat_provider=local_tool`
  - edited exercise became `שכיבת סמיכה על קיר`
  - chat response said one-step progression was enough for the gate.
  - `load_signal=progress_candidate`
  - `progress_evidence=session_rpe_no_pain`
  - active workout gate was `substitution_progression_gate`
  - execution note said the log was general and asked to track `חזרות/RPE`
  - dashboard gate action and next recommended action used the same note.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - No new UI layer, schema, persistence table, provider, or abstraction.
  - The evidence label stays internal, and the user-facing behavior reuses existing `execution_note` rendering.
  - The added tests cover cross-route behavior that unit tests alone would miss.

### Failures and fixes

- Affected backend initially failed because the dashboard switched from generic gate text to `execution_note`, exposing that the structured gate note had lost explicit RPE/pain tracking guidance.
- Fixed by keeping `לתעד RPE וכאב אחרי הסטים` in the shared structured gate note.
- Manual probe had two invalid attempts due local provider configuration and PowerShell Hebrew encoding; the final UTF-8-source probe passed.

### Next research target

- Loop 38 should audit the natural Hebrew chat response itself for session-level gates. The active workout and dashboard now disclose `לוג כללי`, but the immediate chat reply still says RPE/no-pain is enough for the gate without explicitly asking for exercise-level reps next time. The next loop should decide whether that response needs the same tracking guidance and test it without making replies longer than needed.

## Loop 38 - 2026-06-24

### Sources reviewed

- CDC How to Measure Physical Activity Intensity:
  - Relative intensity can be described on a 0-10 perceived-effort scale.
  - `7-8` maps to vigorous relative intensity, but it is still a whole-activity effort signal, not exercise-level performance.
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- CDC Adding Physical Activity as an Adult:
  - Tracking is part of staying consistent, and simple activity logs are useful when they support the next action.
  - https://www.cdc.gov/physical-activity-basics/adding-adults/index.html
- Women's Health / trainer and exercise-science RIR explanation:
  - RIR/RPE adapts load to day-to-day readiness.
  - Beginners may need simpler effort language, and set-level form/reps are more informative than general effort alone.
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- Men's Health / NASM-CPT RIR coaching reference:
  - RIR should mean reps that could still be completed with good form.
  - If a set is too easy, that informs the next load choice rather than chasing more reps blindly.
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/

### Rules extracted

- The bot can accept a simple session-level Hebrew log, but the chat reply should not imply the bot saw exercise-level reps.
- For a substituted/regressed exercise, `RPE 8 + בלי כאב` from a general log opens only a cautious one-step gate.
- The immediate reply should include the same tracking guidance as active workout/dashboard: next time, log reps/RPE for the relevant exercise.
- Keep the reply short: acknowledge, state reason, give one next action.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - Split the progression-gate response branch:
    - high RPE still holds the current version.
    - structured exercise logs keep the existing “enough for the gate” wording.
    - session-level logs now say `זה לוג כללי` and ask for `חזרות/RPE` next time.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added a `rir_rpe_calibration` rule requiring the coach to disclose when a progression gate is based only on a general log.
- Updated tests:
  - `backend/tests/test_coach_engine.py` now asserts the immediate chat response contains `לוג כללי` and `חזרות/RPE`.
  - `backend/tests/test_coaching_knowledge.py` now asserts the knowledge-center rule exists.

### Tests and checks

- Focused tests:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_workout_log_with_session_rpe_no_pain_opens_progression_gate`: `1 passed`.
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_load_prescription_protocols backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom`: `2 passed`.
- Affected backend:
  - `test_coach_engine.py`, `test_workout_logs_api.py`, `test_training_adaptation_service.py`, `test_dashboard_api.py`, `test_coaching_knowledge.py`: `241 passed`.
- Full backend:
  - `python -m pytest backend/tests`: `468 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- First manual probe was invalid because the constants index selected assertion strings instead of the Hebrew prompt/edit/log messages, causing missing-provider fallback.
- Corrected by enumerating the UTF-8 test constants and using prompt/edit/log indices `35/38/41`.
- Valid flow:
  - Created a beginner bodyweight weekly plan.
  - Chat edit: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Chat log: `סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב`.
  - Requested `/api/workouts/next`.
- Result:
  - `edit_provider=local_tool`
  - `chat_provider=local_tool`
  - chat response: `רשמתי את האימון. RPE 8 ובלי כאב פותחים שער זהיר של שלב אחד לשכיבת סמיכה על קיר. זה לוג כללי, אז באימון הבא לתעד גם חזרות/RPE לתרגיל הזה; אם זה עובר RPE 8 או מופיע כאב - לשמור.`
  - `progress_evidence=session_rpe_no_pain`
  - active execution note still says the same general-log tracking guidance.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - One branch split in existing response code.
  - One knowledge-center rule.
  - Two assertions.
  - No new route, schema, UI component, abstraction, or provider behavior.

### Failures and fixes

- No test failures.
- Manual probe failed once due wrong constant selection; corrected and passed.

### Next research target

- Loop 39 should inspect whether the structured exercise-log path now diverges from the session-level path in a useful way. Specifically: when a user logs actual exercise reps/RPE for the regressed exercise, the chat reply can be more confident than the general-log path, but it still should not overpromise a full return to the hard version. Research should focus on one-step progression after exercise-specific evidence and whether the current reply should mention the exact next progression option, not just “שלב אחד”.

## Loop 39 - 2026-06-24

### Sources reviewed

- SELF push-up modifications, reviewed with CSCS/CPT sources:
  - Push-up regressions reduce load while preserving the same movement pattern.
  - Elevated push-ups can progress by lowering the surface gradually; the higher surface is easier, lower box is harder.
  - The key coaching rule is “challenging but not overwhelming,” with form and pain-free movement first.
  - https://www.self.com/story/push-up-modifications
- CDC How to Measure Physical Activity Intensity:
  - Perceived exertion is useful, but it is still relative effort and should be interpreted with the performed movement.
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Women's Health / trainer and exercise-science RIR explanation:
  - RPE/RIR works best when connected to the set actually performed and whether the reps could be completed with good form.
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- Existing ACSM progression rule in the knowledge center:
  - Progress by one variable at a time, commonly small load/rep/variation changes, only when logs support it.

### Rules extracted

- Session-level clean logs can open a gate, but they should stay generic.
- Exercise-specific clean logs can name the next concrete variation because they include the performed exercise and reps.
- For push-up regression, the next step after wall push-up should be a harder elevated version, not a jump to the full floor push-up.
- The wording must still say `שלב אחד בלבד` so “שיפוע גבוה” is understood as the next step, not an unrestricted return.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - Added `progression_next_step` to execution-plan exercises, derived from the first alternative that differs from the current exercise.
  - Structured progression-gate execution notes now say the exact next step, e.g. `שכיבת סמיכה בשיפוע גבוה`, while keeping `שלב אחד בלבד`.
  - Fixed Hebrew free-text parsing for singular `סט` and standalone `חזרות`, so `1 סט 10 חזרות` becomes an exercise result.
- Updated `backend/app/services/coach_engine.py`:
  - Structured exercise-log gate replies now name the next step from `progression_next_step`.
  - Session-level gate replies remain general and still ask for exercise reps/RPE next time.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added the rule that exercise-specific clean logs can name the next variation, while general logs should not.
- Updated tests:
  - `test_workout_logs_api.py` now asserts the execution note and payload expose `שכיבת סמיכה בשיפוע גבוה`.
  - `test_coach_engine.py` adds a Hebrew free-text structured log route test for `1 סט 10 חזרות, RPE 8, בלי כאב`.
  - `test_coaching_knowledge.py` asserts the new knowledge rule.

### Tests and checks

- First focused run:
  - `test_next_workout_uses_progression_gate_after_clean_log_for_regressed_pushup`: failed because the new note named the variation but dropped the phrase `שלב אחד`.
  - `test_chat_workout_log_with_exercise_reps_names_next_progression_step`: failed because the parser treated `1 סט 10 חזרות` as session-level, not exercise-specific.
- Fixes:
  - Restored `שלב אחד בלבד` in the execution note.
  - Updated Hebrew parser regex to accept singular `סט` and `חזרות` without requiring a following weight.
- Focused rerun:
  - Structured next-workout gate test: `1 passed`.
  - Structured chat-log gate test: `1 passed`.
  - Knowledge plan-horizon/scoped edit test: `1 passed`.
- Affected backend:
  - `test_coach_engine.py`, `test_workout_logs_api.py`, `test_training_adaptation_service.py`, `test_dashboard_api.py`, `test_coaching_knowledge.py`: `242 passed`.
- Full backend:
  - `python -m pytest backend/tests`: `469 passed`.
- Final focused after wording alignment:
  - Structured chat-log gate test: `1 passed`.
  - Structured next-workout gate test: `1 passed`.
- Final affected backend:
  - `242 passed`.
- Final full backend:
  - `469 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- Final valid flow:
  - Created beginner bodyweight weekly plan.
  - Chat edit: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`.
  - Chat log: `תעד אימון: עשיתי שכיבת סמיכה על קיר 1 סט 10 חזרות, RPE 8, בלי כאב`.
  - Requested `/api/workouts/next`.
- Result:
  - `edit_provider=local_tool`
  - `chat_provider=local_tool`
  - chat response: `רשמתי את האימון. הלוג של שכיבת סמיכה על קיר נקי: RPE 8 ובלי כאב. הפעולה הבאה: להתקדם שלב אחד בלבד, רק לשכיבת סמיכה בשיפוע גבוה; אם זה עובר RPE 8 או מופיע כאב - לחזור לגרסה הנוכחית.`
  - saved exercise result: `exercise=שכיבת סמיכה על קיר`, `sets=1`, `reps=[10]`
  - `progression_next_step=שכיבת סמיכה בשיפוע גבוה`
  - execution note: `אם הלוג האחרון היה נקי, ללא כאב ועם RPE 8 ומטה, להתקדם שלב אחד בלבד: רק לשכיבת סמיכה בשיפוע גבוה; אחרת לשמור את הגרסה הנוכחית. לתעד RPE וכאב אחרי הסטים.`

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - `progression_next_step` is derived from existing alternatives and avoids duplicating the “first valid next variation” logic in chat.
  - The parser fix is a direct Hebrew regex correction.
  - No new database table, API route, UI component, provider flow, or planner abstraction.

### Failures and fixes

- Parser originally missed natural Hebrew singular set logging.
- Fixed narrowly without changing structured log schemas.
- Wording originally named the variation without the explicit one-step guard.
- Fixed by keeping `שלב אחד בלבד` in both active workout and chat response.

### Next research target

- Loop 40 should inspect how non-push-up substitutions use `progression_next_step`. Some alternatives are true progressions, but some are lateral substitutions for equipment or pain. The next loop should prevent naming an unsafe or lateral “next step” when the edited exercise came from pain or missing equipment, and should keep exact next-step naming only for difficulty regressions where alternatives are ordered as progression steps.

## Loop 40 - Keep Pain And Equipment Substitution Progression Generic

### Research target

Prevent the bot from naming a concrete “next harder step” after substitutions that were made for pain or missing equipment. Exact next-step naming should stay limited to difficulty regressions, where alternatives are intentionally ordered as a progression ladder.

### Sources reviewed

- Mayo Clinic - Weight training: Do's and don'ts of proper technique
  - https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/weight-training/art-20045842
- Barbell Medicine - Pain in Training: What To Do?
  - https://www.barbellmedicine.com/blog/pain-in-training-what-do/

### Findings extracted

- Mayo Clinic separates progression from pain handling: increase resistance slowly only when technique stays correct; if an exercise causes pain, stop, retry later, or use less weight.
- Barbell Medicine frames pain-related exercise changes as finding a tolerable entry point by adjusting load, range of motion, exercise selection, volume, frequency, tempo, and RPE. Progression should be conservative and symptom-guided, not an automatic return to a harder variation.
- Product rule: for “too hard” regressions, a clean exercise-level log may name the next variation. For pain or equipment substitutions, the bot should say `שלב אחד בלבד` but not name a harder/lateral alternative.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - `progression_next_step` is now set only when notes indicate a difficulty regression like `קשות מדי` / `too hard`.
  - Pain, equipment, machine, bench, and unavailable-equipment notes explicitly block named next-step progression.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Scoped plan edit rules now distinguish difficulty-regression logs from pain/equipment substitutions.
  - Added Mayo Clinic weight-training technique and Barbell Medicine pain-training references to the scoped edit source list.
- Updated tests:
  - Added next-workout API coverage proving a knee-pain squat substitution opens only a generic one-step gate after a clean log.
  - Added chat-route coverage proving the Hebrew coach response does not name `ישיבה-קימה` or use `רק ל...` after a knee-pain substitution.
  - Updated knowledge-center assertions for the new scoped edit rule and source reference.

### Tests and checks

- First failing test:
  - `test_next_workout_keeps_pain_substitution_progression_generic_after_clean_log`: failed because `progression_next_step` was `ישיבה-קימה מכיסא`.
- Focused after fix:
  - `test_next_workout_uses_progression_gate_after_clean_log_for_regressed_pushup`
  - `test_next_workout_keeps_pain_substitution_progression_generic_after_clean_log`
  - `test_chat_workout_log_with_exercise_reps_names_next_progression_step`
  - `test_chat_workout_log_after_pain_substitution_keeps_progression_generic`
  - `test_coaching_knowledge_contains_plan_horizon_protocols`
  - Result: `5 passed`.
- Affected backend:
  - `test_workout_logs_api.py`, `test_coach_engine.py`, `test_coaching_knowledge.py`, `test_training_adaptation_service.py`, `test_dashboard_api.py`
  - Result: `244 passed`.
- Full backend:
  - `python -m pytest backend/tests`
  - Result: `471 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- Flow:
  - Created beginner bodyweight weekly plan.
  - Chat edit: `כואבת לי הברך בסקוואט שבתוכנית, תחליף רק את זה`.
  - Chat log: `תעד אימון: עשיתי סקוואט לקופסה בטווח קצר 1 סט 10 חזרות, RPE 7, בלי כאב`.
  - Requested `/api/workouts/next`.
- Result:
  - edit response kept the plan edit scoped to knee pain and said to work in a pain-free range at RPE 5-7.
  - log response: `רשמתי את האימון. RPE 7 ובלי כאב מספיקים לשער ההתקדמות של סקוואט לקופסה בטווח קצר. הפעולה הבאה: להתקדם שלב אחד בלבד, ואם זה עובר RPE 8 או מופיע כאב - לשמור את הגרסה הנוכחית.`
  - `progression_next_step=None`.
  - execution note is generic and does not include `רק ל...`.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - The implementation is a small predicate over existing edit notes.
  - No new schema, API, provider, planner, or UI layer was added.
  - Tests cover the two product branches: exact named progression for difficulty regression, generic progression gate for pain substitution.

### Failures and fixes

- The first manual probe exited nonzero because the temporary SQLite file remained locked during cleanup, even though the printed behavior was correct.
- Reran the same probe with ignored cleanup errors for the ephemeral temp directory; the verification exited cleanly.

### Next research target

- Loop 41 should inspect equipment-substitution cases specifically, especially no-bench and row-machine-unavailable edits. The goal is to verify they also stay generic after clean logs, and to decide whether equipment substitutions should ever name a next step or should only ask for available equipment before progressing.

## Loop 41 - Verify Equipment Substitutions Do Not Name A Next Progression Step

### Research target

Check whether equipment substitutions, especially row-machine-unavailable and no-bench edits, should ever name a concrete next step after a clean log.

### Sources reviewed

- ACE Exercise Library
  - https://www.acefitness.org/resources/everyone/exercise-library/
- Runner's World - Your Strength-Training Starter Pack: Expert-Approved Equipment Picks
  - https://www.runnersworld.com/training/a71693898/strength-training-equipment-runners/
- Existing knowledge-center references retained:
  - NSCA Guide to Program Design
  - HPRC/NSCA Exercise Selection

### Findings extracted

- ACE organizes exercise choice by body part, experience level, and equipment, which supports treating equipment availability as a selection/filtering constraint.
- Runner's World trainer guidance frames dumbbells, bands, boxes, and benches as tools that affect access, stability, and load options. Different tools enable different exercises and progressions, but missing equipment is not by itself proof that the user should return to a harder or different variation.
- Product rule: after equipment substitutions, the bot can open a generic one-step gate from a clean log, but it should not name an equipment-dependent or lateral alternative unless the user confirms the equipment is available and logs the relevant exercise.

### Changes made

- Updated `backend/app/services/coaching_knowledge.py`:
  - Added `ACE Exercise Library Equipment Filters` and `Runner's World Strength Equipment Coach Reference` to scoped plan edit source refs.
  - Added `Runner's World Strength Equipment Coach Reference` to the central source registry.
- Updated tests:
  - Added `test_chat_workout_log_after_row_machine_substitution_keeps_progression_generic`.
  - Updated `test_coaching_knowledge_contains_plan_horizon_protocols` to assert the equipment-specific source refs and source registry entry.

### Tests and checks

- First focused equipment test:
  - Failed with `StopIteration` because the fixture used a four-day plan; after completing the first workout, `/api/workouts/next` advanced to a different day, so the edited row was no longer in the next execution plan.
- Fix:
  - Kept the existing row-machine edit test as a four-day coverage case.
  - Changed only the progression-gate regression test to a one-day gym plan.
- Focused rerun:
  - `test_chat_workout_log_after_row_machine_substitution_keeps_progression_generic`
  - `test_chat_workout_log_after_pain_substitution_keeps_progression_generic`
  - `test_chat_workout_log_with_exercise_reps_names_next_progression_step`
  - `test_coaching_knowledge_contains_plan_horizon_protocols`
  - Result: `4 passed`.
- Affected backend:
  - `test_coach_engine.py`, `test_coaching_knowledge.py`, `test_workout_logs_api.py`, `test_training_adaptation_service.py`, `test_dashboard_api.py`
  - Result: `245 passed`.
- Full backend:
  - `python -m pytest backend/tests`
  - Result: `472 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- Flow:
  - Created one-day intermediate gym plan.
  - Chat edit: `אין לי מכונה לחתירה בתוכנית, תחליף רק את זה`.
  - Chat log: `תעד אימון: עשיתי חתירת משקולת יד בתמיכה 3 סטים 10,10,9 חזרות, RPE 7, בלי כאב`.
  - Requested `/api/workouts/next`.
- Result:
  - edit response: `עדכנתי רק את תרגילי החתירה שדרשו מכונה בלי לבנות תוכנית חדשה: החלפתי 1 תרגילים/חלופות. הפעולה הבאה: לבצע חתירה חופשית/כבל בטכניקה נשלטת ולתעד RPE.`
  - log response: `רשמתי את האימון. RPE 7 ובלי כאב מספיקים לשער ההתקדמות של חתירת משקולת יד בתמיכה. הפעולה הבאה: להתקדם שלב אחד בלבד, ואם זה עובר RPE 8 או מופיע כאב - לשמור את הגרסה הנוכחית.`
  - `progression_next_step=None`.
  - execution note is generic and does not include `רק ל...` or `חתירה בכבל`.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - No new service logic was needed; Loop 40's existing note predicate already handled equipment markers.
  - The new test locks a real equipment flow without adding fixtures or abstractions beyond the existing chat test pattern.
  - Knowledge changes are two source refs plus one source registry entry.

### Failures and fixes

- The only failure was a test-fixture issue: multi-day plan advancement hid the edited row from the next execution plan.
- Fixed by using a one-day gym plan only in the progression-gate test.

### Next research target

- Loop 42 should inspect no-bench edits and floor-press/hip-thrust substitutions. Decide whether the current `ציוד חסר` note is enough, and verify a clean log after no-bench substitution also keeps progression generic without naming a bench-based or incline alternative.

## Loop 42 - Verify No-Bench Substitutions Stay Generic After Clean Logs

### Research target

Verify no-bench edits, especially floor-press substitutions and bench-based alternatives, do not create named progression steps after a clean log.

### Sources reviewed

- ACE Exercise Library
  - https://www.acefitness.org/resources/everyone/exercise-library/
- Runner's World - Your Strength-Training Starter Pack: Expert-Approved Equipment Picks
  - https://www.runnersworld.com/training/a71693898/strength-training-equipment-runners/
- Mayo Clinic - Weight training technique and pain/form guardrails
  - https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/weight-training/art-20045842

### Findings extracted

- Bench availability changes exercise setup and stability. It should be treated as an equipment/access constraint, not a readiness signal.
- Runner's World trainer guidance notes benches can provide stable surfaces and adjustable positions, while floor presses are a usable exercise option. That supports substituting to floor press when no bench exists, but not automatically naming a bench-based next step.
- Product rule: after no-bench edits, the bot should keep a generic progression gate and require RPE/pain tracking; it should not name a bench or incline alternative unless bench availability is restored.

### Changes made

- Updated tests only:
  - Added `test_chat_workout_log_after_no_bench_substitution_keeps_progression_generic`.
  - The test creates a one-day dumbbell+bench plan, applies the Hebrew no-bench scoped edit, logs floor press in Hebrew, and verifies:
    - bench alternatives were removed,
    - the edited exercise contains `ציוד חסר`,
    - the chat response says `שלב אחד` but does not say `רק ל...` or `ספסל`,
    - the next execution plan has `progression_next_step=None`.

### Tests and checks

- Focused:
  - `test_chat_workout_log_after_no_bench_substitution_keeps_progression_generic`
  - `test_chat_workout_log_after_row_machine_substitution_keeps_progression_generic`
  - `test_chat_workout_log_after_pain_substitution_keeps_progression_generic`
  - `test_chat_workout_log_with_exercise_reps_names_next_progression_step`
  - Result: `4 passed`.
- Affected broad attempt:
  - First run of affected backend: `245 passed`, `1 failed`.
  - Failure was `WinError 10055` while AnyIO/TestClient tried to create a new Windows event loop socket, not an assertion failure.
  - Rerunning the failed dashboard test alone with workspace-local `--basetemp`: `1 passed`.
  - Second affected run with `--basetemp`: `245 passed`, `1 failed`.
  - Failure was again `WinError 10055`, this time in `test_chat_workout_log_with_session_rpe_no_pain_opens_progression_gate`.
  - Rerunning that test with the new no-bench test as a small focused chunk: `2 passed`.
- Full backend:
  - Not rerun after Loop 42 because the machine was already hitting Windows socket-buffer exhaustion from many live Python server processes.
  - Last full backend immediately before this test-only loop: `472 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- Flow:
  - Created one-day dumbbell+bench plan.
  - Chat edit: `אין לי ספסל בתוכנית, תחליף רק את מה שצריך`.
  - Chat log: `תעד אימון: עשיתי לחיצת רצפה עם משקולות 3 סטים 10,10,9 חזרות, RPE 7, בלי כאב`.
  - Requested `/api/workouts/next`.
- Result:
  - edit response: `עדכנתי את התוכנית הפעילה בלי לבנות חדשה: הסרתי שימוש בספסל ועדכנתי 3 תרגילים/חלופות. הפעולה הבאה: באימון הקרוב לבצע את הגרסאות בלי ספסל ולתעד RPE/כאב.`
  - log response: `רשמתי את האימון. RPE 7 ובלי כאב מספיקים לשער ההתקדמות של לחיצת רצפה עם משקולות. הפעולה הבאה: להתקדם שלב אחד בלבד, ואם זה עובר RPE 8 או מופיע כאב - לשמור את הגרסה הנוכחית.`
  - edited alternatives: `['לחיצת רצפה עם משקולות']`.
  - `progression_next_step=None`.
  - execution note is generic and does not include `רק ל...` or `ספסל`.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - This loop added one regression test and no new service logic.
  - The existing `ציוד חסר` predicate already blocks named next-step progression.
  - No fixtures, abstractions, schemas, routes, or UI work were added.

### Failures and fixes

- Broad pytest runs are currently limited by Windows socket-buffer exhaustion, likely aggravated by multiple live Python `uvicorn`/`http.server` processes on the machine.
- I did not kill those processes because they may be user-owned live servers.
- Verification was kept to focused tests plus manual probes, with the limitation logged explicitly.

### Next research target

- Loop 43 should return to the main workout-plan builder and inspect whether single-workout, weekly, two-week, and monthly plan outputs all expose horizon-specific progression/tracking language in Hebrew. The next useful slice is not another substitution edge case; it is verifying that each plan horizon says exactly how to log and progress without turning into a generic “program” response.

## Loop 43 - Add End-Of-Block Tracking To Two-Week Plans

### Research target

Audit horizon-specific plan output: single workout, weekly plan, two-week plan, and monthly plan should each tell the user what to log and how to decide the next step without sounding like a generic program.

### Sources reviewed

- Existing builder sources:
  - ACSM resistance training progression references
  - CDC adult physical activity and intensity/tracking guidance
  - NSCA resistance training frequency and exercise-order references
- Additional current web research:
  - Runner's World beginner base-building/RPE discussion surfaced the practical coaching pattern: use RPE to teach pacing and avoid overloading beginners before harder work.

### Findings extracted

- The builder already separates plan horizons structurally: `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan`.
- Single-workout, weekly, and monthly tracking language was specific enough.
- Two-week tracking had a real gap: it said how to use Week 1 to decide Week 2, but it did not tell the user what to summarize at the end of Week 2 before repeating, progressing, or replacing the block.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - Two-week `tracking_guidance` now says to summarize completed work, pain, and what to keep/change at the end of Week 2 before another block.
- Updated `backend/app/services/coaching_knowledge.py`:
  - `tracking_guidance_policy` now explicitly includes a Week 2 end-of-block summary.
- Updated tests:
  - `test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons` now asserts `בסוף שבוע 2` and `בלוק נוסף` in two-week tracking guidance.
  - `test_coaching_knowledge_contains_plan_horizon_protocols` now asserts the knowledge policy includes `סוף שבוע 2`.

### Tests and checks

- Focused:
  - `test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons`
  - `test_coaching_knowledge_contains_plan_horizon_protocols`
  - `test_single_session_plan_is_saved_without_replacing_current_multi_week_plan`
  - Result: `3 passed`.
- Affected small suite:
  - `test_workout_plan_builder.py`
  - `test_workout_plans_api.py`
  - `test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols`
  - Result: `35 passed`.
- Full backend:
  - Not rerun in this loop because the machine is still under Windows TestClient/socket pressure. Last full backend before the later test-only loops was `472 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- Flow:
  - Used Hebrew prompt from the horizon test: `תבנה לי תוכנית לשבועיים עם משקולות`.
  - Generated a two-week plan after onboarding.
- Result:
  - `PLAN_TYPE=two_week_plan`
  - `DURATION_WEEKS=2`
  - progression schedule:
    - `שבוע 1: ללמוד את התנועות עם RPE 5-7 ולתעד כאב, RIR ומה הושלם.`
    - `שבוע 2: אם שבוע 1 היה יציב, להוסיף חזרה נקייה אחת בכל סט או לשמור; אם לא יציב, לא להתקדם ולא להוסיף סטים עדיין.`
  - tracking guidance now includes:
    - `אחרי שבוע 1 להתקדם בשבוע 2 רק אם RPE, כאב והשלמות אימון יציבים; בסוף שבוע 2 לסכם מה הושלם, מה כאב, ומה לשמר או לשנות לפני בלוק נוסף.`
- Note:
  - A direct inline Hebrew assertion in the manual script failed due PowerShell stdin encoding, while the printed payload was correct and the pytest assertion covered the exact Hebrew string. The manual probe was rerun output-only and exited cleanly.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - One sentence was added to an existing horizon branch.
  - Two existing tests were strengthened.
  - No new planner abstraction, schema, route, UI state, or service was added.

### Failures and fixes

- No app/test assertion failed.
- Manual probe had one encoding-only assertion issue; rerun cleanly without relying on inline Hebrew literals.

### Next research target

- Loop 44 should inspect whether the actual chat response after creating each plan horizon summarizes the horizon correctly in Hebrew, not only the stored plan payload. The stored object now has strong horizon guidance; the next risk is that the coach reply might still collapse them into generic text.

## Loop 44 - Surface Plan Horizon In Hebrew Chat Responses

### Research target

Verify that the actual coach response after creating a workout plan clearly distinguishes:

- single workout
- weekly plan
- two-week plan
- monthly plan

The stored plan object already had horizon-specific progression/tracking guidance. The risk was that the chat layer still collapsed all persistent plans into generic "תוכנית אימון מוכנה" language.

### Sources reviewed

- CDC, "How to Measure Physical Activity Intensity" (2025):
  - Relative intensity should be interpreted per person, not as one absolute load.
  - A 0-10 effort scale is a practical way to discuss intensity.
  - The talk test is a simple user-facing way to communicate moderate/vigorous effort.
- Existing knowledge-center source refs already backing the builder:
  - ACSM resistance training progression references
  - CDC adult physical activity and intensity/tracking guidance
  - NSCA resistance training frequency and exercise-order references

### Findings extracted

- The builder already produces the correct horizon-specific stored data:
  - `weekly_plan` has end-of-week consistency review.
  - `two_week_plan` has Week 1 to Week 2 progression plus an end-of-Week-2 summary.
  - `monthly_plan` has weekly review before changing volume/load.
- The chat response is part of the product contract. If it only says "plan ready", the user may not understand whether the plan is a one-off session, a week, a two-week block, or a monthly block.
- The chat layer should reuse `tracking_guidance` from the saved plan instead of inventing a second progression policy.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - Added `_plan_horizon_text(serialized)` to pull the horizon-specific tracking sentence from saved `tracking_guidance`.
  - Included horizon text in normal saved-plan responses.
  - Included horizon text in replacement-candidate responses.
  - Included horizon text when a pending replacement plan is activated.
- Updated `backend/tests/test_coach_engine.py`:
  - Weekly Hebrew plan response now must include `תוכנית שבועית` and `בסוף השבוע`.
  - Monthly Hebrew plan response now must include `תוכנית חודשית` and `בסוף כל שבוע`.
  - Added a two-week Hebrew chat test requiring `תוכנית לשבועיים`, `שבוע 1`, `שבוע 2`, `בסוף שבוע 2`, and `בלוק נוסף`.

### Tests and checks

- Focused chat horizon suite:
  - `single_session_workout_plan_without_replacing_current`
  - `natural_hebrew_weekly_plan_without_workout_word`
  - `natural_hebrew_monthly_plan_without_workout_word`
  - `two_week_horizon_in_response`
  - `spacing_for_four_day_beginner_hebrew_plan`
  - Result after final simplification: `5 passed`.
- Policy/source-of-truth checks:
  - `test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons`
  - `test_coaching_knowledge_contains_plan_horizon_protocols`
  - Result after final simplification: `2 passed`.
- Full chat-engine test file:
  - `backend/tests/test_coach_engine.py`
  - Result after final simplification: `96 passed`.
- Full backend suite:
  - Not rerun in this loop because the machine is still under Windows TestClient/socket pressure from prior loops. The last full backend pass before the later socket-heavy test-only loops was `472 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual Hebrew probe

- Method:
  - Loaded Hebrew prompts from the UTF-8 test source file to avoid PowerShell stdin corruption.
  - Ran single, weekly, two-week, and monthly chat messages through `/api/chat`.
- Result:
  - Single workout response:
    - `אימון יחיד מוכן`
    - `זה אימון חד-פעמי ולא מחליף את התוכנית הפעילה`
    - `לתעד RPE/כאב בסוף`
  - Weekly response:
    - `תוכנית שבועית`
    - `בסוף השבוע לבדוק כמה אימונים הושלמו`
  - Two-week response:
    - `תוכנית לשבועיים`
    - `אחרי שבוע 1 להתקדם בשבוע 2 רק אם RPE, כאב והשלמות אימון יציבים`
    - `בסוף שבוע 2 לסכם... לפני בלוק נוסף`
  - Monthly response:
    - `תוכנית חודשית`
    - `בסוף כל שבוע לבדוק השלמות, RPE, כאב ושינה לפני שינוי נפח או עומס`
- Note:
  - The two-week/monthly manual probes became replacement candidates because the weekly probe created an active plan first. That is expected product behavior, and the replacement-candidate copy now also includes the horizon text.

### Ponytail Review

- Finding applied:
  - `backend/app/services/coach_engine.py:L711`: shrink: duplicate plan-type Hebrew label map. Use `_natural_plan_name(plan_type)` as the existing label source.
  - net: -5 lines possible.
- Post-fix result:
  - Lean already. Ship.

### Failures and fixes

- First manual probe failed before hitting the app because the test helper received `tmp_path=None`.
  - Fixed by using a workspace temp directory.
- Second manual probe hit the app with corrupted Hebrew literals due PowerShell stdin encoding.
  - Fixed by loading prompts from the UTF-8 test source file.
- No app assertion failed after the final code change.

### Next research target

- Loop 45 should inspect the UI/workout-plan display path. The backend now stores and says the correct horizon, but the product is still incomplete if the frontend hides `plan_type`, `progression_schedule`, or `tracking_guidance` behind a generic plan card.

## Loop 45 - Show Plan Horizon And Tracking In The Workout UI

### Research target

Inspect the frontend workout-plan display path to verify that the user can actually see the distinction between a single workout, weekly plan, two-week plan, and monthly plan after the backend stores it.

### Sources reviewed

- Existing source-backed builder and knowledge-center rules from prior loops:
  - plan horizon controls what the user should log and when progression is allowed.
  - RPE/pain/completion tracking is not optional metadata; it is the feedback loop for the next plan decision.
- CDC intensity guidance reviewed in Loop 44:
  - RPE and relative intensity are practical user-facing tools, so UI should expose tracking guidance instead of hiding it in raw data.

### Findings extracted

- `frontend/src/api.ts` already carries `plan_type`, `duration_weeks`, `progression_schedule`, and `tracking_guidance`.
- `frontend/src/WorkoutsPanel.tsx` already renders `progression_schedule` and `tracking_guidance` when present.
- The real UI gap was in the summary row:
  - persistent plans did not show the horizon length, only session minutes when available.
  - a monthly plan could therefore look like just a generic plan plus `תוכנית חודשית`, without `4 שבועות`.
- The existing tests did not assert that the stored progression/tracking guidance is visible in the current-plan UI.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - `formatPlanDuration()` now keeps single workouts as minutes-only.
  - Persistent plans now show horizon length:
    - `שבוע אחד`
    - `שבועיים`
    - `4 שבועות`
  - When session duration exists, persistent plans show it as `X שבועות, Y דקות לאימון`.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - The persisted current-plan fixture now uses canonical `monthly_plan`, `duration_weeks: 4`, and `session_length_minutes: 45`.
  - The test now asserts:
    - `תוכנית חודשית`
    - `4 שבועות, 45 דקות לאימון`
    - `התקדמות לפי שבוע`
    - Week 4 progression text
    - `מה לתעד`
    - end-of-week RPE/pain/sleep tracking guidance

### Tests and checks

- Focused frontend test:
  - `npm.cmd --prefix frontend test -- --run src/WorkoutsPanel.test.tsx`
  - Result: `16 passed`.
- Frontend production build:
  - `npm.cmd run build`
  - Result: passed; Vite produced the production bundle.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- This loop did not need a new Hebrew chat probe because it changed the plan display UI, not chat routing.
- The visible UI behavior is covered by the React test:
  - current persisted monthly plan renders horizon label, horizon length, progression schedule, and tracking guidance.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - No new UI state, route, API field, schema, or component was added.
  - The one helper `formatDurationWeeks()` is a small Hebrew pluralization boundary and avoids denser inline conditional text.

### Failures and fixes

- No test/build failures in this loop.

### Next research target

- Loop 46 should inspect whether the dashboard/current-goal surface uses the canonical plan horizon. The workout tab now exposes horizon and guidance, but the dashboard may still summarize the active plan as a generic name only.

## Loop 46 - Surface Plan Horizon On The Dashboard

### Research target

Check whether the dashboard/current-goal surface uses the canonical plan horizon or still reduces the active plan to a generic name.

### Sources reviewed

- Existing product principle:
  - the dashboard should make progress and the active plan visible without overwhelming the user.
- Existing workout-plan builder rules:
  - plan horizon changes what the user should expect next: one workout, one week, two-week block, or monthly block.
- Prior Loop 44/45 finding:
  - hiding horizon details in any primary surface makes the product feel like a generic plan generator instead of a coaching system.

### Findings extracted

- Backend `DashboardService` already returns `current_workout_plan` using `WorkoutService.serialize_plan(plan)`, so the dashboard API has the full plan object.
- Frontend `DashboardState` incorrectly typed `current_workout_plan` as `{ name } | null`, which hid the available plan horizon fields from the UI code.
- `DashboardPanel` rendered only the plan name in the header, so a monthly plan could appear as just `3-Day Build Muscle Plan` with no `תוכנית חודשית`, `4 שבועות`, or session-duration context.

### Changes made

- Updated `frontend/src/api.ts`:
  - `DashboardState.current_workout_plan` is now typed as `WorkoutPlan | null`.
- Updated `frontend/src/DashboardPanel.tsx`:
  - Dashboard header now renders a compact current-plan summary:
    - plan name
    - plan type label
    - horizon length
    - session length when available
- Added `frontend/src/planFormatters.ts`:
  - Shared plan-horizon label and duration formatting across dashboard and workout panel.
- Updated `frontend/src/WorkoutsPanel.tsx`:
  - Reused the shared plan formatter instead of keeping a separate local map.
- Updated `frontend/src/DashboardPanel.test.tsx`:
  - The dashboard fixture now includes a canonical `monthly_plan`, `duration_weeks: 4`, and `session_length_minutes: 45`.
  - Test asserts the dashboard shows `תוכנית חודשית`, `4 שבועות`, and `45 דקות לאימון`, and does not leak `monthly_plan`.

### Tests and checks

- Focused dashboard test:
  - `npm.cmd --prefix frontend test -- --run src/DashboardPanel.test.tsx`
  - Result before formatter extraction: `3 passed`.
- Focused frontend panel tests after formatter extraction:
  - `npm.cmd --prefix frontend test -- --run src/DashboardPanel.test.tsx src/WorkoutsPanel.test.tsx`
  - Result: `19 passed`.
- Frontend production build:
  - `npm.cmd run build`
  - Result: passed after the shared formatter extraction.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- No new Hebrew chat probe was needed because this loop changed dashboard rendering, not chat routing.
- The visible dashboard behavior is covered by the React test:
  - `3-Day Build Muscle Plan | תוכנית חודשית | 4 שבועות | 45 דקות לאימון`
  - raw internal value `monthly_plan` is not shown.

### Ponytail Review

- Finding applied:
  - `frontend/src/DashboardPanel.tsx` and `frontend/src/WorkoutsPanel.tsx`: shrink/delete duplicate plan-horizon label formatting. Replace both local maps with shared `frontend/src/planFormatters.ts`.
- Post-fix result:
  - Lean already. Ship.
- Reason:
  - Plan-horizon labels are now used in two visible UI surfaces, so one shared formatter is smaller and less error-prone than duplicated maps.

### Failures and fixes

- No test/build failures in this loop.

### Next research target

- Loop 47 should inspect whether the plan generation request UI makes the four horizons easy to ask for in natural Hebrew without adding a long questionnaire. The backend can infer horizons, but the product may need lightweight prompt examples or controls that steer users toward single workout, weekly, two-week, or monthly requests.

## Loop 47 - Add Natural Hebrew Horizon Shortcuts To Plan Requests

### Research target

Inspect whether the plan-generation request UI helps users ask for the four canonical workout horizons without turning the form into a questionnaire.

### Sources reviewed

- Existing product principle:
  - the bot should ask only for missing critical info, infer safely, and avoid long questionnaires.
- Existing intent/builder behavior:
  - backend already infers `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan` from natural Hebrew text.
- Prior UI loops:
  - plan horizon is now visible in the workout tab and dashboard, so the request surface should also make those horizons easy to express.

### Findings extracted

- The workout-plan form had one generic textarea placeholder.
- A user could ask naturally for each horizon, but the UI did not make the four options discoverable.
- Adding a new API parameter would be premature and would duplicate existing intent parsing.
- The smallest useful UX slice is shortcut buttons that fill the textarea with natural Hebrew prompts, then send the same `{ prompt }` payload as before.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - Added four prompt shortcuts:
    - `אימון יחיד`
    - `שבוע`
    - `שבועיים`
    - `חודש`
  - Each shortcut only fills the textarea with a natural Hebrew request.
  - No hidden state and no new backend contract were added.
- Updated `frontend/src/styles.css`:
  - Added compact wrapping layout for the shortcut row.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - Added a test proving the `שבועיים` shortcut fills the Hebrew prompt and submits the same `{ prompt }` payload to `/api/workout-plans`.
  - Tightened existing text queries so shortcut labels do not collide with rendered plan labels.

### Tests and checks

- First focused run:
  - `npm.cmd --prefix frontend test -- --run src/WorkoutsPanel.test.tsx`
  - Result: failed due test-query collisions between shortcut labels and rendered plan labels.
- Fix:
  - Scoped assertions to `.plan-view` where needed.
- Final focused run:
  - `npm.cmd --prefix frontend test -- --run src/WorkoutsPanel.test.tsx`
  - Result: `17 passed`.
- Frontend production build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Covered by the React test:
  - clicking `שבועיים` fills `תבנה לי תוכנית לשבועיים עם התקדמות זהירה לפי RPE וכאב.`
  - submitting sends exactly that prompt to the existing workout-plan API.
  - returned two-week plan displays `תוכנית לשבועיים` and `שבועיים, 40 דקות לאימון`.

### Ponytail Review

- Formal Ponytail Review result:
  - Lean already. Ship.
- Reason:
  - The change avoids a new API field, modal, wizard, plan-horizon state machine, or duplicated backend logic.
  - Buttons are static prompt templates and rely on the existing intent/builder path.

### Failures and fixes

- Two UI tests initially failed because shortcut labels duplicated visible plan labels:
  - `תוכנית לשבועיים`
  - `אימון יחיד`
- Fixed by scoping assertions to the rendered `.plan-view`.
- No build failures.

### Next research target

- Loop 48 should inspect whether the workout-plan API responses and frontend fixtures still use legacy `multi_week` or `single_session` in ways that could confuse the canonical four-horizon system. Keep compatibility only where needed, but do not let legacy labels drive new behavior.

## Loop 48 - Normalize Legacy Plan-Type Fixtures And Internal Focus Keys

### Research target

Audit old `multi_week` and `single_session` usage to make sure legacy values remain compatibility aliases only, not the vocabulary driving new behavior.

### Sources reviewed

- Existing canonical plan-type model:
  - `single_workout`
  - `weekly_plan`
  - `two_week_plan`
  - `monthly_plan`
- Existing alias behavior:
  - `single_session` should normalize to `single_workout`.
  - `multi_week` should infer a canonical persistent horizon, usually `monthly_plan` when the prompt gives no narrower horizon.

### Findings extracted

- Backend schema still accepts `multi_week` and `single_session`; this is acceptable for backward compatibility.
- Builder tests explicitly cover the alias normalization; this should stay.
- Several ordinary fixtures still used legacy values:
  - context builder fixture used `multi_week`
  - token optimization fixture used `multi_week`
  - workout logs test used `single_session`
  - frontend fixtures used `single_session` and `multi_week`
- The builder also used `single_session` as an internal focus/split key for new single-workout plans. That was not just compatibility and could leak into saved day JSON.

### Changes made

- Updated stale fixtures:
  - `backend/tests/test_context_builder.py`: `multi_week` -> `monthly_plan`
  - `backend/tests/test_token_optimization.py`: `multi_week` -> `monthly_plan`
  - `backend/tests/test_workout_logs_api.py`: `single_session` -> `single_workout`
  - `frontend/src/WorkoutsPanel.test.tsx`: `single_session` -> `single_workout`, `multi_week` -> `monthly_plan`
- Renamed non-compatibility tests to canonical language:
  - chat replacement monthly plan test
  - chat single-workout tests
  - workout-plan API single-workout tests
- Kept explicit compatibility tests:
  - `test_infer_plan_type_keeps_old_aliases_compatible`
  - `test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan`
- Updated `backend/app/services/workout_plan_builder.py`:
  - internal split/focus for one-off workouts is now `single_workout`, not `single_session`.
  - `_focus_label_he()` now labels `single_workout`.
- Updated single-workout API tests:
  - assert generated day `focus` is `single_workout`.

### Tests and checks

- Focused workout-plan/backend suite:
  - `test_workout_plan_builder.py`
  - single-workout API tests
  - next-workout single-workout current-plan test
  - Result: `10 passed`.
- Context/token suite:
  - `test_context_builder_includes_current_workout_plan_metadata`
  - `test_token_optimization.py`
  - Result: `5 passed`.
- Single-workout API rerun after adding focus assertions:
  - Result: `4 passed`.
- Frontend workout panel tests:
  - `npm.cmd --prefix frontend test -- --run src/WorkoutsPanel.test.tsx`
  - Result: `17 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- No new browser/manual chat probe was needed; this loop was primarily fixture and internal-key hygiene.
- The API-level tests now prove a new single workout serializes canonical `plan_type: single_workout` and day `focus: single_workout`.

### Ponytail Review

- Finding applied:
  - `backend/app/services/workout_plan_builder.py`: delete legacy `single_session` as an internal split/focus key for newly generated plans. Replace with `single_workout`.
- Post-fix result:
  - Lean already. Ship.
- Reason:
  - Legacy values remain only where they are explicit compatibility aliases.
  - No migration, route, or extra translation layer was added.

### Failures and fixes

- No test failures in this loop.

### Next research target

- Loop 49 should inspect whether saved plan context sent to the AI/provider uses canonical horizon and tracking fields compactly. The plan object is now cleaner, but the context builder/provider compaction path must not drop `plan_type`, `duration_weeks`, progression schedule, or tracking guidance when workout-plan context is relevant.

## Loop 49 - Keep Plan Horizon In Compact Provider Context

### Research target

Verify that saved workout-plan horizon and tracking fields survive the path:

`WorkoutPlan` -> `ContextBuilder` -> optimized provider payload.

### Sources reviewed

- Existing token-efficiency product rule:
  - optimize prompt/context size without dropping information that changes coaching behavior.
- Existing workout-plan horizon rules:
  - `plan_type`, `duration_weeks`, progression schedule, and tracking guidance define how the coach should adapt future advice.

### Findings extracted

- `ContextBuilder._plan()` already included:
  - `plan_type`
  - `duration_weeks`
  - `progression_schedule`
  - `tracking_guidance`
- `compact_provider_context()` kept compact plan identity fields:
  - type
  - weeks
  - days per week
  - split
  - minutes
  - equipment
- But it dropped `progression_schedule` and `tracking_guidance`.
- That means configured-provider chat could know the active plan is monthly, but lose the actual weekly progression/tracking rules that make the plan coachable.

### Changes made

- Updated `backend/app/services/token_budgeting.py`:
  - Added bounded plan list compaction for:
    - `progression_schedule`
    - `tracking_guidance`
  - Added `_compact_workout_plan()` so list handling stays plan-specific instead of making `_pick()` a generic list compactor.
- Updated `backend/tests/test_token_optimization.py`:
  - Token optimization fixture now includes monthly progression schedule and tracking guidance.
  - Test now asserts optimized provider payload keeps:
    - `type: monthly_plan`
    - `weeks: 4`
    - `progression_schedule` containing Week 2 guidance
    - `tracking_guidance` containing end-of-week review guidance
  - The test still enforces the 50% input-token reduction target.

### Tests and checks

- Focused provider/context test:
  - `python -m pytest backend/tests/test_token_optimization.py backend/tests/test_context_builder.py::test_context_builder_includes_current_workout_plan_metadata`
  - Result before Ponytail simplification: `5 passed`.
- Same test after Ponytail simplification:
  - Result: `5 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- No live provider call was needed. The test reads the actual optimized provider `input_text` and verifies the compact JSON payload.
- This is stronger than checking only `ContextBuilder`, because it confirms the final payload sent to the model keeps the plan horizon rules.

### Ponytail Review

- Finding applied:
  - `backend/app/services/token_budgeting.py`: shrink/yagni: generic `lists` parameter on `_pick()` for one use. Replace with `_compact_workout_plan()` and keep list compaction scoped to workout-plan context.
- Post-fix result:
  - Lean already. Ship.

### Failures and fixes

- Initial patch missed the `_pick()` signature update after adding `lists`.
  - Fixed immediately before running tests.
- No test failures after the corrected implementation.

### Next research target

- Loop 50 should inspect whether workout-plan generation and chat responses include enough source-backed safety/progression knowledge for endurance and mobility goals, not only strength/hypertrophy. The four horizons now carry through storage, UI, dashboard, and provider context; the next weak area may be goal-specific content breadth.

## Loop 50 - Make Endurance And Mobility Plans Goal-Specific

### Research target

Check whether endurance and mobility plan generation is truly goal-specific, or just a normal strength plan with lighter reps/rest.

### Sources reviewed

- [CDC adult physical activity guidelines](https://www.cdc.gov/physical-activity-basics/guidelines/adults.html)
  - Adults need weekly aerobic work plus muscle-strengthening activity.
  - Activity can be split through the week; some activity is better than none.
- [CDC physical activity intensity and talk test](https://www.cdc.gov/physical-activity-basics/measuring/index.html)
  - Moderate intensity maps to roughly RPE 5-6 on a 0-10 effort scale.
  - Talk test is a practical intensity cue: moderate work allows talking but not singing.
- [CDC older adult activity and balance guidance](https://www.cdc.gov/physical-activity-basics/guidelines/older-adults.html)
  - Older adults need aerobic, strength, and balance activities weekly.
  - Balance examples include heel-to-toe walking and standing from sitting.
- [ACSM 2026 resistance training guidelines](https://acsm.org/resistance-training-guidelines-update-2026/)
  - Consistency beats complex programming for most adults.
  - Plans should be individualized around goals, enjoyment, and safety.
- [Runner's World run/walk beginner endurance coaching](https://www.runnersworld.com/training/a69889317/starting-a-run-walk-program/)
  - Coaches emphasize gradual duration progression, walk intervals, RPE/breathing cues, and not doing too much too soon.
- [Tom's Guide physical therapist mobility and balance exercises](https://www.tomsguide.com/wellness/workouts/no-sit-ups-or-planks-a-physical-therapist-shares-the-6-best-exercises-for-staying-independent-after-60)
  - Practical mobility and balance work should map to daily movement: sit-to-stand, rotation, tandem stance, single-leg balance, supported work.

### Findings extracted

- Endurance programming should include real aerobic work, not only high-rep strength:
  - walking, cycling, elliptical, rowing, stairs, or run/walk depending on equipment and constraints.
  - progress duration or frequency before intensity.
  - use RPE/talk-test cues instead of exact pace or heart-rate assumptions.
- A user saying "בלי ריצה" should not receive running language in the generated exercise notes or alternatives.
- Mobility programming should include range/control and balance work, not only slow squats/hinges.
- The builder already had `goal_focus` flags, but exercise selection ignored them; this was the narrow place to fix.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - Added CDC intensity/older-adult and coach/practitioner source refs.
  - Added `goal_focus`-based selection:
    - endurance starts with `cardio_base`.
    - mobility starts with `mobility_flow` and `balance_control`.
  - Added structured exercise catalog entries:
    - `אירובי בסיסי בקצב שיחה`
    - `זרימת מוביליטי ירך-גב-כתף`
    - `שיווי משקל והעברת משקל`
  - Kept the existing strength patterns after the goal-specific opening work.
  - Kept no-running requests on non-running cardio options.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Endurance rule now explicitly requires real aerobic work for לב-ריאה/סבולת plans.
  - Mobility rule now explicitly requires mobility/control and balance work when relevant.
  - Added Runner's World and Tom's Guide practitioner references to those rules.
- Updated `backend/tests/test_workout_plans_api.py`:
  - Goal-variable test now fails if endurance starts as high-rep strength instead of cardio.
  - Mobility test now fails if the plan lacks mobility and balance exercises.
  - Hebrew slang test now checks לב ריאה בלי ריצה produces walking/cycling style options and no running text.
  - Ponytail simplification narrowed the test text scan to exercise name, notes, and alternatives instead of all fields/source metadata.

### Tests and checks

- Initial focused run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus`
  - Result: `1 failed, 1 passed`.
  - Cause: product output neutralizer changes direct commands like "העלה" into "להעלות"; the test expected the pre-neutralized wording.
- Corrected focused run:
  - Same focused command.
  - Result: `2 passed`.
- Adjacent affected run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_cardio_programming_rules backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_mobility_flexibility_balance_programming`
  - Result before final source refs: `3 passed`.
- Post-Ponytail/source-ref combined run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_cardio_programming_rules backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_mobility_flexibility_balance_programming`
  - Result: `5 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran API-level Hebrew manual probe using prompts loaded from the UTF-8 test file:
  - `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
  - `תן לי תוכנית מוביליטי חודשית עם משקל גוף`
- Endurance output:
  - plan type: `two_week_plan`
  - goal: `improve_endurance`
  - first exercise: `אירובי בסיסי בקצב שיחה`
  - notes included non-running options: walking, cycling, elliptical, stairs.
  - `contains_running: False`
- Mobility output:
  - plan type: `monthly_plan`
  - goal: `improve_fitness`
  - first exercises: `זרימת מוביליטי ירך-גב-כתף`, `שיווי משקל והעברת משקל`.
  - `contains_running: False`

### Ponytail Review

- Finding applied:
  - `backend/tests/test_workout_plans_api.py`: shrink: the Hebrew endurance test joined every exercise field, including source refs. Replaced with name + notes + alternatives only.
- Post-fix result:
  - Lean already. Ship.

### Failures and fixes

- Focused test initially failed because it expected pre-neutralized Hebrew command wording.
  - Fixed assertion to match saved/product output: `להעלות משך או תדירות לפני עצימות`.
- First manual probe printed correct output but exited with a temp SQLite cleanup lock.
  - Reran with explicit `client.close()`, `db.close()`, engine dispose, and dependency override cleanup.
  - Removed temp directories only after resolving paths inside the workspace.

### Next research target

- Loop 51 should inspect whether chat responses and saved plan summaries expose the new endurance/mobility specificity clearly enough in natural Hebrew. The structured plan now has goal-specific content, but the coach response may still summarize it too generically or hide the first-action difference from the user.

## Loop 51 - Surface Goal-Specific First Actions In Chat Responses

### Research target

Verify that chat-facing Hebrew responses make the new goal-specific plan content visible. A plan can be structurally correct, but if the response only says "saved a plan", the user does not get one clear next action.

### Sources reviewed

- [CDC Overcoming Barriers to Physical Activity](https://www.cdc.gov/physical-activity-basics/overcoming-barriers/index.html)
  - Useful behavior change is concrete and schedule/action oriented.
  - For lack of time, choose activities that fit the time available.
  - For lack of motivation, make activity part of the weekly schedule.
  - For fear of injury, choose activities the person can do safely and progress gradually.
- Loop 50 sources carried forward:
  - CDC intensity/talk-test guidance for endurance.
  - Runner's World run/walk coach guidance for gradual, low-friction endurance starts.
  - Tom's Guide physical therapist mobility/balance examples for practical first movements.

### Findings extracted

- The normal saved-plan response already surfaced the first exercise through `_first_workout_next_action()`.
- The weak path was replacement candidates:
  - If the user already had an active plan, a new persistent plan became a candidate.
  - The response asked whether to replace the old plan, but did not preview what the new plan starts with.
- That hides the value of the new plan exactly when the user has to decide whether to replace the current plan.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - Replacement-candidate plan responses now include a short preview:
    - `האימון הראשון בתוכנית החדשה מתחיל ב...`
  - The replacement confirmation flow stays unchanged:
    - candidate does not become active automatically.
    - final action is still to answer `כן להחליף` or `להשאיר קיימת`.
- Updated `backend/tests/test_coach_engine.py`:
  - Added chat test for endurance first action:
    - Hebrew לב-ריאה request must mention `אירובי בסיסי בקצב שיחה`.
  - Added chat test for mobility first action:
    - Hebrew mobility request must mention `זרימת מוביליטי ירך-גב-כתף`.
  - Added replacement-candidate test:
    - after an active endurance plan exists, a new mobility plan response previews the first mobility exercise while preserving the replacement confirmation question.

### Tests and checks

- Initial focused chat tests before code change:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response`
  - Result: `3 passed`.
  - This confirmed normal plan responses already surfaced the first exercise.
- Focused chat tests after candidate-preview patch:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_previews_candidate_plan_first_action_before_replacement_confirmation`
  - Result: `4 passed`.
- Full coach-engine suite:
  - `python -m pytest backend/tests/test_coach_engine.py`
  - Result before patch: `98 passed`.
  - Result after patch: `99 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran a two-message Hebrew chat transcript through `/api/chat`:
  1. `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
  2. `תן לי תוכנית מוביליטי חודשית עם משקל גוף`
- Before the patch:
  - First response surfaced `אירובי בסיסי בקצב שיחה`.
  - Second response became a replacement candidate and did not show the mobility first exercise.
- After the patch:
  - First response still surfaced `אירובי בסיסי בקצב שיחה`.
  - Second response now includes:
    - `האימון הראשון בתוכנית החדשה מתחיל בזרימת מוביליטי ירך-גב-כתף.`
  - It still says the new plan does not replace the active plan yet and asks for explicit confirmation.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - The new helper is small and scoped to candidate previews.
  - Inlining the extraction would duplicate the same plan/day/exercise lookup inside the response builder.
  - Reusing the existing next-action helper would produce misleading wording for a candidate that is not active yet.

### Failures and fixes

- No automated test failures in this loop.
- Manual transcript exposed the real product gap:
  - candidate-plan response hid the first action.
  - Fixed with a candidate preview while preserving explicit replacement confirmation.

### Next research target

- Loop 52 should inspect whether the dashboard/current-plan view exposes endurance and mobility specificity, not only plan name/days/week. If the chat and saved plan are specific but the dashboard still hides the first upcoming action, the user may lose the "what should I do now" thread outside chat.

## Loop 52 - Show First Exercise Specificity On Dashboard

### Research target

Check whether the dashboard preserves the same "one clear next action" specificity that chat now gives for endurance and mobility plans.

### Sources reviewed

- Loop 51 research carried forward:
  - CDC barrier guidance supports concrete, time/action-oriented next steps.
  - Runner's World run/walk coaching supports showing the first endurance action rather than abstract cardio goals.
  - Physical-therapist mobility/balance guidance supports showing the first practical movement, not only a plan title.
- Existing product principle:
  - The dashboard should show the next recommended action and make progress visible without overwhelming the user.

### Findings extracted

- `WorkoutService.next_workout()` already builds an `execution_plan` with adjusted exercises.
- `DashboardService._next_workout_summary()` kept:
  - next workout id/name
  - load signal
  - next adjustment
  - progression gate
- It dropped the first adjusted exercise.
- Frontend dashboard showed:
  - plan name/type/weeks/session length
  - next workout name and load signal
  - recommended action text
- It did not show the first exercise or prescription, so a לב-ריאה plan could still look generic on the dashboard.

### Changes made

- Updated `backend/app/services/dashboard_service.py`:
  - Added compact `first_exercise` to `next_workout` summary:
    - name
    - sets
    - reps_or_duration
    - rest
  - Did not expose the full workout list in the dashboard payload.
- Updated `frontend/src/api.ts`:
  - Added optional `first_exercise` type to `DashboardState.next_workout`.
- Updated `frontend/src/DashboardPanel.tsx`:
  - Renders one compact line under the next workout:
    - `פותחים: ... | סטים | חזרות/משך | מנוחה ...`
- Updated `frontend/src/DashboardPanel.test.tsx`:
  - Dashboard fixture now uses an endurance plan and asserts the first action line includes `אירובי בסיסי בקצב שיחה`, duration, and RPE.
- Updated `backend/tests/test_dashboard_api.py`:
  - Dashboard API test now creates a Hebrew לב-ריאה plan and asserts `next_workout.first_exercise` contains the cardio opener.

### Tests and checks

- Focused backend dashboard test:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_next_recommended_action_reflects_available_state`
  - Result: `1 passed`.
- Dashboard UI test:
  - `npm.cmd --prefix frontend test -- --run src/DashboardPanel.test.tsx`
  - Result: `1 passed`, `3 tests passed`.
- Full dashboard API file:
  - `python -m pytest backend/tests/test_dashboard_api.py`
  - Result: `9 passed`.
- Frontend production build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- First manual script embedded Hebrew directly in a PowerShell here-string and produced a misleading strength first exercise.
  - Treated as an encoding-risk artifact, not product proof.
- Reran manual dashboard check by loading the Hebrew prompt from the UTF-8 test source:
  - prompt: `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
  - generated plan goal: `improve_endurance`
  - plan first exercise: `אירובי בסיסי בקצב שיחה`, `12-25 דקות`
  - dashboard first exercise:
    - name: `אירובי בסיסי בקצב שיחה`
    - sets: `1`
    - reps_or_duration: `12-25 דקות`
    - rest: `RPE 5-6 / אפשר לדבר במשפטים קצרים`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - The dashboard gets one bounded first-exercise summary, not the whole plan or full exercise list.
  - No new dashboard card or state machine was added.
  - Frontend rendering is a single line inside the existing next-action card.

### Failures and fixes

- No automated test failures.
- Manual probe initially gave a false mismatch due inline Hebrew shell encoding.
  - Fixed by loading the prompt from the UTF-8 test source.

### Next research target

- Loop 53 should inspect whether goal inference and profile defaults behave correctly when a user asks for a different goal than their stored profile. Manual probing reminded that this path is easy to misread; the code appears to prefer prompt-inferred goal, but tests should explicitly lock Hebrew goal override behavior for active profiles.

## Loop 53 - Lock Hebrew Prompt Goal Override Over Saved Profile Goal

### Research target

Verify that a user with a saved profile goal can still ask for a different Hebrew goal and get the requested plan, not the profile default.

### Sources reviewed

- Existing product principle:
  - The bot should retrieve relevant profile context, but not let stored context override the user's current explicit request.
- Existing planner code:
  - `goal = request.goal or inferred_goal or profile_goal or "improve_fitness"`
- Loop 52 manual finding:
  - Inline Hebrew in PowerShell can mislead manual probes; source-loaded UTF-8 prompts are safer proof.

### Findings extracted

- Existing code already prefers:
  1. explicit request goal
  2. prompt-inferred goal
  3. profile goal
  4. default `improve_fitness`
- Existing tests covered open-ended profile defaults and Hebrew goal slang separately.
- Missing test:
  - saved profile says one goal, Hebrew prompt asks another goal.
- This is exactly the risk area for a remembered coach: context should help when the request is vague, not override a clear current ask.

### Changes made

- Updated `backend/tests/test_workout_plans_api.py`:
  - Added `test_workout_plan_hebrew_prompt_goal_overrides_saved_profile_goal`.
  - Scenario:
    - saved profile goal: strength
    - prompt: לב ריאה לשבועיים בלי ריצה
  - Assertions:
    - plan goal is `improve_endurance`
    - plan type is `two_week_plan`
    - profile defaults still fill availability/equipment
    - first exercise is the cardio opener
    - no running text appears in the first exercise notes.
- Updated `backend/tests/test_coach_engine.py`:
  - Tightened the chat endurance first-action test to assert the saved plan goal is `improve_endurance`.

### Tests and checks

- Focused workout-plan profile/default tests:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_uses_saved_profile_when_request_is_open_ended backend/tests/test_workout_plans_api.py::test_workout_plan_hebrew_prompt_goal_overrides_saved_profile_goal`
  - Result: `2 passed`.
- Chat + planner goal override focused run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_hebrew_prompt_goal_overrides_saved_profile_goal backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response`
  - Result: `2 passed`.
- Full workout-plan API file:
  - `python -m pytest backend/tests/test_workout_plans_api.py`
  - Result: `30 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Loaded the Hebrew prompt from the UTF-8 test source and ran `/api/workout-plans`.
- Result:
  - profile goal: `improve_strength`
  - prompt: `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
  - status: `200`
  - plan goal: `improve_endurance`
  - plan type: `two_week_plan`
  - equipment: profile-backed `resistance bands`
  - first exercise: `אירובי בסיסי בקצב שיחה`, `12-25 דקות`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Test-only loop.
  - No production code added.
  - Assertions target the exact behavior boundary: prompt-inferred goal beats saved profile goal, while useful profile defaults still apply.

### Failures and fixes

- No automated test failures.
- No production fix was needed; the behavior was already correct.

### Next research target

- Loop 54 should inspect whether explicit `request.goal` from API clients takes priority over Hebrew prompt text, and whether that can produce user-hostile behavior if the UI or future channel accidentally sends a stale goal field. The precedence is intentional for typed API calls, but the product may need a guard or test around conflicts.

## Loop 54 - Prefer Current Hebrew Goal Text Over Stale Structured Goal Fields

### Research target

Check whether an explicit API `goal` field can silently override the user's current Hebrew request, especially if a future UI, WhatsApp channel, or cached form state sends stale structured metadata.

### Sources reviewed

- Nielsen Norman Group, Jakob Nielsen, "10 Usability Heuristics for User Interface Design", updated 2024-01-30:
  - https://www.nngroup.com/articles/ten-usability-heuristics/

### Findings extracted

- Visibility of system status:
  - Users should see outcomes that match the action they just took.
  - A hidden stale field that changes the plan goal would break trust.
- Match with the real world:
  - The system should use the user's language and concepts.
  - If the Hebrew prompt says `לב ריאה`, the planner should treat that as the current intent.
- Error prevention:
  - Good defaults and constraints should prevent user-hostile mistakes before they happen.
  - Stale structured fields are exactly the kind of preventable mistake a coach product should guard against.
- Minimalist design:
  - Do not ask a clarification question when the current text is already clear.
  - Infer safely, save the assumption, and proceed.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - Changed workout goal precedence from `request.goal -> prompt inference -> profile goal -> default` to `prompt inference -> request.goal -> profile goal -> default`.
  - Added a persisted planning assumption when a structured `goal` field conflicts with a clearly inferred prompt goal.
- Updated `backend/tests/test_workout_plans_api.py`:
  - Added `test_workout_plan_hebrew_prompt_goal_beats_conflicting_request_goal`.
  - Added `test_workout_plan_request_goal_still_applies_when_prompt_has_no_goal`.

### Tests and checks

- Focused conflict tests:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_hebrew_prompt_goal_beats_conflicting_request_goal backend/tests/test_workout_plans_api.py::test_workout_plan_request_goal_still_applies_when_prompt_has_no_goal --basetemp .pytest-tmp-loop54-focused`
  - Result: `2 passed`.
- Full workout-plan API file:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop54-workout-api`
  - Result: `32 passed`.
- Chat-side focused tests:
  - First run used stale test names and collected zero tests.
  - Corrected run:
    - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_previews_candidate_plan_first_action_before_replacement_confirmation --basetemp .pytest-tmp-loop54-chat`
    - Result: `2 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran a manual API probe with Unicode-escaped Hebrew to avoid PowerShell encoding corruption.
- Scenario:
  - saved profile goal: `improve_strength`
  - request body `goal`: `build_muscle`
  - prompt: `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
- Result:
  - status: `200`
  - plan goal: `improve_endurance`
  - plan type: `two_week_plan`
  - first exercise: `אירובי בסיסי בקצב שיחה`
  - assumption saved: `הטקסט ציין מטרה שונה משדה goal, השתמשתי במטרה מתוך הבקשה.`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - The production change is one precedence line plus one existing assumptions entry.
  - The tests cover the two necessary branches without adding helpers or a new policy object.
  - No new abstraction was introduced.

### Failures and fixes

- One chat test command failed because the remembered test names were stale.
  - Root cause: local test functions have different names.
  - Fix: inspected the file and reran the intended local tests by their actual names.
- No product behavior failure after the code change.

### Next research target

- Loop 55 should broaden practitioner research into how Israeli and global coaches phrase beginner plans, progression, warmups, substitutions, and "one clear next action" in natural language. The code now picks the right goal; the next risk is that the saved plan is technically correct but still sounds too clinical or generic in Hebrew.

## Loop 55 - Natural Hebrew Tracking Language From Practitioner Sources

### Research target

Broaden beyond generic medical/academic sources and inspect practitioner language for how plans explain progression, home training, tracking, and one practical next action.

### Sources reviewed

- Barbell Medicine, Austin Baraki, MD, "Pain in training: What To Do?", updated 2026-03-28:
  - https://www.barbellmedicine.com/blog/pain-in-training-what-do/
- RP Strength, "Complete Hypertrophy Training Guide":
  - https://rpstrength.com/blogs/articles/complete-hypertrophy-training-guide
- Precision Nutrition, John Berardi, PhD, CSCS, "Making the most of your time in the gym":
  - https://www.precisionnutrition.com/exercise-progressions
- ONEBODY Israel, Nir Gorgi, "פול בודי - עובדים על כל הגוף באימון אחד":
  - https://www.onebody.co.il/fbw-gym/
- ONEBODY Israel, Roy Glazan, "איך להתאמן בבית בצורה אפקטיבית מבלי להשתמש בציוד מיוחד":
  - https://www.onebody.co.il/how-to-home-workout/

### Findings extracted

- Barbell Medicine:
  - Pain modification should find a tolerable entry point, often by reducing load, range of motion, tempo, volume or exercise selection.
  - Progression after pain should be conservative and based on stable symptoms over 24-48 hours, not aggressive jumps.
- RP Strength:
  - Hypertrophy planning should start with low set counts and add sets only when recovery is not sufficiently challenged.
  - A few exercises per session/week per muscle group are enough; too many exercises create confusion and fatigue.
- Precision Nutrition:
  - Progression is the question that matters, including for cardio and fat-loss support.
  - Users need a concrete way to know how work increases between sessions.
- ONEBODY Israel:
  - Natural Israeli plan language commonly uses `פול בודי`, `2-3 אימונים בשבוע`, `יום כן יום לא`, `משקל גוף`, `קצב עבודה`, `זמן עבודה`, `התנגדות`.
  - Useful tracking phrasing: do not guess what happened last workout; write down the weights/reps or the completed work.
  - Tone caveat:
    - Some practitioner phrasing is too shaming or macho for this product.
    - Extract the practical language, not the guilt-based tone.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - Tracking guidance now says:
    - `לא לנחש מה היה באימון הקודם: לתעד את התרגיל המרכזי - חזרות, משקל אם יש, ו-RIR או כמה חזרות נשארו ברזרבה.`
- Updated `backend/app/services/coaching_knowledge.py`:
  - Added compact provider-context language rule:
    - natural Hebrew terms, not `מערכות/הישנויות`, and `מעקב: לא לנחש`.
  - Added knowledge-center tracking policy rule:
    - use natural coach language and tell the user to write down the main exercise instead of guessing.
  - Added practitioner source refs to the tracking policy:
    - `Precision Nutrition Exercise Progressions`
    - `OneBody FBW Gym Plan`
- Updated tests:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coaching_knowledge.py`

### Tests and checks

- Focused run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_conservative_assumptions_for_minimal_prompt backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom --basetemp .pytest-tmp-loop55-focused`
  - First result: failed.
  - Root causes:
    - Test expected a slightly different Hebrew phrase than the saved guidance.
    - Provider context exceeded the strict budget by adding a separate sentence.
  - Fix:
    - clarified the saved guidance to use `את התרגיל המרכזי`.
    - merged `לא לנחש` into the existing compact provider-context line.
  - Final result: `2 passed`.
- Affected run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop55-affected`
  - First result: `143 passed, 1 failed`.
  - Root cause:
    - I trimmed away the existing required Hebrew terminology rule: `סטים/חזרות לא מערכות/הישנויות`.
  - Fix:
    - restored that terminology in the compact provider-context line and shaved only `RIR`.
  - Final result: `144 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran a Hebrew chat request through `/api/chat` using Unicode escapes to avoid PowerShell Hebrew corruption.
- Prompt:
  - `תבנה לי תוכנית אימונים לשבועיים בבית בלי ציוד`
- Result:
  - status: `200`
  - provider status: `local_tool`
  - saved plan type: `two_week_plan`
  - saved tracking guidance includes:
    - `לא לנחש מה היה באימון הקודם: לתעד את התרגיל המרכזי - חזרות, משקל אם יש, ו-RIR או כמה חזרות נשארו ברזרבה.`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - The builder persists one practical sentence.
  - The knowledge center records the same behavior as a rule.
  - Tests lock both surfaces.
  - No helper, class, or new policy object was added.

### Failures and fixes

- Failed focused test due exact Hebrew wording mismatch.
  - Fixed by improving production wording and preserving the test intent.
- Failed provider context budget.
  - Fixed by merging the new rule into an existing compact sentence, not by raising the budget.
- Failed existing Hebrew terminology test.
  - Fixed by restoring `סטים/חזרות לא מערכות/הישנויות`.

### Next research target

- Loop 56 should inspect whether single-workout and weekly-plan visible chat responses should surface the same natural tracking language, or whether keeping it only inside the saved structured plan is enough. The risk is response clutter: adding too much tracking text to the chat preview could violate the "one clear next action" rule.

## Loop 56 - Surface Natural Tracking Cue In Visible Chat Without Clutter

### Research target

Decide whether the visible chat response should include the same `לא לנחש` tracking cue added to saved structured plans, without violating the "one clear next action" response rule.

### Sources reviewed

- Nielsen Norman Group, Jakob Nielsen, "10 Usability Heuristics for User Interface Design", updated 2024-01-30:
  - https://www.nngroup.com/articles/ten-usability-heuristics/
- Digital.gov / PlainLanguage.gov, "Plain language guide series":
  - https://digital.gov/guides/plain-language
- ONEBODY Israel, "פול בודי - עובדים על כל הגוף באימון אחד":
  - https://www.onebody.co.il/fbw-gym/

### Findings extracted

- NN/G minimalist design:
  - Extra information competes with relevant information.
  - Do not add a paragraph of tracking instructions to the plan preview.
- Plain language:
  - Content should be written for the audience and help them act immediately.
  - The right level is a short phrase inside the next action, not a separate explanation.
- ONEBODY practitioner phrasing:
  - Tracking should prevent guessing what happened in the previous workout.
  - The practical idea is useful; the product should keep the wording calmer than macho practitioner copy.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - Single-workout visible next action now ends with:
    - `ולתעד RPE/כאב ומה הושלם - לא לנחש.`
  - Persistent plan visible next action now ends with:
    - `ואז לתעד RPE/כאב ומה הושלם - לא לנחש.`
- Updated `backend/tests/test_coach_engine.py`:
  - Existing single-workout response test now asserts `לא לנחש`.
  - Existing endurance plan response test now asserts `לא לנחש`.
  - Existing mobility plan response test now asserts `לא לנחש`.

### Tests and checks

- Focused chat tests:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response --basetemp .pytest-tmp-loop56-focused`
  - Result: `3 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop56-coach`
  - Result: `99 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran a Hebrew `/api/chat` endurance request using Unicode escapes:
  - `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
- Result:
  - status: `200`
  - provider status: `local_tool`
  - response stays one next action:
    - `הפעולה הבאה: להתחיל מיום שני גוף מלא, תרגיל ראשון אירובי בסיסי בקצב שיחה, ואז לתעד RPE/כאב ומה הושלם - לא לנחש.`
- Encoding note:
  - The first boolean check used a raw Hebrew literal in PowerShell and returned false even though the printed response had the phrase.
  - Reran with Unicode-escaped `לא לנחש`; result was `True`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - The change is one concise suffix in the existing next-action helper.
  - No new helper or formatter was added.
  - Extracting a constant for two adjacent return strings would be more code than the duplication.

### Failures and fixes

- No automated failures.
- Manual proof had one false negative due raw Hebrew shell literal.
  - Fixed by rerunning the check with Unicode escapes.

### Next research target

- Loop 57 should inspect if replacement-candidate responses should include the same tracking cue before confirmation, or if that would confuse users because the candidate is not active yet. The likely rule is: preview the first exercise, but do not instruct logging until activation.

## Loop 57 - Candidate Plan Preview Should Not Tell Users To Log Yet

### Research target

Check whether replacement-candidate responses should include the same `לא לנחש` tracking cue added to active plan responses.

### Sources reviewed

- Nielsen Norman Group, "10 Usability Heuristics for User Interface Design":
  - visibility of system status
  - user control and freedom
  - error prevention
- Existing product rule:
  - a candidate plan is saved but not active until the user confirms replacement.

### Findings extracted

- The candidate response has a different job than an active-plan response:
  - show the user what was created
  - clearly state it has not replaced the active plan
  - ask for the next decision
- Adding logging language before activation would be misleading:
  - the user might start logging against a plan that is not active
  - the next action should be `כן להחליף` or `להשאיר קיימת`, not workout tracking
- Best path:
  - keep first-exercise preview
  - explicitly avoid active-plan tracking instructions until activation

### Changes made

- Updated `backend/tests/test_coach_engine.py` only:
  - `test_chat_endpoint_previews_candidate_plan_first_action_before_replacement_confirmation` now asserts candidate responses do not include:
    - `לא לנחש`
    - `לתעד RPE/כאב`

### Tests and checks

- Focused candidate test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_previews_candidate_plan_first_action_before_replacement_confirmation --basetemp .pytest-tmp-loop57-focused`
  - Result: `1 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop57-coach`
  - Result: `99 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran two Hebrew `/api/chat` messages:
  1. active endurance plan request
  2. mobility monthly plan request, creating a candidate
- Result:
  - status: `200`
  - candidate preview present: `True`
  - not-active-yet message present: `True`
  - `לא לנחש`: `False`
  - `לתעד RPE/כאב`: `False`
  - response next action remains confirmation:
    - `לענות 'כן להחליף' כדי להפעיל אותה, או 'להשאיר קיימת' כדי למחוק את המועמדת.`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Test-only loop.
  - Two negative assertions lock the state distinction without changing production code.
  - No helper or new response mode was added.

### Failures and fixes

- No automated failures.
- No production fix needed; existing behavior was correct.

### Next research target

- Loop 58 should inspect plan activation responses after a candidate is confirmed. If activation is the first moment the new plan becomes actionable, the activation response may need the same concise `לא לנחש` tracking cue.

## Loop 58 - Add Tracking Cue To Activation Response Only After Confirmation

### Research target

Inspect the replacement confirmation flow and decide whether the activation response should include the same concise tracking cue as active plan responses.

### Sources reviewed

- Nielsen Norman Group, "10 Usability Heuristics for User Interface Design":
  - visibility of system status
  - user control and freedom
  - error prevention
- Loop 57 product rule:
  - candidate preview should not ask the user to log because the candidate is not active yet.

### Findings extracted

- Activation is the first moment the new candidate becomes the actionable current plan.
- Therefore the activation response should:
  - confirm state changed
  - keep the horizon summary
  - give one next action
  - include the practical tracking cue
- This does not belong in the candidate response before confirmation.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - `_activated_plan_response()` now ends with:
    - `הפעולה הבאה: להתחיל מהאימון הראשון ולתעד RPE/כאב ומה הושלם - לא לנחש.`
- Updated `backend/tests/test_coach_engine.py`:
  - Replacement confirmation test now asserts:
    - `לתעד RPE/כאב ומה הושלם`
    - `לא לנחש`

### Tests and checks

- Focused replacement confirmation test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_confirms_plan_replacement_deletes_old_plan_and_keeps_log_history --basetemp .pytest-tmp-loop58-focused`
  - Result: `1 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop58-coach`
  - Result: `99 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran Hebrew `/api/chat` replacement flow:
  1. create active endurance plan
  2. create mobility candidate
  3. send `כן להחליף`
- Result:
  - candidate response has `לא לנחש`: `False`
  - activation response has `לא לנחש`: `True`
  - activation response:
    - `התוכנית החדשה פעילה עכשיו... הפעולה הבאה: להתחיל מהאימון הראשון ולתעד RPE/כאב ומה הושלם - לא לנחש.`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - The response text is updated in place.
  - No new formatter or state machine was added.
  - Extracting a constant for a short repeated suffix would make this less direct.

### Failures and fixes

- No automated failures.
- No manual verification failures.

### Next research target

- Loop 59 should inspect workout-plan UI surfaces. Backend and chat now expose better tracking language, but the frontend plan viewer may still show generic guidance or omit tracking instructions from the place users actually read before training.

## Loop 59 - Verify Workout UI Shows Saved Tracking Guidance

### Research target

Check whether the frontend workout-plan view surfaces the new tracking guidance where users actually read the plan before training.

### Sources reviewed

- Existing `WorkoutsPanel` UI:
  - current plan view
  - `מעקב והתקדמות` section
  - `מה לתעד` subsection
- Loop 55-58 product rule:
  - saved structured plan data should carry the tracking rule, and active chat responses should expose it concisely.

### Findings extracted

- The UI already renders `plan.tracking_guidance` under `מה לתעד`.
- Adding a new UI panel would be duplicate and noisier.
- The missing piece was test coverage that the new `לא לנחש` guidance actually appears in the plan view.

### Changes made

- Updated `frontend/src/WorkoutsPanel.test.tsx` only:
  - current-plan fixture now includes:
    - `לא לנחש מה היה באימון הקודם: לתעד את התרגיל המרכזי - חזרות, משקל אם יש, ו-RIR או כמה חזרות נשארו ברזרבה.`
  - current-plan render test now asserts the phrase appears under the existing `מה לתעד` section.

### Tests and checks

- Frontend test command:
  - `npm.cmd test -- frontend/src/WorkoutsPanel.test.tsx --runInBand`
  - Project wrapper behavior:
    - backend suite ran: `480 passed`
    - frontend suite ran: `9 files passed, 42 tests passed`
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Product inspection:
  - `WorkoutsPanel` already renders `tracking_guidance` with no extra UI needed.
  - The tested Hebrew text appears under the user-facing `מה לתעד` heading, not hidden in debug or API-only data.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Test-only loop.
  - No duplicate UI block was added.
  - Existing data-driven rendering is reused.

### Failures and fixes

- No automated failures.
- No production change needed.

### Next research target

- Loop 60 should inspect whether `tracking_guidance` survives compact provider context and dashboard summaries after the recent language changes. The backend had a previous compact-provider fix; verify the new guidance is not lost in downstream surfaces.

## Loop 60 - Verify Natural Tracking Guidance Survives Provider Context Compaction

### Research target

Verify that the new `לא לנחש` tracking guidance remains available when the coach builds an optimized provider request.

### Sources reviewed

- Existing `token_budgeting.compact_provider_context()` implementation.
- Existing `ContextBuilder` and token optimization tests.
- Loop 49 prior rule:
  - `progression_schedule` and `tracking_guidance` must survive compaction.

### Findings extracted

- The compactor already preserves `tracking_guidance`, but only keeps the first two items.
- The fixture order matters:
  - if the new `לא לנחש` rule is third, it will be dropped from optimized provider context.
  - the correct order is practical tracking rule first, weekly/monthly summary second.

### Changes made

- Updated `backend/tests/test_token_optimization.py` only:
  - Added the `לא לנחש` tracking guidance to the current workout plan fixture.
  - Ordered tracking guidance so the compacted context keeps:
    1. the practical no-guessing rule
    2. the weekly summary rule
  - Added assertion that optimized context includes `לא לנחש`.

### Tests and checks

- Focused token compaction test:
  - `python -m pytest backend/tests/test_token_optimization.py::test_optimized_chat_request_cuts_input_tokens_by_half_without_dropping_context --basetemp .pytest-tmp-loop60-focused`
  - Result: `1 passed`.
- Full token optimization file:
  - `python -m pytest backend/tests/test_token_optimization.py --basetemp .pytest-tmp-loop60-token`
  - Result: `4 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Ran `compact_provider_context()` manually with a monthly plan containing:
  - `לא לנחש...`
  - weekly summary guidance
- Result:
  - compacted `current_workout_plan.tracking_guidance` contains both expected items.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Test-only loop.
  - Uses existing token optimization test and existing compactor.
  - No production code or helper was needed.

### Failures and fixes

- No automated failures.
- A quick `rg` verification command used an overly specific pattern and returned no matches.
  - Reran with a simpler `לא לנחש|tracking_guidance` pattern and confirmed the edits.

### Next research target

- Loop 61 should inspect dashboard summary surfaces specifically. The plan viewer and provider context now preserve tracking guidance, but the dashboard next action may still omit the no-guessing cue when it points users to the next workout.

## Loop 61 - Surface No-Guess Tracking Cue In Dashboard Next Action

### Research target

Verify that the dashboard's next recommended workout action carries the same practical tracking rule already present in saved plans, chat activation, and provider context.

### Sources reviewed

- Existing dashboard service:
  - `backend/app/services/dashboard_service.py`
- Existing dashboard API tests:
  - `backend/tests/test_dashboard_api.py`
- Existing dashboard UI tests:
  - `frontend/src/DashboardPanel.test.tsx`
- Prior Loop 55-60 rule:
  - Workout guidance should tell the user to record what happened, especially RPE/pain/completion, and not guess from memory.

### Findings extracted

- Dashboard actions are high-leverage because users see them before deciding what to do next.
- The no-guess cue belongs only on workout-backed next actions, not onboarding or nutrition actions.
- The smallest useful product change is to append the cue to the existing workout action string.
- No new UI component or dashboard data model is needed.

### Changes made

- Updated `backend/app/services/dashboard_service.py`:
  - workout-backed `next_recommended_action` now ends with:
    - `לתעד RPE/כאב ומה הושלם - לא לנחש.`
- Updated `backend/tests/test_dashboard_api.py`:
  - dashboard next-action test now uses a Hebrew endurance plan prompt.
  - asserts first exercise summary still appears.
  - asserts the planned action includes `לא לנחש`.
- Updated `frontend/src/DashboardPanel.test.tsx`:
  - dashboard fixture uses a Hebrew endurance plan.
  - asserts the visible next action includes `לא לנחש`.

### Tests and checks

- Focused dashboard next-action test:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_next_recommended_action_reflects_available_state --basetemp .pytest-tmp-loop61-dashboard`
  - Result: `1 passed`.
- Full dashboard API file:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop61-dashboard-full`
  - Result: `9 passed`.
- Dashboard frontend command:
  - `npm.cmd test -- frontend/src/DashboardPanel.test.tsx --runInBand`
  - Project wrapper behavior:
    - backend suite ran: `480 passed`
    - frontend suite ran: `9 files passed, 42 tests passed`
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual API probe created isolated onboarding and a Hebrew endurance plan, then fetched `/api/dashboard`.
- Observed `next_recommended_action`:
  - `לבצע את יום שני גוף מלא. שמור על התוכנית הנוכחית ואסוף עוד לוגים לפני שינוי משמעותי. לתעד RPE/כאב ומה הושלם - לא לנחש.`
- Confirmed:
  - `has_no_guess=True`
  - dashboard returned a real `next_workout_id`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Production change is one existing action suffix.
  - Tests reuse existing dashboard API and UI coverage.
  - No new helper, component, or abstraction was introduced for this cue.

### Failures and fixes

- No automated failures.
- No production follow-up needed for this surface.

### Next research target

- Loop 62 should inspect the dashboard progression-gate branch. It already has conservative progression copy, but may not consistently include the same no-guess wording when a substituted exercise is being advanced.

## Loop 62 - Add No-Guess Evidence Rule To Progression Gates

### Research target

Check whether the dashboard progression-gate branch should use the same no-guess tracking language after a regression/substitution, especially when the user is allowed to progress one step.

### Sources reviewed

- Barbell Medicine - Pain in Training: What To Do?
  - `https://www.barbellmedicine.com/blog/pain-in-training-what-do/`
  - Relevant finding: after pain or a modified entry point, progression should be based on stable symptoms over the next 24-48 hours, conservative increments, and avoiding overly aggressive jumps.
- Stronger by Science - The Science of Autoregulation
  - `https://www.strongerbyscience.com/autoregulation/`
  - Relevant finding: RPE/RIR is useful when it is a structured, anchored self-report, not vague "training by feel".
- OneBody Israel - פול בודי - עובדים על כל הגוף באימון אחד
  - `https://www.onebody.co.il/fbw-gym/`
  - Relevant finding: Hebrew practitioner language explicitly says to track weights and not guess what was done in the previous workout.

### Findings extracted

- A progression gate is not just an encouragement to progress.
- It is a decision rule:
  - clean completion
  - RPE 8 or lower
  - no pain
  - progress one step only
  - record actual evidence instead of guessing.
- The dashboard gate branch was more conservative than a normal progress action, but it did not consistently include `לא לנחש`.
- The source of the gate text is usually `WorkoutService` execution notes, with `DashboardService` only providing a fallback.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - substitution progression-gate execution notes now end with `לא לנחש`.
  - session-level progression-gate note now says not to guess what happened in the sets.
- Updated `backend/app/services/dashboard_service.py`:
  - fallback progression-gate action now includes `לא לנחש`.
- Updated `backend/app/services/coaching_knowledge.py`:
  - scoped edit policy now says not to guess set data after regression/substitution.
  - dashboard adherence rule now says the next action must not guess workout data.
- Updated tests:
  - `backend/tests/test_dashboard_api.py`
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_coaching_knowledge.py`

### Tests and checks

- First focused command used a stale knowledge test name:
  - Result: failed before running tests; corrected the node id.
- Corrected focused set:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_surfaces_progression_gate_after_regressed_exercise_clean_log backend/tests/test_dashboard_api.py::test_dashboard_surfaces_session_level_progression_gate_note_after_chat_log backend/tests/test_workout_logs_api.py::test_next_workout_uses_progression_gate_after_clean_log_for_regressed_pushup backend/tests/test_workout_logs_api.py::test_next_workout_keeps_pain_substitution_progression_generic_after_clean_log backend/tests/test_coach_engine.py::test_chat_workout_log_with_session_rpe_no_pain_opens_progression_gate backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols --basetemp .pytest-tmp-loop62-focused`
  - Result: `6 passed`.
- Affected backend files:
  - `python -m pytest backend/tests/test_dashboard_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop62-affected`
  - Result: `241 passed`.
- Tightened dashboard knowledge assertion:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_progress_measurement_protocols --basetemp .pytest-tmp-loop62-knowledge-tighten`
  - Result: `1 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew flow used isolated SQLite:
  1. onboarding
  2. created Hebrew weekly beginner bodyweight plan
  3. chat: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`
  4. local edit regressed the push-up to `שכיבת סמיכה על קיר`
  5. logged clean completion with RPE 8, RIR 2, no pain
  6. fetched `/api/dashboard`
- Final observed gate/action:
  - progression gate includes `לתעד RPE וכאב אחרי הסטים - לא לנחש`.
  - dashboard next action includes the same gate text.
  - `has_no_guess=True`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - No helper or new abstraction added.
  - The production change is plain user-facing copy in the existing execution-note source and dashboard fallback.
  - A shared string helper would add indirection without reducing meaningful complexity.

### Failures and fixes

- Manual probe 1 failed because the selector expected `movement_pattern` in `/api/workouts/next` exercise output.
  - Fixed by inspecting payload and matching the actual regressed exercise name.
- Manual probe 2 still failed because Hebrew typed directly into the PowerShell here-string did not reach the API reliably and the chat fell through to the configured AI path.
  - Fixed by sending Hebrew via Unicode escapes, which triggered the deterministic `local_tool` route.
- No automated test failures after the stale node id was corrected.

### Next research target

- Loop 63 should inspect the chat response after a clean progression-gate log. The workout execution note and dashboard now say `לא לנחש`, but the immediate chat response after logging may still open the gate without that same no-guess wording.

## Loop 63 - Add No-Guess Cue To Immediate Progression-Gate Chat Responses

### Research target

Verify whether the immediate chat response after logging a clean progression-gate workout should also include the no-guess tracking cue.

### Sources reviewed

- Reused Loop 62 sources because this loop is the same decision surface, only in the chat response:
  - Barbell Medicine - Pain in Training: What To Do?
  - Stronger by Science - The Science of Autoregulation
  - OneBody Israel - פול בודי - עובדים על כל הגוף באימון אחד
- Additional web searches for ACE/Precision Nutrition coaching language did not return usable source pages in the current search tool. No code decision depended on those failed searches.

### Findings extracted

- The chat response is the first surface the user sees after logging.
- If the chat says a progression gate is open, it should still tell the user to record real evidence and not infer missing set data from memory.
- This should apply to:
  - missing RPE/pain status
  - session-level RPE/no-pain logs
  - exercise-level clean logs with a named next step
  - generic pain-substitution progression gates.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - missing-info gate response now says the bot will keep the current version and not guess.
  - session-level gate response now says to record exercise reps/RPE and not guess.
  - exercise-level named next-step response now says to document the next attempt and not guess.
  - generic gate response now says to document the next attempt and not guess.
- Updated `backend/tests/test_coach_engine.py`:
  - added assertions for `לא ננחש` / `לא לנחש` across the four progression-gate chat paths.

### Tests and checks

- Focused chat progression-gate tests:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_workout_log_for_progression_gate_asks_for_missing_rpe backend/tests/test_coach_engine.py::test_chat_workout_log_with_session_rpe_no_pain_opens_progression_gate backend/tests/test_coach_engine.py::test_chat_workout_log_with_exercise_reps_names_next_progression_step backend/tests/test_coach_engine.py::test_chat_workout_log_after_pain_substitution_keeps_progression_generic --basetemp .pytest-tmp-loop63-focused`
  - Result: `4 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop63-coach`
  - Result: `99 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew flow used isolated SQLite and Unicode-escaped Hebrew strings:
  1. created Hebrew weekly beginner bodyweight plan
  2. chat edit: `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`
  3. chat log: `תעד אימון: עשיתי שכיבת סמיכה על קיר 1 סט 10 חזרות, RPE 8, בלי כאב`
  4. observed `provider=local_tool`
  5. observed response includes:
     - `לתעד בפועל ולא לנחש`
  6. `has_no_guess=True`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Four existing response strings were tightened.
  - No helper, route, schema, or abstraction was added.
  - Tests reuse the existing coach-engine progression-gate scenarios.

### Failures and fixes

- No automated failures.
- Manual Hebrew probe used Unicode escapes from the start to avoid the PowerShell encoding issue found in Loop 62.

### Next research target

- Loop 64 should inspect whether normal small-progress workout logs outside substitution/regression gates still encourage guessing from memory. If they already tell users to log enough data, leave them alone; if not, tighten the smallest response path only.

## Loop 64 - Stop Generic Session RPE Logs From Progressing By Guess

### Research target

Inspect normal workout-log chat responses outside substitution/regression progression gates. The risk: a session-only RPE log might make the bot suggest adding a rep without exercise-level reps or set data.

### Sources reviewed

- Stronger by Science - The Science of Autoregulation
  - RPE/RIR is useful when anchored and tied to the work actually performed.
- Barbell Medicine - Pain in Training: What To Do?
  - Progression should be conservative and based on observed tolerance, not a rigid automatic jump.
- OneBody Israel - פול בודי - עובדים על כל הגוף באימון אחד
  - Hebrew practitioner rule: track weights and do not guess the previous workout.
- Existing code:
  - `backend/app/services/coach_engine.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- The generic `log.rpe is not None` branch ran before checking `log.exercise_results`.
- That meant a message like:
  - `סיימתי אימון, מאמץ 8 מתוך 10, בלי כאב`
  could produce:
  - add one rep in the main exercise
  even though the bot did not know which exercise or reps were completed.
- This is product-risky because it violates the knowledge-center rule:
  - do not progress from guessed workout data.

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - high RPE behavior unchanged.
  - structured exercise logs with manageable RPE may still suggest one-rep progression and now say to document it.
  - session-only manageable RPE logs now say:
    - central exercise/reps are missing
    - repeat the same structure
    - record central exercise, reps, RPE and pain
    - do not add a rep from a guess.
- Added `backend/tests/test_coach_engine.py::test_chat_endpoint_session_rpe_log_does_not_progress_from_missing_exercise_data`.

### Tests and checks

- Focused tests:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_session_rpe_log_does_not_progress_from_missing_exercise_data backend/tests/test_coach_engine.py::test_chat_endpoint_logs_workout_with_negated_pain_without_safety_override --basetemp .pytest-tmp-loop64-focused`
  - Result: `2 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop64-coach`
  - Result: `100 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew chat probe used isolated SQLite and Unicode-escaped Hebrew:
  - `סיימתי אימון, מאמץ 8 מתוך 10, בלי כאב`
- Observed:
  - `provider=local_tool`
  - response says central exercise with reps is missing
  - response says `לא להוסיף חזרה מתוך ניחוש`
  - `has_no_guess=True`
  - `has_add_one_rep=False`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One branch split and one focused regression test.
  - No extra service, schema, setting, or abstraction.

### Failures and fixes

- No automated failures.
- Manual probe passed on first attempt by using Unicode escapes.

### Next research target

- Loop 65 should inspect structured workout-log parsing and responses for Hebrew gym slang around RPE/RIR and pain. The current safer response depends on correctly distinguishing session-only logs from exercise-level logs.

## Loop 65 - Parse Hebrew Gym Shorthand As Exercise-Level Evidence

### Research target

Inspect the workout-log parser boundary. The safer Loop 64 response depends on distinguishing:

- session-only log:
  - `סיימתי אימון, מאמץ 8 מתוך 10`
- exercise-level log:
  - exercise name + sets/reps/load + RPE/pain.

### Sources reviewed

- Existing workout log parser and tests:
  - `backend/app/services/workout_service.py`
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_coach_engine.py`
- Prior research carried forward:
  - Stronger by Science: RPE/RIR is useful when anchored to the work performed.
  - OneBody Israel: Hebrew practitioner guidance emphasizes tracking weights instead of guessing previous work.

### Findings extracted

- Existing Hebrew parsing covered:
  - `3 סטים 10,8,7`
  - `מאמץ 8 מתוך 10`
  - `בלי כאב`
- It did not cover compact gym shorthand:
  - `3x10`
- Without parsing `3x10`, the bot could treat a useful exercise-level log as a session-only log and lose reps/load evidence.
- Manual probing also found a second real gap:
  - weight `ק״ג` with Hebrew gershayim was not parsed, while ASCII `ק"ג` was.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - parser now accepts Hebrew/English compact set-rep notation:
    - `3x10`
    - `3X10`
    - `3×10`
  - expands `3x10` to reps `[10, 10, 10]`.
  - accepts `ק״ג` as a Hebrew kg token in addition to `ק"ג`, `קג`, `קילו`, and `kg`.
- Updated `backend/tests/test_workout_logs_api.py`:
  - added API parser test for `עשיתי לחיצת חזה 3x10 עם 50 ק״ג. מאמץ 8 מתוך 10, בלי כאב.`
- Updated `backend/tests/test_coach_engine.py`:
  - added chat-level test proving shorthand logs become exercise-level evidence and do not hit the session-only missing-exercise branch.

### Tests and checks

- Focused Hebrew parser tests:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_hebrew_sets_reps_and_weight backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_natural_hebrew_effort_as_rpe backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_hebrew_gym_shorthand_sets_reps_and_effort --basetemp .pytest-tmp-loop65-focused`
  - Result: `3 passed`.
- Broad affected combined run:
  - `python -m pytest backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop65-affected`
  - Result: `121 passed`, then `WinError 10055` socket exhaustion on Windows TestClient setup.
  - Root cause: environment resource exhaustion, not an assertion failure.
- Isolated reported failing test:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_structured_workout_log_uses_exercise_notes_as_safety_source --basetemp .pytest-tmp-loop65-isolate-socket`
  - Result: `1 passed`.
- Full workout log API file:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop65-workout-logs-final`
  - Result: `22 passed`.
- Focused shorthand parser + chat tests:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_hebrew_gym_shorthand_sets_reps_and_effort backend/tests/test_coach_engine.py::test_chat_endpoint_hebrew_shorthand_log_is_exercise_level_evidence --basetemp .pytest-tmp-loop65-chat-shorthand`
  - Result: `2 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop65-coach-final`
  - Result: `101 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew API probe used isolated SQLite and Unicode-escaped text:
  - `עשיתי לחיצת חזה 3x10 עם 50 ק״ג. מאמץ 8 מתוך 10, בלי כאב.`
- First manual result:
  - parsed exercise/reps/RPE/pain correctly
  - failed to capture weight because `ק״ג` was not in the regex.
- After fix:
  - `parse_confidence=high`
  - `rpe=8`
  - `pain_flag=False`
  - `exercise=לחיצת חזה`
  - `sets=3`
  - `reps=[10, 10, 10]`
  - `weight=50 ק״ג`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One regex case, tiny repeated-reps extraction, and two focused tests.
  - No new parser framework, dependency, schema, or abstraction.

### Failures and fixes

- Combined broad test run hit Windows socket exhaustion:
  - `WinError 10055`.
  - Verified by rerunning the reported failing test in isolation: passed.
  - Avoided another combined TestClient-heavy run and ran affected files separately.
- Manual probe found `ק״ג` weight was dropped:
  - fixed by accepting Hebrew gershayim kg notation.

### Next research target

- Loop 66 should inspect workout-log parsing for RIR / `חזרות ברזרבה` in Hebrew logs. RPE is now parsed naturally, but RIR may still be lost from unstructured chat/API logs, weakening progression decisions.

## Loop 66 - Free-text RIR logging must stay exercise-level

### Research target

- Inspect whether unstructured Hebrew/chat workout logs preserve `RIR` / reps-in-reserve evidence.
- Keep this narrow:
  - do not add schema until the product has a real top-level session RIR use case.
  - preserve RIR when the parser can attach it to a concrete exercise result.

### Sources checked

- Stronger by Science / Eric Helms, "The Science of Autoregulation":
  - https://www.strongerbyscience.com/autoregulation/
  - Key extraction: RIR-based RPE anchors effort to how many more reps could be performed before failure, so it belongs closest to the set/exercise evidence.
- Health summary of the 2026 ACSM resistance-training position stand:
  - https://www.health.com/5-things-to-know-from-the-new-strength-training-guidelines-11930807
  - Key extraction: the updated ACSM framing emphasizes consistency, avoiding routine failure, using a few reps in reserve, and matching loading/progression to the user's goal.
  - Cited underlying paper in article: Currier BS, D'Souza AC, Singh MAF, et al. ACSM position stand, Med Sci Sports Exerc. 2026;58(4):851-872.
- Hebrew / Israeli web search attempted:
  - searched for `RIR`, `חזרות ברזרבה`, and `אימון כוח` combinations.
  - Result this loop: no reliable accessible Hebrew/Israeli source returned by the search tool for RIR terminology. Keep broad Israeli coach/source expansion active in later loops.

### Rules extracted

- RIR is not just generic effort; it is reps left before failure for a specific set/exercise.
- If the user logs:
  - `RIR 2`
  - `2 reps in reserve`
  - `2 חזרות ברזרבה`
  - `נשארו לי 2 חזרות`
  then the bot should store that as exercise-level evidence when the exercise was parsed.
- If the user says only `RIR 2` with no exercise/reps, do not invent exercise evidence or add a schema column. Keep needing the missing exercise context in later coaching.
- This supports progression decisions without guessing:
  - clean exercise data + RIR can inform future load decisions.
  - session-only RIR should not trigger precise progression.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - added `_parse_rir()`.
  - supports English `RIR 2` / `2 reps in reserve`.
  - supports Hebrew `2 חזרות ברזרבה`, `נשארו לי 2 חזרות`, `נותרו 2 חזרות`, `השארתי 2 חזרות`.
  - attaches parsed RIR to each parsed exercise result.
  - marks parse confidence `high` when exercise results have either RPE or RIR.
- Updated `backend/tests/test_workout_logs_api.py`:
  - added API test for Hebrew free-text RIR with `3x10`, `ק״ג`, no pain.
- Updated `backend/tests/test_coach_engine.py`:
  - added chat-route test proving a Hebrew RIR workout log is saved as exercise-level evidence and does not fall into the missing-exercise branch.

### Tests and checks

- Focused RIR regressions:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_hebrew_rir_as_exercise_level_evidence backend/tests/test_coach_engine.py::test_chat_endpoint_hebrew_rir_log_is_exercise_level_evidence --basetemp .pytest-tmp-loop66-focused`
  - Result: `2 passed`.
- Full workout log API file:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop66-workout-logs`
  - Result: `23 passed`.
- Full coach engine file:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop66-coach`
  - Result: `102 passed`.
- Final focused rerun after Ponytail cleanup:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_hebrew_rir_as_exercise_level_evidence backend/tests/test_coach_engine.py::test_chat_endpoint_hebrew_rir_log_is_exercise_level_evidence --basetemp .pytest-tmp-loop66-focused-final`
  - Result: `2 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew chat probe through `/api/chat` with Unicode-escaped text:
  - `תעד אימון: עשיתי לחיצת חזה 3x10 עם 50 ק״ג, RIR 2, בלי כאב.`
- Result:
  - `status_code=200`
  - `provider_status=local_tool`
  - `safety_flagged=False`
  - missing-exercise phrase: `False`
  - saved log:
    - `status=completed`
    - `rpe=None`
    - `pain_flag=False`
    - `exercise=\u05dc\u05d7\u05d9\u05e6\u05ea \u05d7\u05d6\u05d4`
    - `weight=50 \u05e7\u05f4\u05d2`
    - `rir=2`

### Ponytail Review

- Initial finding applied:
  - shrink repeated `exercise_results[0]` assertions in the two new tests into a local `result` variable.
- Final result:
  - Lean already. Ship.
- Rationale:
  - One small parser helper, no schema migration, no new abstraction, no dependency.
  - RIR remains tied to actual parsed exercise evidence, which is the product behavior needed now.

### Failures and fixes

- No assertion failures.
- Console rendered Hebrew as mojibake in one manual print, so the check was repeated with `unicode_escape` output to verify actual stored codepoints.

### Next research target

- Loop 67 should inspect whether plan progression logic actually uses stored exercise-level `rir`, or whether it currently relies only on top-level RPE and pain status. If RIR is stored but ignored, add the smallest safe progression rule that uses RIR without over-claiming precision.

## Loop 67 - Use exercise-level RIR in progression without guessing

### Research target

- Determine whether stored `rir` actually affects progression decisions.
- Preserve the product rule:
  - pain and missed/partial logs beat progression.
  - RIR should help only when attached to real exercise evidence.
  - do not create precise load math from a subjective estimate.

### Sources checked

- Stronger by Science / Eric Helms, "The Science of Autoregulation":
  - https://www.strongerbyscience.com/autoregulation/
  - Key extraction: RIR/RPE is a practical autoregulation input, but it is still a subjective estimate. Use it to make small decisions, not exact predictions.
- Health summary of the 2026 ACSM resistance-training position stand:
  - https://www.health.com/5-things-to-know-from-the-new-strength-training-guidelines-11930807
  - Key extraction: current guidance emphasizes sustainable progression, consistency, and keeping a few reps in reserve rather than routine failure.
- Men's Health trainer/media source, "How to Use Reps in Reserve (RIR) to Build More Muscle":
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/
  - Key extraction: common coaching language frames about 2 reps in reserve as a practical target; if work is clearly too easy, adjust load rather than chasing random extra reps.
- Women's Health trainer/media source, "Want Better Gains? It's Time to Start Tracking Your Reps in Reserve":
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
  - Key extraction: RIR is commonly explained as reps left before form failure and used to manage effort, fatigue, and consistency.
- Hebrew / Israeli search:
  - searched again for `RIR`, `חזרות ברזרבה`, and Israeli coach/trainer phrasing.
  - Result this loop: search tool did not return a reliable Israeli source worth encoding into product rules. Keep this as an open research target.

### Existing-code finding

- `WorkoutLog.exercise_results[*].rir` existed and Loop 66 made free-text logs preserve it.
- `TrainingAdaptationService._result_supports_progression()` still required RPE, so a clean RIR-only log was ignored.
- Manual chat probe found a second real issue:
  - `/api/chat` used stripped `intent.payload_text` to decide whether a workout log targeted the active plan.
  - For `תעד אימון: ...`, the command phrase was stripped before `_text_log_targets_next_workout()`, so the log saved with `workout_id=None`.
  - Because `/api/workouts/next` only adapts from current-plan workout IDs, the RIR evidence was invisible.

### Rules extracted

- RIR 1-3 on a completed exercise with reps/sets can support a small progression candidate.
- RIR 0 means the set was at/near failure:
  - do not progress.
  - treat as high effort / recovery-needed unless pain or adherence signals already take priority.
- RIR without exercise evidence should not drive progression.
- RIR should not override:
  - pain flags
  - skipped/partial/modified status
  - missing exercise/reps evidence
  - high RPE when both RPE and RIR are present.

### Changes made

- Updated `backend/app/services/training_adaptation_service.py`:
  - `_result_supports_progression()` now accepts completed exercise evidence when RIR is in the conservative 1-3 range even if top-level/session RPE is missing.
  - added high-effort detection for exercise-level RPE >= 9 or RIR <= 0.
  - zero-RIR logs now produce `recovery_needed` and exercise adjustment `reduce_or_hold`.
- Updated `backend/app/services/coach_engine.py`:
  - `_handle_tool_intent()` now receives `raw_text` as well as stripped `payload_text`.
  - workout-log binding uses `raw_text` to decide whether the log targets the active next workout.
  - `_text_log_targets_next_workout()` now recognizes natural Hebrew workout-log commands:
    - `תעד אימון`
    - `לתעד אימון`
    - `רשום אימון`
    - `רשמתי אימון`
    - `סיימתי אימון`
    - `עשיתי אימון`
- Updated `backend/tests/test_training_adaptation_service.py`:
  - added RIR-only progression test.
  - added RIR 0 recovery test.
- Updated `backend/tests/test_workout_logs_api.py`:
  - added API-level free-text Hebrew RIR -> next-workout progression test.
- Updated `backend/tests/test_coach_engine.py`:
  - added chat-level Hebrew RIR log -> active workout binding -> next-workout progression test.

### Tests and checks

- Initial focused Loop 67 tests:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_exercise_rir_without_session_rpe_for_progression backend/tests/test_training_adaptation_service.py::test_training_adaptation_treats_zero_rir_as_recovery_need backend/tests/test_workout_logs_api.py::test_next_workout_uses_free_text_hebrew_rir_for_progression --basetemp .pytest-tmp-loop67-focused`
  - Result: `3 passed`.
- Full adaptation service:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop67-adaptation`
  - Result: `11 passed`.
- Full workout log API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop67-workout-logs`
  - Result: `24 passed`.
- Full dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop67-dashboard`
  - Result: `9 passed`.
- Full coach engine before chat-binding bug fix:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop67-coach`
  - Result: `102 passed`.
- Focused rerun after chat-binding fix:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_exercise_rir_without_session_rpe_for_progression backend/tests/test_training_adaptation_service.py::test_training_adaptation_treats_zero_rir_as_recovery_need backend/tests/test_workout_logs_api.py::test_next_workout_uses_free_text_hebrew_rir_for_progression backend/tests/test_coach_engine.py::test_chat_endpoint_hebrew_rir_log_targets_next_workout_for_progression --basetemp .pytest-tmp-loop67-focused3`
  - Result: `4 passed`.
- Full affected files after chat-binding fix:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop67-adaptation-final`
  - Result: `11 passed`.
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop67-workout-logs-final`
  - Result: `24 passed`.
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop67-dashboard-final`
  - Result: `9 passed`.
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop67-coach-final`
  - Result: `103 passed`.
- Final focused rerun after naming cleanup:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_exercise_rir_without_session_rpe_for_progression backend/tests/test_training_adaptation_service.py::test_training_adaptation_treats_zero_rir_as_recovery_need backend/tests/test_workout_logs_api.py::test_next_workout_uses_free_text_hebrew_rir_for_progression backend/tests/test_coach_engine.py::test_chat_endpoint_hebrew_rir_log_targets_next_workout_for_progression --basetemp .pytest-tmp-loop67-focused-final`
  - Result: `4 passed`.
- Full adaptation service after final rename:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop67-adaptation-postrename`
  - Result: `11 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew chat flow:
  - create one-day beginner gym plan.
  - send `/api/chat`:
    - `תעד אימון: עשיתי לחיצת חזה 3x10 עם 50 ק״ג, נשארו לי 2 חזרות ברזרבה, בלי כאב.`
- First manual result before chat-binding fix:
  - `saved_rir=2`
  - `saved_workout_id=None`
  - next workout stayed `maintain`
  - Root cause: active-workout targeting used stripped payload, not raw command text.
- Final manual result:
  - `saved_workout_id=1`
  - `saved_rpe=None`
  - `saved_rir=2`
  - `saved_exercise=\u05dc\u05d7\u05d9\u05e6\u05ea \u05d7\u05d6\u05d4`
  - `load_signal=progress_candidate`
  - `progress_evidence=exercise_log`
  - `execution_load_signal=progress_candidate`

### Ponytail Review

- Finding applied:
  - rename `high_rir_effort` / `_latest_log_has_near_failure_rir()` because the helper also catches high exercise-level RPE. Replacement: `high_exercise_effort` / `_latest_log_has_high_exercise_effort()`.
- Final result:
  - Lean already. Ship.
- Rationale:
  - No schema change.
  - No new progression engine.
  - The rule is one small extension to existing adaptation logic and one raw-vs-payload fix in chat binding.

### Failures and fixes

- Focused chat-binding test initially failed:
  - expected `saved_log.workout_id == workout_id`
  - actual `saved_log.workout_id is None`.
- Root cause investigation:
  - `_text_log_targets_next_workout()` returned `True` when called with the raw message.
  - actual chat path passed stripped `intent.payload_text`, where `תעד אימון:` had been removed.
  - fixed at the source by passing `raw_text` to `_handle_tool_intent()` and using it only for active-workout targeting.

### Next research target

- Loop 68 should inspect whether dashboard and coach response copy clearly explains RIR-based progression in Hebrew. The data path now works, but user-facing language may still say only RPE and miss the actual RIR evidence.

## Loop 68 - Surface RIR evidence in Hebrew product copy

### Research target

- Verify whether the user-facing surfaces explain RIR-based progression:
  - immediate chat response after logging workout
  - `/api/workouts/next` execution note
  - dashboard `next_recommended_action`
- Avoid building new UI or metadata unless the existing surfaces cannot carry the explanation.

### Sources checked

- Stronger by Science / Eric Helms, "The Science of Autoregulation":
  - https://www.strongerbyscience.com/autoregulation/
  - Product extraction: RIR is understandable to users when explained as reps left before failure. The bot should name the user's actual logged effort signal.
- Health summary of 2026 ACSM position stand:
  - https://www.health.com/5-things-to-know-from-the-new-strength-training-guidelines-11930807
  - Product extraction: the recommendation should keep the progression small and tie it to sustainable effort, not imply exact precision.
- Men's Health and Women's Health RIR explainers:
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
  - Product extraction: common coach language says RIR is a practical effort gauge. User copy can say `RPE/RIR בשליטה` without a long physiology lecture.

### Existing-code finding

- After Loop 67, the data path worked:
  - free-text RIR saved as `exercise_results[*].rir`.
  - RIR 1-3 could drive `progress_candidate`.
  - chat logs could bind to active workout.
- But the user-facing copy still had gaps:
  - generic next-workout progression note said only `אפשר להוסיף חזרה אחת...`
  - dashboard action used generic `next_adjustment`, so it did not say RIR was the evidence.
  - chat response for a RIR-only log told the user to log RPE next time instead of acknowledging `RIR 2`.

### Rules extracted

- If RIR drove or supported the decision, the product should say so briefly.
- Do not over-explain:
  - one sentence is enough.
  - preserve the next action.
- Do not imply exact loading math:
  - say small progression in one variable.
  - keep `לא לנחש`.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - generic small-progression execution note now says the last log showed `RPE/RIR` in control.
- Updated `backend/app/services/dashboard_service.py`:
  - `next_workout` summary now includes `progress_evidence`.
  - dashboard `next_recommended_action` has a specific branch for exercise-log progression:
    - says the last log included reps and `RPE/RIR` in control.
    - still says to document RPE/pain/completion and not guess.
- Updated `backend/app/services/coach_engine.py`:
  - added `_first_logged_rir()`.
  - RIR-only workout logs now get specific responses:
    - RIR 0: do not progress, keep/reduce.
    - RIR 1-3: small progression is allowed.
    - RIR above 3: repeat and aim for RIR 1-3 before larger increases.
- Updated tests:
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_dashboard_api.py`
  - `backend/tests/test_coach_engine.py`

### Tests and checks

- Focused Loop 68 tests:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_next_workout_uses_free_text_hebrew_rir_for_progression backend/tests/test_dashboard_api.py::test_dashboard_surfaces_rir_based_progression_evidence backend/tests/test_coach_engine.py::test_chat_endpoint_hebrew_rir_log_targets_next_workout_for_progression --basetemp .pytest-tmp-loop68-focused`
  - Result: `3 passed`.
- Full workout log API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop68-workout-logs`
  - Result: `24 passed`.
- Full dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop68-dashboard`
  - Result: `10 passed`.
- Full coach engine:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop68-coach`
  - Result: `103 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew flow:
  - create one-day beginner gym plan.
  - chat log:
    - `תעד אימון: עשיתי לחיצת חזה 3x10 עם 50 ק״ג, נשארו לי 2 חזרות ברזרבה, בלי כאב.`
- Verified:
  - `chat_has_RIR_2=True`
  - `chat_has_RPE_RIR=True`
  - `saved_workout_id=1`
  - `saved_rir=2`
  - `next_execution_has_RPE_RIR=True`
  - `dashboard_has_RPE_RIR=True`
  - `dashboard_progress_evidence=exercise_log`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - No schema change.
  - No new dashboard model layer.
  - One helper to read logged RIR and three small copy assertions.

### Failures and fixes

- No assertion failures in Loop 68.
- No manual probe failures.

### Next research target

- Loop 69 should inspect whether RIR 0 / near-failure logs are visible and conservative in chat, next-workout, and dashboard copy. The internal adaptation now treats RIR 0 as recovery-needed, but the user-facing language may need the same clarity.

## Loop 69 - Make RIR 0 visibly conservative

### Research target

- Check whether near-failure logs (`RIR 0`) stay conservative across:
  - immediate chat response
  - `/api/workouts/next`
  - dashboard next action
- Avoid turning failure training into a default progression pattern.

### Sources checked

- Search target:
  - training to failure, RIR 0, fatigue, recovery, and Hebrew RIR/failure terminology.
- Men's Health RIR explainer:
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/
  - Key extraction: common coaching language recommends leaving about 2 reps in reserve rather than defaulting to failure.
- Women's Health RIR explainer:
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
  - Key extraction: RIR 0 is usually not necessary on every set and can increase fatigue; RIR is useful for managing effort and consistency.
- General failure-training search result:
  - training-to-failure sources broadly define failure as inability to complete another rep and frame it as a high-intensity tool, not a default beginner progression rule.
- Israeli/Hebrew search:
  - again weak for reliable RIR-specific sources in this pass. Do not encode low-quality Hebrew-source claims into rules.

### Existing-code finding

- Loop 67 already made `RIR 0` produce:
  - `load_signal=recovery_needed`
  - exercise adjustment reason `near_failure_rir`.
- Loop 68 made controlled RIR visible, but near-failure copy still needed checking.
- The chat branch already said `RIR 0` is close to failure and says not to add reps.
- `/api/workouts/next` and dashboard recovery copy were still mostly generic and could hide why the system reduced load.

### Rules extracted

- RIR 0 means the set was at or near failure.
- For this product:
  - do not progress from RIR 0.
  - recommend keeping or reducing load/volume.
  - ask the user to aim for 2-3 RIR on the next effort.
  - keep pain and safety rules first.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - recovery-needed execution note now says the last effort was high by `RPE/RIR`.
  - still recommends reducing volume/load and leaving 2-3 RIR.
- Updated `backend/app/services/dashboard_service.py`:
  - `next_workout` summary now includes `signals`.
  - dashboard next action has a specific recovery branch when signals include `RPE/RIR`.
  - copy says the last log was close to failure and recommends lowering volume/load.
- Updated tests:
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_dashboard_api.py`
  - `backend/tests/test_coach_engine.py`

### Tests and checks

- Focused Loop 69 tests:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_next_workout_treats_free_text_zero_rir_as_recovery_needed backend/tests/test_dashboard_api.py::test_dashboard_surfaces_zero_rir_recovery_evidence backend/tests/test_coach_engine.py::test_chat_endpoint_zero_rir_log_is_conservative --basetemp .pytest-tmp-loop69-focused`
  - Result: `3 passed`.
- Full workout log API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop69-workout-logs`
  - Result: `25 passed`.
- Full dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop69-dashboard`
  - Result: `11 passed`.
- Full coach engine:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop69-coach`
  - Result: `104 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew zero-RIR flow:
  - create one-day beginner gym plan.
  - chat log:
    - `תעד אימון: עשיתי לחיצת חזה 3x10, RIR 0, בלי כאב.`
- Verified:
  - `chat_has_RIR_0=True`
  - `chat_has_no_add=True`
  - `saved_rir=0`
  - `next_load_signal=recovery_needed`
  - `next_reason=near_failure_rir`
  - `next_execution_has_RPE_RIR=True`
  - `dashboard_has_RPE_RIR=True`
  - `dashboard_load_signal=recovery_needed`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One recovery-note edit, one dashboard branch, and three tests.
  - No new schema, no new adapter, no failure-training feature branch.

### Failures and fixes

- No assertion failures.
- No manual probe failures.

### Next research target

- Loop 70 should inspect whether high-RIR / too-easy logs (`RIR 4+`) produce a useful but not over-aggressive action. Current logic does not treat RIR above 3 as progression evidence; the bot may need to say "aim closer to RIR 1-3" rather than silently maintaining.

## Loop 70 - Treat high RIR as underload, not silence

### Research target

- Check whether `RIR 4+` should be:
  - maintain only
  - small progression
  - or a separate "too easy / underloaded" guidance path.
- Keep the rule conservative:
  - no large jumps.
  - aim toward RIR 1-3.
  - preserve pain and failure safeguards.

### Sources checked

- Men's Health RIR explainer:
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/
  - Key extraction: if the set is clearly too easy, the common coaching answer is to increase resistance rather than chase arbitrary extra reps.
- Women's Health RIR explainer:
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
  - Key extraction: RIR 5 is a sign to reevaluate load; common practical target is around 2-3 RIR for many working sets.
- Stronger by Science / autoregulation framing:
  - https://www.strongerbyscience.com/autoregulation/
  - Key extraction: RIR is subjective, so use it for small autoregulated changes rather than exact load calculations.
- Hebrew/Israeli search:
  - still no reliable RIR-specific Israeli source found in this pass.

### Existing-code finding

- After Loop 67, `_result_supports_progression()` only accepted RIR 1-3.
- RIR 4+ produced no progress evidence:
  - load signal could stay `maintain`.
  - chat did say there was too much reserve, but next-workout/dashboard behavior did not carry a clear action.
- That is too quiet: a user who logs `RIR 5` did useful tracking and needs one clear next action.

### Rules extracted

- RIR 4+ is not a failure signal.
- It usually means the set was underloaded or too easy for the target.
- The next action should be:
  - increase load slightly, or slow tempo/control.
  - aim for RIR 1-3.
  - do not jump aggressively.
- If pain, skipped/partial status, or RIR 0 exists, those still take priority.

### Changes made

- Updated `backend/app/services/training_adaptation_service.py`:
  - added `_result_underloaded()`.
  - high RIR now creates exercise adjustment:
    - `adjustment=small_progression`
    - `reason=high_rir_underload`
    - next action: small load increase or slower tempo toward `RIR 1-3`.
  - `_result_supports_progression()` now blocks only `RIR <= 0`; positive RIR can support a small progression candidate.
- Updated `backend/app/services/workout_service.py`:
  - execution plan preserves the specific `high_rir_underload` next action instead of overwriting it with generic "add one rep" copy.
- Updated `backend/app/services/dashboard_service.py`:
  - dashboard next action recognizes `high_rir_underload` and tells the user to raise load slightly or slow tempo toward `RIR 1-3`.
- Updated `backend/app/services/coach_engine.py`:
  - immediate RIR > 3 response now recommends a small load/tempo adjustment toward `RIR 1-3`, without a large jump.
- Updated tests:
  - `backend/tests/test_training_adaptation_service.py`
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_dashboard_api.py`
  - `backend/tests/test_coach_engine.py`

### Tests and checks

- Initial focused Loop 70 tests:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_high_rir_as_underload_progression backend/tests/test_workout_logs_api.py::test_next_workout_uses_free_text_high_rir_for_underload_progression backend/tests/test_dashboard_api.py::test_dashboard_surfaces_high_rir_underload_guidance backend/tests/test_coach_engine.py::test_chat_endpoint_high_rir_log_recommends_small_underload_adjustment --basetemp .pytest-tmp-loop70-focused`
  - Result: `3 passed, 1 failed`.
  - Failure was an assertion expecting the noun `קפיצה`; product copy used the actual phrase `לא לקפוץ הרבה`.
- Focused rerun after test fix:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_high_rir_as_underload_progression backend/tests/test_workout_logs_api.py::test_next_workout_uses_free_text_high_rir_for_underload_progression backend/tests/test_dashboard_api.py::test_dashboard_surfaces_high_rir_underload_guidance backend/tests/test_coach_engine.py::test_chat_endpoint_high_rir_log_recommends_small_underload_adjustment --basetemp .pytest-tmp-loop70-focused2`
  - Result: `4 passed`.
- Full adaptation service:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop70-adaptation`
  - Result: `12 passed`.
- Full workout log API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop70-workout-logs`
  - Result: `26 passed`.
- Full dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop70-dashboard`
  - Result: `12 passed`.
- Full coach engine:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop70-coach`
  - Result: `105 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew high-RIR flow:
  - create one-day beginner gym plan.
  - chat log:
    - `תעד אימון: עשיתי <exercise> 3x10, RIR 5, בלי כאב.`
- Verified:
  - `chat_has_RIR_5=True`
  - `chat_has_RIR_target=True`
  - `chat_has_small_load=True`
  - `saved_rir=5`
  - `next_load_signal=progress_candidate`
  - `next_reason=high_rir_underload`
  - execution note says to raise load slightly or slow tempo toward `RIR 1-3`, not to jump a lot.
  - dashboard action includes `RIR 1-3` and `לא לנחש`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One service branch, one dashboard branch, one execution-copy preservation branch.
  - Reuses existing `exercise_adjustments`; no new planner layer or schema.

### Failures and fixes

- One focused test assertion was too specific:
  - expected `קפיצה`.
  - actual copy: `לא לקפוץ הרבה`.
  - fixed the assertion to check the actual conservative phrase.

### Next research target

- Loop 71 should inspect whether RIR/RPE evidence is represented in the knowledge center rules, not only service behavior. If the bot's knowledge center still describes progression only as RPE-based, update it so plan-building and response rules consistently mention RIR 0, RIR 1-3, and RIR 4+.

## Loop 71 - Knowledge center RIR/RPE bands

### Research target

- Align the bot's knowledge center with the runtime RIR behavior built in Loops 66-70.
- Keep the provider context compact so workout prompts inherit the rule without sending full protocol tables.

### Sources checked

- Stronger by Science / Helms autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- Men's Health, `How to Use Reps in Reserve (RIR) to Build More Muscle`:
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/
- Women's Health, `Want Better Gains? It's Time to Start Tracking Your Reps in Reserve`:
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- Health summary of the 2026 ACSM resistance-training position stand:
  - https://www.health.com/5-things-to-know-from-the-new-strength-training-guidelines-11930807
- Hebrew/Israeli search attempts:
  - searched for `חזרות ברזרבה`, `RIR אימון`, `כשל שריר`, and Israeli coach/source variants.
  - no reliable accessible Hebrew RIR-specific source found in this loop, so I did not add a weak local source as evidence.

### Findings extracted

- RIR should be treated as a practical effort signal, not an exact measurement.
- The bot needs explicit bands:
  - `RIR 0`: failure or near-failure, do not progress; bias recovery/maintain/reduce.
  - `RIR 1-3`: normal controlled working range for many strength/hypertrophy users.
  - `RIR 4+`: too much reserve/underloaded; use a small load increase or slower tempo toward `RIR 1-3`, not a big jump.
- Beginners, new exercises, pain, or unstable technique need more reserve and more conservative interpretation.

### Changes made

- Updated `backend/app/services/coaching_knowledge.py`:
  - `volume_progression_protocols.rir_rpe_autoregulation` now includes explicit `RIR 0`, `RIR 1-3`, and `RIR 4+` progression interpretation.
  - `load_prescription_protocols.rir_rpe_calibration` now includes the same log-interpretation bands.
  - compact `volume_progression_summary` now includes `RIR 0`, `1-3`, and `4+`.
  - compact `load_prescription_summary` now keeps `1-3` and beginner/new-exercise `2-4` RIR targets.
- Updated `backend/tests/test_coaching_knowledge.py`:
  - added protocol-level assertions for the RIR bands.
  - added provider-context assertions so compact workout prompts keep the bands.

### Tests and checks

- Focused knowledge tests:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_volume_progression_protocols backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_load_prescription_protocols backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_load_prescription_summary_for_workouts_only backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_volume_progression_summary_for_workouts_only --basetemp .pytest-tmp-loop71-focused`
  - Result: `4 passed`.
- Full knowledge file, first run:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop71-knowledge`
  - Result: `109 passed, 3 failed`.
  - Cause: provider context grew to `8368` chars, above the `8350` budget.
- Budget fix:
  - shortened compact provider summary copy without removing the RIR bands.
- Focused rerun:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_volume_progression_protocols backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_load_prescription_protocols backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_load_prescription_summary_for_workouts_only backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_volume_progression_summary_for_workouts_only --basetemp .pytest-tmp-loop71-focused-2`
  - Result: `4 passed`.
- Full knowledge rerun:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop71-knowledge-2`
  - Result: `112 passed`.
- Manual provider-context probe:
  - `CoachingKnowledgeService().for_provider_context("workout_plan", query="RIR 5 קל מדי מה להעלות?")`
  - Verified `volume_progression_summary` contains `RIR 0`, `1-3`, and `4+`.
  - Verified compact context length is `8343`, under the `8350` budget.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - This loop adds one missing knowledge rule and narrow regression assertions.
  - No new schema, no new provider layer, no duplicate planner logic.
  - The only bloat risk was provider prompt length; the failing budget test forced the summary back under budget.

### Failures and fixes

- Full knowledge tests failed on prompt budget:
  - provider context length was `8368`, limit is `<8350`.
  - fixed by shortening the compact RIR summary strings.

### Next research target

- Loop 72 should broaden beyond RIR into coach-facing progression language from Israeli and global coaching sources:
  - how coaches phrase "too easy / too hard / just right" in natural user language.
  - whether the bot's Hebrew responses should translate RIR into simpler language when the user does not use the term.
  - inspect chat response paths for overuse of technical `RIR/RPE` terms versus natural Hebrew.

## Loop 72 - Natural Hebrew effort language

### Research target

- Support Hebrew-first workout logs where the user does not know or use `RPE/RIR`.
- Convert natural phrases like `קל מדי`, `כבד מדי`, `בקושי סיימתי`, and `בשליטה` into useful coaching decisions without inventing exact numeric effort.

### Sources checked

- CDC, `How to Measure Physical Activity Intensity`:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Women's Health, `Want Better Gains? It's Time to Start Tracking Your Reps in Reserve`:
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- Women's Health, `If a Workout Feels Easy, Does It Still Count for Strength Gains?`:
  - https://www.womenshealthmag.com/fitness/a71088407/do-easy-workouts-build-strength/
- Men's Health, `How to Use Reps in Reserve (RIR) to Build More Muscle`:
  - https://www.menshealth.com/fitness/a65935301/reps-in-reserve-to-build-more-muscle/
- Business Insider / Jim Stoppani RIR coaching summary:
  - https://www.businessinsider.com/build-more-muscle-less-time-pro-tips-top-exercise-scientist-2026-2
- Israeli/Hebrew source search:
  - searched coach/source variants for `קל מדי`, `כבד מדי`, `קשה מדי`, `נשאר לי מלא כוח`, and `חזרות ברזרבה`.
  - no reliable accessible Hebrew source with a clean RIR-specific mapping was found in this loop.

### Findings extracted

- Beginner-friendly coaching should not force technical `RIR/RPE` reporting before the user has learned it.
- A natural-language effort signal is useful:
  - `קל מדי` / `נשאר לי מלא כוח`: underloaded, progress with a small load/tempo change.
  - `כבד מדי` / `בקושי סיימתי`: too hard, maintain or reduce.
  - `מאתגר אבל בשליטה`: controlled, possible small progression if reps/sets were logged.
- These should be persisted as qualitative signals, not fake numeric RIR or RPE.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - added `_parse_qualitative_effort()`.
  - stores `effort_signal` on parsed `exercise_results` as:
    - `underloaded`
    - `too_hard`
    - `controlled`
  - `parse_confidence=high` when exercise results include qualitative effort evidence.
  - preserves the existing numeric RPE/RIR behavior when the user gives a number.
- Updated `backend/app/services/training_adaptation_service.py`:
  - `underloaded` creates `reason=qualitative_underload` and uses the same small-progression path as high RIR.
  - `too_hard` creates `reason=qualitative_high_effort` and triggers recovery/maintain behavior.
  - `controlled` can support exercise-level progression evidence when reps/sets are logged.
- Updated `backend/app/services/workout_service.py` execution-plan behavior:
  - `qualitative_underload` now gets the specific underload execution note instead of falling back to generic `RPE/RIR בשליטה`.
- Updated `backend/app/services/coach_engine.py`:
  - chat confirmations now respond naturally to `קל מדי`, `כבד מדי`, and `בשליטה`.
- Updated `backend/app/services/coaching_knowledge.py`:
  - Hebrew terminology protocol now says not to force numeric `RPE/RIR` when the user gives natural effort language.
- Updated tests:
  - `backend/tests/test_training_adaptation_service.py`
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_coaching_knowledge.py`

### Tests and checks

- First focused run:
  - wrong knowledge test id, so no tests ran.
- Focused rerun:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_qualitative_underload_without_fake_rir backend/tests/test_training_adaptation_service.py::test_training_adaptation_treats_qualitative_too_hard_as_recovery_need backend/tests/test_workout_logs_api.py::test_workout_log_api_parses_natural_hebrew_controlled_effort backend/tests/test_workout_logs_api.py::test_next_workout_uses_natural_hebrew_underload_without_fake_rir backend/tests/test_coach_engine.py::test_chat_endpoint_natural_hebrew_underload_log_recommends_small_adjustment backend/tests/test_coach_engine.py::test_chat_endpoint_natural_hebrew_too_hard_log_is_conservative backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_hebrew_coach_language_protocols --basetemp .pytest-tmp-loop72-focused-2`
  - Result: `6 passed, 1 failed`.
  - Failure: next-workout execution note did not preserve `qualitative_underload`.
- Focused rerun after fix:
  - same command with `--basetemp .pytest-tmp-loop72-focused-3`
  - Result: `7 passed`.
- Full adaptation service:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop72-adaptation`
  - Result: `14 passed`.
- Full workout log API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop72-workout-logs`
  - Result: `28 passed`.
- Full coach engine:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop72-coach`
  - Result: `107 passed`.
- Full knowledge file:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop72-knowledge`
  - Result: `112 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- First manual probe failed because Hebrew text passed through a PowerShell pipe was corrupted before reaching the app:
  - app correctly returned the unreadable-character guard.
  - no log was saved.
- Reran the manual probe with Unicode escapes and a temporary database.
- Underloaded Hebrew message:
  - `תעד אימון: עשיתי <exercise> 3x10, היה קל מדי ונשאר לי מלא כוח, בלי כאב.`
  - Verified response says to raise a small load or slow tempo.
  - Verified saved `effort_signal=underloaded`.
  - Verified no fake `rir` was saved.
  - Verified next-workout reason is `qualitative_underload`.
- Too-hard Hebrew message:
  - `תעד אימון: עשיתי לחיצת חזה 3x10, היה כבד מדי ובקושי סיימתי, בלי כאב.`
  - Verified response says to keep or reduce load.
  - Verified saved `effort_signal=too_hard`.

### Ponytail Review

- Finding:
  - `backend/app/services/workout_service.py`: shrink duplicate term `בקושי סיימתי את`; `בקושי סיימתי` already matches it.
  - net: `-1` line possible.
- Fix applied:
  - removed the duplicate term.
- Focused post-Ponytail rerun:
  - same focused Loop 72 command with `--basetemp .pytest-tmp-loop72-focused-4`
  - Result: `7 passed`.
- Final Ponytail result after fix:
  - Lean already. Ship.

### Failures and fixes

- Wrong test id on first focused run:
  - fixed by using `test_coaching_knowledge_contains_hebrew_coach_language_protocols`.
- Real integration failure:
  - adaptation reason was `qualitative_underload`, but execution note only checked `high_rir_underload`.
  - fixed by treating both reasons as underload progression.
- Manual Hebrew probe encoding failure:
  - fixed by using Unicode escapes instead of raw Hebrew through PowerShell stdin.

### Next research target

- Loop 73 should inspect whether dashboard copy and weekly summary copy now surface qualitative effort correctly:
  - `underloaded` should not be hidden behind generic `RPE/RIR`.
  - `too_hard` should show a conservative next action.
  - summaries should stay short and Hebrew-natural.

## Loop 73 - Dashboard copy for qualitative effort

### Research target

- Make dashboard next actions reflect qualitative Hebrew effort signals instead of hiding them under generic `RPE/RIR` copy.
- Preserve the dashboard rule: one clear next action, short reason, no shame, no fake precision.

### Sources checked

- CDC, `How to Measure Physical Activity Intensity`:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- TechRadar / Fitbod founder interview on adaptive fitness app feedback:
  - https://www.techradar.com/health-fitness/fitness-apps/its-no-longer-enough-for-an-app-to-tell-you-what-to-do-people-want-to-know-why-fitness-app-fitbods-founder-on-the-reason-behind-the-ai-fitness-boom
- TechRadar summary of app behavior-change features:
  - https://www.techradar.com/health-fitness/fitness-apps/5-fitness-apps-that-can-help-you-stick-to-your-workout-goals-in-2026-according-to-science
- Fitness app harm / overtracking caution:
  - https://www.thetimes.com/life-style/health-fitness/article/fitness-apps-trackers-negative-health-weight-loss-advice-bntzt83t0

### Findings extracted

- Dashboard feedback should explain why the recommendation appears, but not overexplain.
- Self-monitoring is useful only when it leads to a clear, realistic action.
- Rigid metrics can become demotivating; qualitative logs should be respected as useful evidence.
- For CALO BOT this means:
  - `qualitative_underload`: show small load/tempo progression.
  - `qualitative_high_effort`: show maintain/reduce action in natural Hebrew.
  - do not mention `RPE/RIR` in the visible action if the user did not give `RPE/RIR`.

### Changes made

- Updated `backend/app/services/dashboard_service.py`:
  - dashboard underload branch now handles both `high_rir_underload` and `qualitative_underload`.
  - added a separate `qualitative_high_effort` recovery branch:
    - says the last log described effort as too heavy.
    - recommends reducing volume or load.
    - keeps the logging instruction short.
  - restored the generic recovery branch to numeric `RPE/RIR` wording only.
- Updated `backend/tests/test_dashboard_api.py`:
  - added `test_dashboard_surfaces_natural_hebrew_underload_guidance`.
  - added `test_dashboard_surfaces_natural_hebrew_too_hard_recovery_guidance`.
  - tightened the too-hard test to reject generic `RPE/RIR` wording in the qualitative path.

### Tests and checks

- Focused dashboard tests:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_surfaces_natural_hebrew_underload_guidance backend/tests/test_dashboard_api.py::test_dashboard_surfaces_natural_hebrew_too_hard_recovery_guidance backend/tests/test_dashboard_api.py::test_dashboard_surfaces_high_rir_underload_guidance backend/tests/test_dashboard_api.py::test_dashboard_surfaces_zero_rir_recovery_evidence --basetemp .pytest-tmp-loop73-focused`
  - Result: `4 passed`.
- Full dashboard suite:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop73-dashboard`
  - Result: `14 passed`.
- Focused rerun after plain-language split:
  - same focused command with `--basetemp .pytest-tmp-loop73-focused-2`
  - Result: `4 passed`.
- Full dashboard rerun after final cleanup:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop73-dashboard-3`
  - Result: `14 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual dashboard probe with temporary database and Unicode-escaped Hebrew:
  - underloaded log:
    - saved next action says to raise small load or slow tempo toward `RIR 1-3`.
    - reason is `qualitative_underload`.
  - too-hard log:
    - saved next action says the last log described effort as too heavy.
    - recommends lowering volume/load.
    - verified visible action does not contain `RPE/RIR`.
    - reason is `qualitative_high_effort`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Two dashboard reason checks and two tests.
  - No new formatter, no separate dashboard policy layer, no schema change.

### Failures and fixes

- Initial implementation used a generic `RPE/RIR או מאמץ מילולי` phrase.
- That was technically correct but not Hebrew-natural for users who said `כבד מדי`.
- Fixed by adding a qualitative high-effort branch before the generic numeric recovery branch.

### Next research target

- Loop 74 should inspect frontend/dashboard rendering:
  - whether `next_recommended_action` and `next_workout.exercise_adjustments` display clearly in the UI.
  - whether the frontend hides useful next-action evidence.
  - add/update frontend tests if the UI fails to surface the dashboard action.

## Loop 74 - Frontend dashboard rendering and types

### Research target

- Verify that the frontend actually displays the qualitative-effort dashboard action created in Loop 73.
- Avoid adding UI clutter unless the current dashboard hides the user's next action.

### Sources checked

- Reused Loop 73 dashboard/action research:
  - CDC perceived-intensity guidance.
  - adaptive fitness-app feedback examples.
  - app overtracking/shame caution.
- Local UI inspection:
  - `frontend/src/DashboardPanel.tsx`
  - `frontend/src/DashboardPanel.test.tsx`
  - `frontend/src/api.ts`

### Findings extracted

- The dashboard already renders `next_recommended_action` prominently under `פעולה הבאה`.
- It also renders workout name, load-signal label, and first exercise.
- Adding a second visible evidence panel for `exercise_adjustments` would create dashboard clutter right now.
- The real frontend gap was type coverage:
  - backend sends `signals`, `exercise_adjustments`, `progress_evidence`, and `plan_adjustment`.
  - `DashboardState.next_workout` did not type those fields.
  - UI tests therefore could not assert that qualitative effort evidence is present and not leaked raw.

### Changes made

- Updated `frontend/src/api.ts`:
  - `DashboardState.next_workout` now includes:
    - `signals`
    - `exercise_adjustments`
    - `progress_evidence`
    - `plan_adjustment`
- Updated `frontend/src/DashboardPanel.test.tsx`:
  - added a test that renders qualitative high-effort dashboard action.
  - asserts the visible action says `מאמץ כבד מדי`.
  - asserts raw internal reason `qualitative_high_effort` is not rendered.

### Tests and checks

- Focused frontend test:
  - `npm.cmd --prefix frontend test -- --run DashboardPanel.test.tsx`
  - Result: `1 passed`, `4 tests passed`.
- Frontend build/type check:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Local UI code path:
  - `DashboardPanel` renders `dashboard.next_recommended_action` directly.
  - Since backend dashboard action is already natural Hebrew, the current UI surface is sufficient.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Type coverage plus one UI test is enough.
  - A separate evidence panel would be premature and could reduce dashboard clarity.

### Failures and fixes

- No test failures in this loop.

### Next research target

- Loop 75 should inspect `WorkoutsPanel` logging UI:
  - whether users can log qualitative effort without typing free-text chat.
  - whether adding qualitative effort controls is worth it now or too much UI.
  - if not adding controls, ensure the existing free-text note path clearly supports natural Hebrew effort phrases.

## Loop 75 - Structured workout logs and natural Hebrew effort notes

### Research target

- Verify whether the structured workout logging UI can carry natural Hebrew effort feedback without adding another control.
- Decide whether phrases like `קל מדי` and `נשאר לי מלא כוח` should be parsed from exercise notes as qualitative signals.

### Sources checked

- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Stronger by Science / Eric Helms - The Science of Autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- Search pass for Israeli/Hebrew coach language:
  - queries included `חזרות ברזרבה`, `קל מדי אימון מאמן כושר`, `RPE אימון כוח`, and `יומן אימון`.
  - no reliable accessible Hebrew source added a better rule than the existing product language; I did not encode unsupported coach-specific claims.
- Local UI inspection:
  - `frontend/src/WorkoutsPanel.tsx`
  - `frontend/src/WorkoutsPanel.test.tsx`
  - `frontend/src/api.ts`

### Findings extracted

- Perceived effort is valid user input, but it must be anchored and interpreted cautiously.
- Helms's autoregulation guidance supports subjective feedback when it is structured, not treated as vague "train by feel".
- CDC guidance supports user-friendly intensity language and a simple 0-10 effort scale, which backs not forcing every user into technical RPE/RIR terms.
- The existing WorkoutsPanel already has per-exercise notes and general notes.
- Adding chips or a new effort selector now would be UI clutter.
- The useful product slice is:
  - accept natural Hebrew effort in existing notes.
  - persist it as `effort_signal`.
  - do not fabricate numeric `RPE` or `RIR`.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - structured workout logs now parse qualitative effort from exercise notes, request notes, and request text.
  - stores `effort_signal` on the relevant exercise result when phrases indicate underloaded, too hard, or controlled effort.
  - keeps `rir` as `None` when the user did not provide a numeric RIR.
- Updated `backend/tests/test_workout_logs_api.py`:
  - added coverage for structured exercise notes containing `היה קל מדי ונשאר לי מלא כוח`.
  - asserts `effort_signal=underloaded`, no fake `rir`, and `qualitative_underload` adaptation.
- Updated `frontend/src/api.ts`:
  - `WorkoutLog.exercise_results` now types optional `effort_signal`.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - added a UI test proving the existing per-exercise note field submits natural Hebrew effort notes without requiring RPE/RIR.

### Tests and checks

- Focused backend test:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_structured_workout_log_parses_qualitative_effort_from_exercise_notes --basetemp .pytest-tmp-loop75-structured`
  - Result: `1 passed`.
- Focused frontend test:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx -t "submits natural Hebrew effort notes"`
  - Result: `1 passed`, `17 skipped`.
- Full affected backend test file:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop75-workout-logs`
  - Result: `29 passed`.
- Full affected frontend test file:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `18 passed`.
- Frontend build/type check:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual TestClient structured-log probe with Unicode-escaped Hebrew note:
  - note: `היה קל מדי ונשאר לי מלא כוח`
  - verified `effort_signal=underloaded`.
  - verified `rir=null`.
  - verified `load_signal=progress_candidate`.
  - verified first adjustment reason `qualitative_underload`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - No new UI control, no new service layer, no new schema table.
  - The only production change is parsing the existing notes field and typing the returned signal.
  - The frontend test duplicates fetch stubbing because that is the local test style; extracting a shared stub factory for one case would be a bigger abstraction than the change itself.

### Failures and fixes

- First manual probe printed the correct verified values but exited nonzero because Windows held the temporary SQLite file during cleanup.
- Reran with explicit `client.close()` and tolerant temp cleanup.
- Second manual probe exited cleanly.

### Next research target

- Loop 76 should inspect whether recent qualitative effort signals are visible enough in recent workout logs.
- Product question:
  - Should recent logs display natural effort labels like `קל מדי`, `כבד מדי`, `בשליטה`, or is showing only plan adaptation enough?
  - Avoid exposing internal codes like `underloaded` or `qualitative_underload`.

## Loop 76 - Recent workout log visibility for qualitative effort

### Research target

- Decide whether saved qualitative effort signals should be visible in recent workout logs.
- Keep the UI Hebrew-natural and avoid exposing internal reason/signal codes.

### Sources checked

- Shalawadi et al. 2026 - Who Gets to Interpret the Workout? User Tensions with AI-Generated Fitness Feedback:
  - https://arxiv.org/abs/2604.23830
- Stronger by Science / Eric Helms - The Science of Autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Local UI inspection:
  - `frontend/src/WorkoutsPanel.tsx`
  - `frontend/src/WorkoutsPanel.test.tsx`

### Findings extracted

- AI fitness feedback should preserve user context and agency instead of reducing every session to numeric judgment.
- Autoregulation works best when subjective feedback is structured and repeatable.
- Existing recent-log rendering showed exercise name, reps, and weight, but hid `effort_signal`.
- Hiding the signal makes the saved qualitative data less useful to the user.
- Showing internal codes like `underloaded` would be bad product UX.
- Smallest useful UI change:
  - append a natural Hebrew label to the existing exercise result text.
  - map only known signals.
  - suppress unknown signals instead of leaking raw codes.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - `formatLoggedExercise()` now appends a natural effort label.
  - `underloaded` -> `קל מדי`.
  - `too_hard` -> `כבד מדי`.
  - `controlled` -> `בשליטה`.
  - unknown values render as empty text.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - recent workout log fixture includes `effort_signal: underloaded`.
  - test asserts recent log displays `Goblet squat 10 20kg קל מדי`.
  - test asserts raw `underloaded` is not rendered.

### Tests and checks

- Focused recent-log UI test:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx -t "loads persisted recent workout logs"`
  - Result: `1 passed`, `17 skipped`.
- Full affected frontend test file:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `18 passed`.
- Frontend build/type check:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Local rendering path:
  - last saved log and recent logs both use `formatLoggedExercise()`.
  - The same label mapping therefore applies immediately after saving and in persisted history.
  - Unknown codes are dropped by the formatter.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Three-label formatter, one test assertion.
  - No new component, no new styling, no new tracking controls.
  - A separate "effort badge" component would be premature.

### Failures and fixes

- No test failures in this loop.

### Next research target

- Loop 77 should inspect whether coach chat confirmations and dashboard/recent-log labels use the same Hebrew wording.
- Product question:
  - Should the wording live in a shared frontend/backend mapping, or is duplication acceptable while only three labels exist?

## Loop 77 - Effort wording consistency and frontend copy cleanup

### Research target

- Check whether the natural effort labels should be centralized across frontend and backend.
- Verify whether any active workout UI copy conflicts with the Hebrew-first, concise coach tone.

### Sources checked

- TechRadar / Fitbod interview on AI fitness transparency and explaining why recommendations change:
  - https://www.techradar.com/health-fitness/fitness-apps/its-no-longer-enough-for-an-app-to-tell-you-what-to-do-people-want-to-know-why-fitness-app-fitbods-founder-on-the-reason-behind-the-ai-fitness-boom
- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?:
  - https://arxiv.org/abs/2604.23830
- Search pass on UI wording:
  - `UX writing consistency terminology labels user interface concise copy`
  - `plain language interface labels user codes avoid jargon UX writing`
- Local code inspection:
  - `backend/app/services/coach_engine.py`
  - `backend/app/services/dashboard_service.py`
  - `backend/app/services/workout_service.py`
  - `frontend/src/WorkoutsPanel.tsx`
  - `frontend/src/formatters.ts`

### Findings extracted

- Users need transparent explanations, but not every surface needs identical sentence wording.
- Chat and dashboard should explain the next action.
- Recent logs should use compact labels.
- A shared frontend/backend text registry for only three labels would be premature.
- Real drift found:
  - `frontend/src/formatters.ts` used five em dashes in rendered adjustment explanations.
  - That copy is visible in the WorkoutsPanel execution-plan path.
  - Replacing those with simple hyphen separators improves consistency without changing behavior.

### Changes made

- Updated `frontend/src/formatters.ts`:
  - replaced five visible em dashes with normal ` - ` separators.
  - left existing adjustment explanation logic unchanged.
- No shared label registry added.
- No backend change in this loop.

### Tests and checks

- Full affected frontend test file:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `18 passed`.
- Frontend build/type check:
  - `npm.cmd run build`
  - Result: passed.
- Unicode punctuation check:
  - inline Python scan of `frontend/src/formatters.ts`
  - Result: `em_dash=0`, `en_dash=0`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Local code path:
  - `WorkoutsPanel` imports `formatAdjustmentExplanation`.
  - The cleaned strings are shown next to adjusted exercises.
  - The meaning of each explanation stayed the same.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Rejected shared label/text registry.
  - Five-character-class cleanup in existing copy is smaller than adding infrastructure.
  - Tests and build covered the active UI path.

### Failures and fixes

- No test failures in this loop.

### Next research target

- Loop 78 should inspect generated workout plans for whether tracking guidance tells users how to log qualitative effort.
- Product question:
  - The app can parse and display `קל מדי`, `כבד מדי`, and `בשליטה`; do generated plans explicitly teach users to log those phrases when they do not know RPE/RIR?

## Loop 78 - Generated plan guidance for qualitative effort logging

### Research target

- Check whether generated workout plans tell users how to log natural effort phrases.
- Keep the guidance short and avoid adding another checklist item if the existing tracking line can carry it.

### Sources checked

- Stronger by Science / Eric Helms - The Science of Autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- Women's Health - Reps in Reserve explainer:
  - https://www.womenshealthmag.com/fitness/a71141972/reps-in-reserve/
- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Search pass:
  - `beginner lifters RPE RIR accuracy repetitions in reserve familiarization resistance training`
  - `RIR scale beginners resistance training accuracy rating perceived exertion review`
- Local code inspection:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/tests/test_workout_plans_api.py`

### Findings extracted

- RPE/RIR are useful, but beginners may need plain-language anchors while learning to estimate effort.
- The app now parses qualitative effort, but generated plans only told users to log `RPE` and `RIR`.
- Adding a new guidance row would risk pushing other capped guidance out of `tracking_guidance`.
- Smallest useful change:
  - fold the natural phrases into the existing first tracking instruction.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - first tracking guidance item now says users can log `RPE כללי או מאמץ מילולי כמו קל מדי/כבד מדי/בשליטה`.
  - added a narrow neutralizer repair so `כבד מדי` is not changed to `לכבד מדי`.
- Updated `backend/tests/test_workout_plans_api.py`:
  - generated plan assertion now requires `מאמץ מילולי`, `קל מדי`, and `כבד מדי`.
  - added a negative assertion that `לכבד מדי` never appears in tracking guidance.

### Tests and checks

- Focused API test:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_conservative_assumptions_for_minimal_prompt --basetemp .pytest-tmp-loop78-focused`
  - Result: `1 passed`.
- Focused rerun after neutralizer repair:
  - same test with `--basetemp .pytest-tmp-loop78-focused-2`
  - Result: `1 passed`.
- Full affected API test file:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop78-workout-plans-2`
  - Result: `32 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual TestClient probe for a Hebrew minimal plan:
  - verified returned tracking guidance includes:
    - `מאמץ מילולי`
    - `קל מדי`
    - `כבד מדי`
    - `בשליטה`
  - verified it does not include corrupted `לכבד מדי`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One existing guidance string updated.
  - One narrow repair for an existing neutralizer edge case.
  - No new logging-guidance service, no schema change, no extra UI.

### Failures and fixes

- Initial manual probe failed to find the item because inline Python used literal Hebrew and PowerShell corrupted the string.
- Reran with Unicode escapes for the search terms.
- Manual probe then exposed `לכבד מדי` from the broad neutralizer.
- Fixed with a narrow post-replacement and tightened the test.

### Next research target

- Loop 79 should inspect whether the knowledge center itself documents this qualitative logging path.
- Product question:
  - The builder tells users to log plain-language effort, but does provider context tell the AI not to convert those phrases into fake RPE/RIR numbers?

## Loop 79 - Knowledge center/provider context for qualitative effort

### Research target

- Check whether the provider context tells the coach to preserve natural Hebrew effort phrases instead of inventing numeric RPE/RIR.
- Keep the provider context compact because `workout_plan` and `workout_log` context are already near budget limits.

### Sources checked

- Stronger by Science / Eric Helms - The Science of Autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- Local code inspection:
  - `backend/app/services/coaching_knowledge.py`
  - `backend/tests/test_coaching_knowledge.py`

### Findings extracted

- The full Hebrew coaching language protocol already had the right rule:
  - preserve phrases like `קל מדי`, `כבד מדי`, and `בשליטה` as verbal effort.
- The compact provider context did not clearly say that those phrases are not numbers.
- Adding a new provider section would be overkill and would risk prompt budget drift.
- Smallest useful change:
  - fold the rule into the existing compact `coaching_behavior` line.

### Changes made

- Updated `backend/app/services/coaching_knowledge.py`:
  - compact workout provider context now says `קל/כבד/בשליטה=מאמץ מילולי, לא מספר`.
  - shortened adjacent wording to keep the provider context under the existing budget.
- Updated `backend/tests/test_coaching_knowledge.py`:
  - provider-budget test now requires `מאמץ מילולי` and `לא מספר` in workout `coaching_behavior`.
  - kept existing budget assertions for `workout_plan` and `workout_log`.

### Tests and checks

- Focused provider-budget test:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom --basetemp .pytest-tmp-loop79-budget-2`
  - Result: `1 passed`.
- Full affected knowledge test file:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop79-knowledge`
  - Result: `112 passed`.
- Provider-context size probe:
  - `workout_plan`: `8347`
  - `workout_log`: `8278`
- `git diff --check`:
  - Clean before this log entry; CRLF warnings only.

### Manual/product check

- Manual provider-context probe verified:
  - compact context includes `מאמץ מילולי, לא מספר`.
  - compact context stays under the provider budget.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One existing compact context line was updated.
  - No new provider section, schema, service, or duplicated language registry.

### Failures and fixes

- First budget test failed because the provider context grew to `8351`, just over the `<8350` assertion.
- Fixed by shortening nearby wording without removing the rule.

### Next research target

- Loop 80 should verify the real chat/context pipeline, not just `CoachingKnowledgeService.for_provider_context()`.
- Product question:
  - Does the updated qualitative-effort rule survive the actual context builder/provider payload used for workout chat and workout-log requests?

## Loop 80 - Optimized provider payload preserves qualitative effort rule

### Research target

- Verify the real chat/context pipeline, not only the isolated knowledge service.
- Specific risk:
  - `ContextBuilder` may include the rule, but token optimization may drop it before the AI provider sees it.

### Sources checked

- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- TechRadar interview with Fitbod cofounder Allen Chen on AI fitness context and explainability:
  - https://www.techradar.com/health-fitness/fitness-apps/its-no-longer-enough-for-an-app-to-tell-you-what-to-do-people-want-to-know-why-fitness-app-fitbods-founder-on-the-reason-behind-the-ai-fitness-boom
- Search pass:
  - `CDC tracking physical activity progress self monitoring goals`
  - `AI fitness app workout interpretation user context paper 2026`
  - `context engineering LLM keep critical instructions compact prompt engineering best practices`
- Local code inspection:
  - `backend/app/services/context_builder.py`
  - `backend/app/services/token_budgeting.py`
  - `backend/app/services/coach_engine.py`
  - `backend/tests/test_context_builder.py`
  - `backend/tests/test_token_optimization.py`

### Findings extracted

- AI fitness feedback should preserve user context and not collapse lived workout feedback into rigid numbers.
- CDC supports subjective intensity as a legitimate rating path, not only exact objective metrics.
- The real product bug was in compaction:
  - `ContextBuilder` included `coaching_behavior`.
  - `compact_provider_context()` dropped `coaching_behavior`.
  - The optimized AI request therefore lost `מאמץ מילולי, לא מספר`.
- Smallest useful fix:
  - whitelist one compact `coaching_behavior` item in the existing token compactor.

### Changes made

- Updated `backend/app/services/token_budgeting.py`:
  - `_KNOWLEDGE_LIMITS` now keeps one compact `coaching_behavior` item.
  - This preserves the instruction `קל/כבד/בשליטה=מאמץ מילולי, לא מספר` in optimized AI requests.
- Updated `backend/tests/test_token_optimization.py`:
  - added `test_optimized_workout_log_request_keeps_qualitative_effort_instruction`.
  - the test builds real context through `ContextBuilder`, builds the optimized AI request, parses the provider payload, and verifies the rule survives in both compact context and `tools`.

### Tests and checks

- Focused new regression test:
  - `python -m pytest backend/tests/test_token_optimization.py::test_optimized_workout_log_request_keeps_qualitative_effort_instruction --basetemp .pytest-tmp-loop80-token-focused`
  - Result: `1 passed`.
- Existing token-budget guard:
  - `python -m pytest backend/tests/test_token_optimization.py::test_optimized_chat_request_cuts_input_tokens_by_half_without_dropping_context --basetemp .pytest-tmp-loop80-token-budget`
  - Result: `1 passed`.
- Full affected token file:
  - `python -m pytest backend/tests/test_token_optimization.py --basetemp .pytest-tmp-loop80-token-full`
  - Result: `5 passed`.
- Context builder spot check:
  - `python -m pytest backend/tests/test_context_builder.py::test_context_builder_includes_compact_coaching_knowledge --basetemp .pytest-tmp-loop80-context-builder`
  - Result: `1 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Before the fix, a manual optimized-request probe showed:
  - `full_has_coaching_behavior=True`
  - `compact_has_coaching_behavior=False`
  - `compact_has_qualitative_effort=False`
- After the fix, the same path showed:
  - `compact_has_coaching_behavior=True`
  - compact line includes `מאמץ מילולי, לא מספר`
  - `tools_has_qualitative_effort=True`
  - optimized input tokens: `966`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One existing compaction whitelist was extended.
  - One regression test covers the actual failure path.
  - No new prompt layer, no duplicated context builder, no schema change.

### Failures and fixes

- Initial probe confirmed the rule was present in full context but absent from the optimized provider payload.
- Fixed by preserving one compact `coaching_behavior` item.

### Next research target

- Loop 81 should inspect user-visible chat behavior for qualitative effort after logging.
- Product question:
  - When the user says `היה קל מדי`, does the local workout-log response give a practical progression action without inventing fake RPE/RIR and without routing to generic AI chat?

## Loop 81 - User-visible Hebrew workout-log effort response

### Research target

- Inspect the local chat route for natural Hebrew effort phrases.
- Confirm user-facing responses for:
  - `קל מדי`
  - `כבד מדי`
  - `בשליטה`
- Avoid production code if the existing route already behaves correctly.

### Sources checked

- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- TechRadar interview with Fitbod cofounder Allen Chen on contextual AI fitness coaching:
  - https://www.techradar.com/health-fitness/fitness-apps/its-no-longer-enough-for-an-app-to-tell-you-what-to-do-people-want-to-know-why-fitness-app-fitbods-founder-on-the-reason-behind-the-ai-fitness-boom
- Local code inspection:
  - `backend/app/services/coach_engine.py`
  - `backend/app/services/workout_service.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- The local workout-log route already maps qualitative effort to practical actions:
  - underloaded -> small load increase or tempo change.
  - too hard -> keep or reduce load/volume.
  - controlled -> repeat structure and add one rep only if technique stays clean.
- Existing tests covered `קל מדי` and `כבד מדי`, but did not explicitly assert that the response avoids fake RPE/RIR.
- There was no chat endpoint test for `בשליטה`.
- Smallest useful change:
  - tighten tests, not production code.

### Changes made

- Updated `backend/tests/test_coach_engine.py`:
  - underload chat test now asserts no `RPE` or `RIR` is invented in the response.
  - underload test now checks saved `rir` with `.get("rir") is None`.
  - too-hard chat test now asserts no `RPE` or `RIR` is invented in the response.
  - too-hard test now asserts saved `rpe is None` and saved `rir is None`.
  - added `test_chat_endpoint_natural_hebrew_controlled_log_keeps_verbal_effort`.

### Tests and checks

- Focused underload chat test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_natural_hebrew_underload_log_recommends_small_adjustment --basetemp .pytest-tmp-loop81-underload`
  - Result: `1 passed`.
- Focused too-hard chat test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_natural_hebrew_too_hard_log_is_conservative --basetemp .pytest-tmp-loop81-toohard`
  - Result: `1 passed`.
- Focused controlled-effort chat test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_natural_hebrew_controlled_log_keeps_verbal_effort --basetemp .pytest-tmp-loop81-controlled`
  - Result: `1 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual TestClient Hebrew chat:
  - Input:
    - `תעד אימון: עשיתי לחיצת חזה 3x10, היה מאתגר אבל בשליטה, בלי כאב.`
  - Output:
    - `רשמתי את האימון. נשמע שהמאמץ היה בשליטה. הפעולה הבאה: לחזור על אותו מבנה, ואם הטכניקה נשארת נקייה להוסיף חזרה אחת ולתעד שוב.`
  - Provider status:
    - `local_tool`
- This is the intended behavior:
  - short Hebrew response.
  - one next action.
  - no fake numeric RPE/RIR.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Production code already behaved correctly.
  - Only missing test coverage was added.
  - No new service, route, schema, or prompt text.

### Failures and fixes

- First patch attempt missed because the nearby test file block has mixed historical encoding display in PowerShell.
- Reopened exact UTF-8 line-numbered block and applied a tighter patch.

### Next research target

- Loop 82 should inspect whether dashboard/next-workout copy also preserves qualitative effort without saying `RPE/RIR בשליטה` when the evidence was only `קל מדי`.
- Product question:
  - Does the dashboard next action accidentally convert verbal effort into numeric-style evidence?

## Loop 82 - Dashboard copy preserves verbal underload evidence

### Research target

- Inspect dashboard/next-workout copy after a Hebrew `קל מדי` workout log.
- Make sure dashboard guidance does not convert verbal effort into fake numeric RIR evidence.

### Sources checked

- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- TechRadar interview with Fitbod cofounder Allen Chen on contextual AI fitness coaching:
  - https://www.techradar.com/health-fitness/fitness-apps/its-no-longer-enough-for-an-app-to-tell-you-what-to-do-people-want-to-know-why-fitness-app-fitbods-founder-on-the-reason-behind-the-ai-fitness-boom
- Local code inspection:
  - `backend/app/services/dashboard_service.py`
  - `backend/tests/test_dashboard_api.py`
  - `frontend/src/DashboardPanel.tsx`
  - `frontend/src/DashboardPanel.test.tsx`

### Findings extracted

- Dashboard had one over-broad branch:
  - `qualitative_underload` and `high_rir_underload` shared the same copy.
- That meant a `קל מדי` log produced dashboard guidance saying the log left too many reps in reserve and targeted `RIR 1-3`.
- This is not a dangerous training recommendation, but it violates the product rule:
  - do not convert verbal effort into a fake numeric RPE/RIR statement.
- Smallest useful change:
  - split dashboard copy by adjustment reason.

### Changes made

- Updated `backend/app/services/dashboard_service.py`:
  - `qualitative_underload` now says the log described the effort as `קל מדי`.
  - it recommends a small load increase or slower tempo without a big jump.
  - it asks to log `מאמץ/כאב ומה הושלם`, not `RPE/RIR`.
  - `high_rir_underload` keeps the numeric `RIR 1-3` target.
- Updated `backend/tests/test_dashboard_api.py`:
  - natural Hebrew underload dashboard test now requires `קל מדי`.
  - it rejects `RIR 1-3` and `RPE/RIR` in the verbal-effort dashboard action.

### Tests and checks

- Verbal underload dashboard test:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_surfaces_natural_hebrew_underload_guidance --basetemp .pytest-tmp-loop82-dashboard-qual`
  - Result: `1 passed`.
- Numeric high-RIR dashboard test:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_surfaces_high_rir_underload_guidance --basetemp .pytest-tmp-loop82-dashboard-rir`
  - Result: `1 passed`.
- Full affected dashboard API file:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop82-dashboard-full`
  - Result: `14 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual dashboard probe after Hebrew `קל מדי` workout log:
  - reason:
    - `qualitative_underload`
  - next action:
    - `לבצע את יום 1 גוף מלא. הלוג האחרון תיאר שהמאמץ היה קל מדי, אז להעלות עומס קטן או להאט קצב בלי קפיצה גדולה. לתעד מאמץ/כאב ומה הושלם - לא לנחש.`
  - `RIR 1-3` present:
    - `False`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Existing branch was split by existing reason values.
  - No schema change, no new copy service, no frontend change.

### Failures and fixes

- No test failures after the branch split.

### Next research target

- Loop 83 should inspect the training adaptation service copy and next-workout execution plan for the same issue.
- Product question:
  - Does the next workout execution plan still say `RPE/RIR בשליטה` when the only evidence was qualitative `קל מדי`?

## Loop 83 - Next-workout execution plan preserves verbal effort evidence

### Research target

- Inspect `TrainingAdaptationService` and the next-workout execution plan.
- Confirm qualitative `קל מדי` and `בשליטה` evidence does not become fake `RPE/RIR` evidence.

### Sources checked

- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Stronger by Science / Eric Helms - The Science of Autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- Local code inspection:
  - `backend/app/services/training_adaptation_service.py`
  - `backend/app/services/workout_service.py`
  - `backend/tests/test_training_adaptation_service.py`
  - `backend/tests/test_workout_logs_api.py`

### Findings extracted

- `TrainingAdaptationService` used `qualitative_underload` but still returned a numeric `RIR 1-3` target.
- `WorkoutService._build_adjusted_exercise()` reused the same note for `qualitative_underload` and `high_rir_underload`.
- Verbal `בשליטה` could enter the generic manageable-effort path and get execution copy saying the log showed `RPE/RIR בשליטה`.
- This is not catastrophic, but it blurs evidence quality. The user did not report RPE/RIR, so the app should not imply they did.
- Smallest useful change:
  - make existing reason values more precise and branch copy by reason.

### Changes made

- Updated `backend/app/services/training_adaptation_service.py`:
  - `qualitative_underload` now says the log described the effort as too easy and avoids `RIR`.
  - numeric `high_rir_underload` still targets `RIR 1-3`.
  - added `qualitative_controlled_effort` for `בשליטה` logs without numeric RPE/RIR.
- Updated `backend/app/services/workout_service.py`:
  - execution-plan notes now split:
    - `qualitative_underload` -> verbal too-easy copy.
    - `high_rir_underload` -> numeric RIR copy.
    - `qualitative_controlled_effort` -> verbal controlled-effort copy.
  - generic `RPE/RIR בשליטה` copy remains only for genuinely numeric/evidence-backed cases.
- Updated `backend/tests/test_training_adaptation_service.py`:
  - qualitative underload now rejects `RIR`.
  - added qualitative controlled-effort adaptation test.
- Updated `backend/tests/test_workout_logs_api.py`:
  - next-workout underload test now rejects `RIR` and `RPE/RIR`.
  - added next-workout controlled-effort API test.

### Tests and checks

- Focused training underload test:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_qualitative_underload_without_fake_rir --basetemp .pytest-tmp-loop83-train-underload`
  - Result: `1 passed`.
- Focused training controlled-effort test:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_qualitative_controlled_effort_without_fake_metrics --basetemp .pytest-tmp-loop83-train-controlled`
  - Result: `1 passed`.
- Focused next-workout underload test:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_next_workout_uses_natural_hebrew_underload_without_fake_rir --basetemp .pytest-tmp-loop83-next-underload`
  - Result: `1 passed`.
- Focused next-workout controlled-effort test:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_next_workout_uses_controlled_verbal_effort_without_fake_metrics --basetemp .pytest-tmp-loop83-next-controlled`
  - Result: `1 passed`.
- Full affected adaptation file:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop83-training-full`
  - Result: `15 passed`.
- Full affected workout-log API file:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop83-workout-logs-full`
  - Result: `30 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual next-workout probe after Hebrew `קל מדי` log:
  - reason:
    - `qualitative_underload`
  - execution note:
    - `להעלות עומס קטן או להאט קצב כי הלוג תיאר שקל מדי, לא לקפוץ הרבה.`
  - notes:
    - `לעבוד בטווח ללא כאב ובקצב נשלט. הלוג האחרון תיאר מאמץ קל מדי; לתקן במשתנה אחד קטן בלי קפיצה גדולה.`
  - `RIR` present in execution note or notes:
    - `False`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Existing adaptation reasons and execution-plan branches were refined.
  - No new schema, no separate copy registry, no extra orchestration layer.

### Failures and fixes

- No test failures after the wording split.

### Next research target

- Loop 84 should inspect frontend dashboard/workout panel rendering for these new verbal effort actions.
- Product question:
  - Does the frontend display the corrected backend copy cleanly without stale expectations, overflow, or hidden raw reason codes?

## Loop 84 - Frontend renders verbal effort adjustment reasons

### Research target

- Inspect frontend Dashboard and Workouts panels for the corrected verbal-effort backend copy.
- Make sure new backend reason values do not disappear, leak raw codes, or show fake `RPE/RIR` copy.

### Sources checked

- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- TechRadar interview with Fitbod cofounder Allen Chen on contextual AI fitness coaching:
  - https://www.techradar.com/health-fitness/fitness-apps/its-no-longer-enough-for-an-app-to-tell-you-what-to-do-people-want-to-know-why-fitness-app-fitbods-founder-on-the-reason-behind-the-ai-fitness-boom
- Local code inspection:
  - `frontend/src/DashboardPanel.tsx`
  - `frontend/src/DashboardPanel.test.tsx`
  - `frontend/src/WorkoutsPanel.tsx`
  - `frontend/src/WorkoutsPanel.test.tsx`
  - `frontend/src/formatters.ts`

### Findings extracted

- Dashboard renders backend `next_recommended_action` directly and does not expose raw adjustment reason codes.
- WorkoutsPanel renders `execution_note` directly and then optionally adds a per-exercise Hebrew explanation from `formatAdjustmentExplanation()`.
- New reason `qualitative_controlled_effort` would not leak, but it also would not get a user-facing explanation.
- Existing qualitative reasons were also missing from the explanation map.
- Smallest useful change:
  - add formatter entries for the qualitative reason values and one UI regression test.

### Changes made

- Updated `frontend/src/formatters.ts`:
  - added Hebrew explanations for:
    - `qualitative_controlled_effort`
    - `qualitative_underload`
    - `qualitative_high_effort`
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - added a qualitative-effort next-workout fixture.
  - added a UI test that renders verbal effort explanations, rejects raw reason codes, and rejects `RPE/RIR` leakage.

### Tests and checks

- Focused WorkoutsPanel UI test:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx -t "renders verbal effort adjustment explanations"`
  - Result: `1 passed`, `18 skipped`.
- Full WorkoutsPanel suite:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `19 passed`.
- DashboardPanel suite:
  - `npm.cmd --prefix frontend test -- --run DashboardPanel.test.tsx`
  - Result: `4 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- The new UI fixture renders:
  - `Goblet squat: אפשר לתקן בעדינות - הלוג האחרון תיאר שהתרגיל היה קל מדי.`
  - `Dumbbell row: אפשר לשקול תוספת עדינה - הלוג האחרון תיאר מאמץ בשליטה.`
- The UI test confirms:
  - `qualitative_underload` is not visible.
  - `qualitative_controlled_effort` is not visible.
  - `RPE/RIR` is not visible in that verbal-effort fixture.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Formatter map extended with three entries.
  - One UI regression test.
  - No new presentation abstraction or duplicated backend logic.

### Failures and fixes

- No test failures in this loop.

### Next research target

- Loop 85 should inspect docs/product behavior references for stale workout-log guidance that says only `RPE/RIR`.
- Product question:
  - Do local docs and prompt registry now reflect that Hebrew users can log plain-language effort like `קל מדי`, `כבד מדי`, and `בשליטה`?

## Loop 85 - Product docs reflect verbal effort logging

### Research target

- Inspect source-of-truth product docs and prompt registry for stale `RPE/RIR`-only workout-log guidance.
- Avoid adding redundant runtime prompt code if `coaching_knowledge` already carries the rule.

### Sources checked

- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Shalawadi et al. 2026 - Who Gets to Interpret the Workout?
  - https://arxiv.org/abs/2604.23830
- Local code/docs inspection:
  - `CALO BRAIN/01_PRODUCT/02-Product-Behavior.md`
  - `CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md`
  - `README.md`
  - `backend/app/prompts.py`
  - `backend/app/services/coaching_knowledge.py`

### Findings extracted

- Product behavior still said workout logs persist `RPE/RIR`, pain flags, and notes, but did not mention verbal effort signals.
- Prompt registry did not document the rule that `קל מדי`, `כבד מדי`, and `בשליטה` must not become fake RPE/RIR.
- Runtime prompt code did not need another sentence:
  - compact `coaching_knowledge.coaching_behavior` already carries the provider rule.
  - duplicating it in the global prompt would add prompt weight without a clear behavioral gain.
- Smallest useful change:
  - update source-of-truth docs only.

### Changes made

- Updated `CALO BRAIN/01_PRODUCT/02-Product-Behavior.md`:
  - metadata date set to `2026-06-25`.
  - workout logs now explicitly include verbal effort signals: `קל מדי`, `כבד מדי`, `בשליטה`.
  - product behavior now says verbal effort must stay verbal in coach responses, next-workout adjustments, and dashboard copy.
- Updated `CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md`:
  - metadata date set to `2026-06-25`.
  - prompt constraints now say not to invent numeric RPE/RIR from verbal effort.
  - implementation notes now mention the compact `coaching_behavior` item surviving token compaction.

### Tests and checks

- Documentation verification:
  - `rg -n "verbal effort|קל מדי|כבד מדי|בשליטה|fake numeric RPE/RIR|coaching_behavior" CALO BRAIN/01_PRODUCT/02-Product-Behavior.md CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md`
  - Result: expected updated lines found.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- No runtime behavior changed in this loop.
- Previous loops already verified backend chat, dashboard, next-workout, frontend UI, and build behavior for verbal effort.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Two source-of-truth docs updated.
  - No redundant prompt-code edit.
  - No new documentation page or duplicated spec.

### Failures and fixes

- No failures in this loop.

### Next research target

- Loop 86 should return to the workout-plan builder itself and inspect whether plan generation asks users to log verbal effort consistently across all plan horizons.
- Product question:
  - Do single workout, weekly, two-week, and monthly plans all carry the same short tracking guidance without bloating the plan output?

## Loop 86 - Plan horizons carry verbal effort tracking guidance

### Research target

- Inspect workout-plan generation for stale `RPE/RIR`-only tracking language.
- Confirm all four plan horizons mention verbal effort without bloating plan output:
  - single workout
  - weekly plan
  - two-week plan
  - monthly plan

### Sources checked

- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Stronger by Science / Eric Helms - The Science of Autoregulation:
  - https://www.strongerbyscience.com/autoregulation/
- Local code inspection:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_workout_plan_builder.py`
  - `frontend/src/WorkoutsPanel.tsx`

### Findings extracted

- Shared `_tracking_guidance()` already tells users to log `RPE כללי או מאמץ מילולי כמו קל מדי/כבד מדי/בשליטה`.
- Stale language remained in `_progression_schedule()`:
  - single workout said only `RPE/כאב/מה הושלם`.
  - weekly plan said only `RPE, כאב ופספוסים`.
  - beginner two-week plan said only `RIR`.
  - monthly beginner/generic/advanced check-in wording leaned numeric.
- Smallest useful change:
  - update the existing schedule strings, not add another tracking-guidance layer.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - single workout progression now says `RPE או מאמץ מילולי`.
  - weekly progression now says `RPE או מאמץ מילולי`.
  - two-week beginner progression now says `RIR או מאמץ מילולי`.
  - monthly beginner/generic/advanced progression checks now account for verbal effort as well as RPE.
- Updated `backend/tests/test_workout_plans_api.py`:
  - single-workout alias test now requires verbal-effort progression and tracking guidance.
  - weekly/two-week/monthly horizon test now requires verbal-effort guidance in tracking and progression output.

### Tests and checks

- Focused single-workout test:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan --basetemp .pytest-tmp-loop86-single-2`
  - Result: `1 passed`.
- Focused horizon test:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons --basetemp .pytest-tmp-loop86-horizons-3`
  - Result: `1 passed`.
- Full affected workout-plans API file:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop86-workout-plans-full`
  - Result: `32 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual API probe across plan horizons:
  - `single_workout`: verbal-effort guidance present.
  - `weekly_plan`: verbal-effort guidance present.
  - `two_week_plan`: verbal-effort guidance present.
  - `monthly_plan`: verbal-effort guidance present.
- Example single tracking line:
  - `לתעד אחרי כל אימון: הושלם/חלקי/פוספס, RPE כללי או מאמץ מילולי כמו קל מדי/כבד מדי/בשליטה, כאב או מגבלה, והערה קצרה על הביצוע.`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Edited existing schedule strings.
  - Added assertions to existing tests.
  - No new plan-guidance system or duplicated plan formatter.

### Failures and fixes

- First horizon test failed because the monthly branch in the fixture did not contain exact `מאמץ מילולי`.
- Printing the returned monthly plan showed natural inflection `המאמץ המילולי`.
- Fixed the test assertion to require both `מאמץ` and `מילולי` in the same item.

### Next research target

- Loop 87 should inspect structured-log form validation and helper copy.
- Product question:
  - Does the frontend structured-log form encourage natural Hebrew effort notes without requiring users to know RPE/RIR?

## Loop 87 - Structured-log form encourages natural effort notes

### Research target

- Inspect the frontend structured-log form and validation copy.
- Make sure users can understand that `קל מדי`, `כבד מדי`, and `בשליטה` are valid log notes, not only RPE/RIR.

### Sources checked

- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Local code inspection:
  - `frontend/src/WorkoutsPanel.tsx`
  - `frontend/src/WorkoutsPanel.test.tsx`

### Findings extracted

- The form already had RPE/RIR fields and note fields.
- The empty structured-log validation still said only:
  - `RPE/RIR כללי או הערה קצרה`
- Exercise and general note textareas had no examples, so users could miss that natural effort phrases are useful.
- Smallest useful change:
  - update placeholders and validation copy only.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - exercise note placeholder now gives examples:
    - `קל מדי`, `כבד מדי`, `בשליטה`, or pain area.
  - general note placeholder now gives examples:
    - `האימון היה בשליטה`, `קל מדי`, `כבד מדי`.
  - empty structured-log validation now says:
    - `הערת מאמץ כמו קל מדי/כבד מדי/בשליטה`.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - added `guides empty structured logs toward natural effort notes`.
  - test verifies placeholders, validation text, and no payload submission.

### Tests and checks

- Focused UI test:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx -t "guides empty structured logs"`
  - Result: `1 passed`, `19 skipped`.
- Full WorkoutsPanel suite:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `20 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- The UI now tells users they can write plain Hebrew effort notes instead of requiring numeric effort.
- This matches backend parsing and dashboard/next-workout behavior from previous loops.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Visible copy only.
  - One regression test.
  - No new form fields, no validation abstraction, no UX redesign.

### Failures and fixes

- The first test assertion used `findByPlaceholderText` for an exercise placeholder that appears once per exercise.
- Fixed by using `findAllByPlaceholderText`.

### Next research target

- Loop 88 should inspect the chat free-text workout log placeholder and text log route.
- Product question:
  - Does the free-text log UI also invite natural Hebrew effort phrases and not only sets/reps/weight examples?

## Loop 88 - Free-text workout log placeholder includes verbal effort

### Research target

- Inspect the free-text workout log UI.
- Confirm the placeholder invites natural Hebrew effort phrases, not only sets/reps/weight.

### Sources checked

- CDC - How to Measure Physical Activity Intensity:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- Local code inspection:
  - `frontend/src/WorkoutsPanel.tsx`
  - `frontend/src/WorkoutsPanel.test.tsx`

### Findings extracted

- The free-text log route already parses natural effort.
- The UI placeholder still showed only:
  - sets, reps, and weight.
- This creates a product mismatch:
  - backend accepts `היה קל מדי בלי כאב`, but the UI does not teach it.
- Smallest useful change:
  - extend the placeholder example and assert it in the existing free-text log test.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - free-text workout log placeholder now includes:
    - `היה קל מדי בלי כאב`.
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - existing free-text log test now asserts the natural-effort placeholder is visible.

### Tests and checks

- Focused free-text log UI test:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx -t "logs a workout from natural language text"`
  - Result: `1 passed`, `19 skipped`.
- Full WorkoutsPanel suite:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `20 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- The free-text log placeholder now demonstrates:
  - exercise volume/load.
  - qualitative effort.
  - explicit no-pain status.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One placeholder update.
  - One assertion in an existing test.
  - No new form state or alternate logging flow.

### Failures and fixes

- No failures in this loop.

### Next research target

- Loop 89 should step back from verbal effort and inspect plan-type detection again for natural Hebrew slang.
- Product question:
  - Are single workout, weekly, two-week, and monthly requests still classified correctly after all the recent copy and tracking changes?

## Loop 89 - Hebrew slang plan-type detection and chat routing

### Research target

- Re-check plan-type detection and chat routing for natural Hebrew/slang plan requests.
- Confirm `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan` still route correctly.

### Sources checked

- Local code inspection:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/app/services/coach_intent_service.py`
  - `backend/app/services/coach_engine.py`
  - `backend/tests/test_workout_plan_builder.py`
  - `backend/tests/test_coach_intent_service.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- Builder inference already handled core Hebrew plan terms, but lacked slang variants:
  - `סשן`, `מיני אימון`, `שבוע הבא`, `שבועיים הקרובים`, `חודש הקרוב`.
- Chat intent routing also lacked `סשן`, so a real chat request like `תן לי סשן אחד קצר עכשיו` could miss the workout-plan path.
- Manual chat probe exposed stale saved-plan copy:
  - response still said `לתעד RPE/כאב ומה הושלם`.
- Smallest useful change:
  - extend phrase lists and update the direct saved-plan response copy.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - added single-workout slang:
    - `עכשיו`, `אימון בודד`, `מיני אימון`, `סשן`, `סשן אחד`.
  - added weekly phrases:
    - `שבוע הבא`, `לשבוע הבא`.
  - added two-week phrases:
    - `שבועיים הקרובים`, `השבועיים הקרובים`, `שבועיים הבאים`, `לשבועיים הקרובים`.
  - added monthly phrases:
    - `חודש הקרוב`, `לחודש הקרוב`.
- Updated `backend/app/services/coach_intent_service.py`:
  - added matching chat-routing coverage for `סשן`, `אימון זריז`, `מיני אימון`, `עכשיו`, `שבוע הבא`, `שבועיים הקרובים`, and `חודש הקרוב`.
- Updated `backend/app/services/coach_engine.py`:
  - saved-plan next action now says `לתעד RPE או מאמץ מילולי, כאב ומה הושלם`.
  - plan activation fallback now uses the same wording.
- Updated tests:
  - `backend/tests/test_workout_plan_builder.py`
  - `backend/tests/test_coach_intent_service.py`
  - `backend/tests/test_coach_engine.py`

### Tests and checks

- Plan-builder tests:
  - `python -m pytest backend/tests/test_workout_plan_builder.py --basetemp .pytest-tmp-loop89-plan-builder-2`
  - Result: `5 passed`.
- Focused chat-intent test:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_hebrew_training_week_creation_as_workout_plan --basetemp .pytest-tmp-loop89-intent-focused`
  - Result: `1 passed`.
- Full builder + intent files:
  - `python -m pytest backend/tests/test_workout_plan_builder.py backend/tests/test_coach_intent_service.py --basetemp .pytest-tmp-loop89-builder-intent-full`
  - Result: `29 passed`.
- Focused chat-response tests:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_workout_plan_intent_to_module backend/tests/test_coach_engine.py::test_chat_confirms_plan_replacement_deletes_old_plan_and_keeps_log_history backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current --basetemp .pytest-tmp-loop89-chat-focused-2`
  - Result: `3 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew chat:
  - input:
    - `תן לי סשן אחד קצר עכשיו`
  - result:
    - `provider_status=local_tool`
    - saved plan type: `single_workout`
    - response includes `מאמץ מילולי`
- Visible response:
  - `אימון יחיד מוכן... הפעולה הבאה: להתחיל בסקוואט לקופסה, לבצע את שאר האימון לפי הסדר, ולתעד RPE או מאמץ מילולי, כאב ומה הושלם - לא לנחש.`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Direct phrase-list additions.
  - Direct tests for routing/inference.
  - No classifier rewrite or NLP layer.

### Failures and fixes

- First focused pytest command used an old test name and ran no tests.
- Fixed by finding the current single-workout chat test name and rerunning the correct focused set.
- Manual chat probe exposed stale response copy; fixed `_first_workout_next_action()` and `_activated_plan_response()`.

### Next research target

- Loop 90 should inspect the remaining stale `RPE/כאב` response helpers in dashboard, workout edits, and recovery guidance.
- Product question:
  - Which remaining `RPE/כאב` lines should become `RPE או מאמץ מילולי`, and which should stay numeric because they are specifically about RPE/RIR?

---

## Loop 90 - Remove stale RPE-only tracking copy without weakening numeric gates

### Research question

- The bot now preserves Hebrew verbal effort (`קל מדי`, `כבד מדי`, `בשליטה`) without inventing fake RPE/RIR.
- Remaining question:
  - Where is `RPE/כאב` only tracking copy still user-visible?
  - Which instances are generic tracking prompts and should accept `מאמץ מילולי`?
  - Which instances are actual numeric progression gates and should stay RPE-specific?

### Findings extracted

- Generic post-workout tracking prompts should not force the user into numeric RPE/RIR.
- Numeric gates should stay numeric when the rule itself is numeric, for example:
  - progress one step only if the last log was clean, pain-free, and `RPE 8` or lower.
- This distinction keeps Hebrew-first behavior usable without making progression less safe.
- The remaining stale prompts were in:
  - return-after-break guidance
  - dashboard next action branches
  - scoped workout-plan edits
  - advanced two-week progression schedule copy
  - one frontend dashboard fixture

### Changes made

- Updated `backend/app/services/coach_engine.py`:
  - return-after-break next action now says:
    - `לתעד RPE או מאמץ מילולי, כאב/עייפות`
  - kept `RPE 5-7` as a real intensity target.
- Updated `backend/app/services/dashboard_service.py`:
  - numeric RPE/RIR branches now allow `RPE/RIR או מאמץ מילולי` for tracking.
  - qualitative `כבד מדי` branch now says `לתעד מאמץ מילולי, כאב ומה הושלם`.
  - generic fallback now says `לתעד RPE או מאמץ מילולי, כאב ומה הושלם`.
  - kept explicit `RPE/RIR` wording where the evidence is actually numeric.
- Updated `backend/app/services/workout_service.py`:
  - no-bench edit response now asks to log `RPE או מאמץ מילולי וכאב`.
  - row-machine replacement response now asks to log `RPE או מאמץ מילולי`.
  - minimum-version fallback now asks to log `RPE או מאמץ מילולי וכאב`.
  - kept substitution progression-gate text numeric because it depends on `RPE 8` or lower.
- Updated `backend/app/services/workout_plan_builder.py`:
  - advanced two-week progression warning now checks `RPE, מאמץ מילולי, כאב או ביצועים`.
- Updated `frontend/src/DashboardPanel.test.tsx`:
  - dashboard fixtures now match the current verbal-effort tracking contract.

### Tests and checks

- Dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop90-dashboard`
  - Result: `14 passed`.
- Focused coach-engine paths:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_scoped_row_machine_unavailable_updates_pull_without_replacement backend/tests/test_coach_engine.py::test_chat_scoped_reduce_volume_edit_updates_sets_without_replacement backend/tests/test_coach_engine.py::test_chat_endpoint_answers_return_after_break_guidance_locally --basetemp .pytest-tmp-loop90-coach`
  - Result: `3 passed`.
- Workout-log API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop90-workout-logs`
  - Result: `30 passed`.
- Plan builder:
  - `python -m pytest backend/tests/test_workout_plan_builder.py --basetemp .pytest-tmp-loop90-builder`
  - Result: `5 passed`.
- Focused workout-plan API:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level --basetemp .pytest-tmp-loop90-plans`
  - Result: `2 passed`.
- Frontend focused dashboard test:
  - `npm.cmd --prefix frontend test -- --run DashboardPanel.test.tsx`
  - Result: `4 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual Hebrew return-after-break chat:
  - input:
    - `לא התאמנתי חודש, איך לחזור לחדר כושר בלי להיפצע?`
  - result:
    - `status=200`
    - `provider_status=local_tool`
    - response includes `מאמץ מילולי`
    - response does not include old `RPE/` slash tracking prompt.
- Manual Hebrew dashboard path:
  - logged:
    - `עשיתי <exercise> 3x10. היה כבד מדי ובקושי סיימתי, בלי כאב.`
  - result:
    - `reason=qualitative_high_effort`
    - dashboard action includes `כבד מדי`
    - dashboard action includes `מאמץ מילולי`
    - dashboard action does not include fake `RPE/RIR`
    - dashboard action still says `לא לנחש`.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Copy-only contract fixes inside existing branches.
  - No new service, classifier, or prompt layer.
  - Numeric gate copy stayed numeric where it protects progression safety.

### Failures and fixes

- First manual TestClient probe failed before reaching the app because the helper expected `pathlib.Path`, not `str`.
- Fixed by rerunning with `Path(...)`; the product probe then passed.

### Next research target

- Loop 91 should inspect the remaining frontend progression-gate language:
  - `frontend/src/WorkoutsPanel.tsx` still says `שער התקדמות: לתעד RPE`.
  - backend progression gates still require numeric `RPE 8` or lower.
- Product question:
  - Should the UI keep `RPE` as mandatory for substitution progression gates, or should it offer a beginner-friendly fallback such as `מאמץ מילולי` while explicitly saying progression cannot advance without numeric RPE?

---

## Loop 91 - Let beginners save verbal effort at progression gates without advancing blindly

### Research question

- Progression-gate UI still required numeric `RPE` before saving a completed structured log.
- Product question:
  - Should numeric RPE remain mandatory for the gate?
  - Or should Hebrew beginners be allowed to log `מאמץ מילולי` while the app refuses to advance without numeric RPE?

### Sources checked

- Existing knowledge source registry:
  - `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - relevant source groups:
    - load monitoring includes `RPE/sRPE`, fatigue, performance trends, and recovery signals.
    - Hebrew language references include Israeli RPE/RIR explainers and plain-language guidance.
    - provider behavior keeps full language protocols internal and exposes compact Hebrew behavior rules.
- External refresh:
  - Borg/RPE background and verbal anchors:
    - https://en.wikipedia.org/wiki/Rating_of_perceived_exertion
  - Practical extraction:
    - RPE is a useful numeric subjective scale, but it depends on user understanding and clear anchors.
    - For beginners, a verbal effort note is better than blocking the log or forcing a made-up number.

### Findings extracted

- Numeric RPE is still appropriate for an actual progression gate because the current gate says:
  - progress one step only if clean, pain-free, and `RPE 8` or lower.
- But numeric RPE should not be required merely to save a workout log.
- Better product rule:
  - If RPE is present: allow the gate to evaluate progression.
  - If only verbal effort is present: save the log, preserve the evidence, and keep the current exercise version.
  - If neither RPE nor verbal effort is present: ask for one missing effort signal.
- This matches the core principle:
  - ask only for missing critical info;
  - infer safely;
  - do not fake RPE/RIR.

### Changes made

- Updated `frontend/src/WorkoutsPanel.tsx`:
  - Progression-gate hint now says:
    - `RPE 1-10 נדרש רק כדי להתקדם; מאמץ מילולי נשמר, אבל בלי RPE נשמור את הגרסה הנוכחית.`
  - Added a small `hasVerbalEffortText()` helper for Hebrew effort terms:
    - `קל מדי`, `כבד מדי`, `בשליטה`, `מאמץ`, `קשה`, `קל`, `כבד`.
  - Structured-log validation now blocks a gate attempt only when both are missing:
    - numeric RPE;
    - verbal effort note.
  - Error copy now says:
    - `שער התקדמות דורש RPE 1-10 כדי להתקדם; אם אינך יודע RPE, כתוב מאמץ מילולי ונשמור את הגרסה הנוכחית.`
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - renamed the gate test to require `RPE or verbal effort`.
  - kept coverage that empty gate attempts are blocked.
  - kept coverage that numeric RPE submits and is persisted.
  - added coverage that verbal effort submits with `rpe: null` and notes preserved.
  - updated partial-log coverage to the new hint/error language.

### Tests and checks

- Initial focused frontend test run:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: failed one assertion because the same helpful sentence appeared in both the hint and the validation error.
- Fixed assertion:
  - used `getAllByText(...)` for deliberate duplicate copy.
- Focused frontend test rerun:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `21 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Product behavior represented in tests:
  - empty gate attempt with reps but no effort signal:
    - blocked;
    - tells the user to add `RPE 1-10` or verbal effort.
  - numeric RPE:
    - submitted as `rpe: 8`;
    - still eligible for the numeric gate.
  - verbal effort:
    - submitted with `rpe: null`;
    - note `היה בשליטה בלי כאב` preserved;
    - no fake numeric RPE is created.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One local helper and two tests.
  - No new state machine.
  - Preserves the numeric gate instead of weakening backend progression logic.

### Failures and fixes

- First UI test assertion was too broad and matched both hint and error copy.
- Fixed the test assertion; no code behavior change needed.

### Next research target

- Loop 92 should inspect backend structured-log handling after a verbal-effort progression-gate log:
  - Does the backend/dashboard clearly explain that the log was saved but progression should stay on the current version because numeric RPE is missing?
  - Or does it silently treat the log as normal completion?

---

## Loop 92 - Backend holds progression gate when verbal effort lacks numeric RPE

### Research question

- After Loop 91, the frontend allows users to save a substitution-gate log with verbal effort and no numeric RPE.
- Backend risk:
  - `בשליטה` can become `qualitative_controlled_effort`.
  - The adaptation layer could treat that as enough progression evidence.
  - For a substitution progression gate, that would be too generous because the gate requires numeric `RPE 8` or lower.

### Findings extracted

- The structured log path stored `effort_signal` but did not mark that a substitution progression gate was missing numeric RPE.
- `TrainingAdaptationService._result_supports_progression()` allows `controlled` verbal effort when sets are completed.
- That is acceptable for ordinary small progression, but not for a numeric substitution gate.
- Better product rule:
  - Save the verbal log.
  - Preserve `effort_signal`.
  - Mark the gate as missing RPE.
  - Return `maintain`, not `progress_candidate`.
  - Explain that verbal effort was saved, but RPE is required before advancing the gate.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - structured exercise logs now detect whether the logged exercise belongs to a numeric substitution progression gate.
  - when the exercise is a gate and no exercise/session RPE was supplied, the saved exercise result gets:
    - `progression_gate_missing_rpe: true`
  - detection is limited to existing gate markers in the saved exercise text:
    - `שער התקדמות אחרי החלפה`
    - `הוחלף`
    - `קשות מדי`
    - `לא זמינה`
    - `לא זמין`
- Updated `backend/app/services/training_adaptation_service.py`:
  - added a `progression_gate_missing_rpe` hold path.
  - adaptation now returns:
    - `load_signal=maintain`
    - signal `שער התקדמות חסר RPE`
    - next action: `לשמור את הגרסה הנוכחית; מאמץ מילולי נשמר, אבל צריך RPE 1-10 וכאב כדי להתקדם שלב.`
  - exercise adjustment stays `maintain` with reason `progression_gate_missing_rpe`.
- Updated tests:
  - `backend/tests/test_workout_logs_api.py`
  - `backend/tests/test_dashboard_api.py`

### Tests and checks

- Focused workout API:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_next_workout_holds_progression_gate_after_verbal_effort_without_rpe --basetemp .pytest-tmp-loop92-workout-focused`
  - Result: `1 passed`.
- Focused dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_holds_progression_gate_after_verbal_effort_without_rpe --basetemp .pytest-tmp-loop92-dashboard-focused`
  - Result: `1 passed`.
- Full workout logs API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop92-workout-logs`
  - Result: `31 passed`.
- Full dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop92-dashboard`
  - Result: `15 passed`.
- Training adaptation service:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop92-training`
  - Result: `15 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual API probe:
  - create beginner bodyweight weekly plan.
  - ask in Hebrew:
    - `שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר`
  - log structured result:
    - `היה בשליטה בלי כאב`
    - no numeric RPE.
  - result:
    - `progression_gate_missing_rpe=True`
    - next workout `load_signal=maintain`
    - adjusted reason `progression_gate_missing_rpe`
    - execution note includes:
      - `מאמץ מילולי נשמר`
      - `RPE 1-10`
      - `הגרסה הנוכחית`

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One persisted result marker and one adaptation branch.
  - Reuses existing exercise notes/gate markers.
  - Avoids a larger gate-state model until there is evidence it is needed.

### Failures and fixes

- No failing tests after implementation.

### Next research target

- Loop 93 should inspect frontend display for the new `progression_gate_missing_rpe` reason:
  - Does the next-workout panel show the backend `execution_note` clearly enough?
  - Should `frontend/src/formatters.ts` add a human explanation for this reason so it does not appear as an unformatted or silent adjustment?

---

## Loop 93 - Frontend explains held progression gate without leaking reason code

### Research question

- Backend now sends `progression_gate_missing_rpe` when verbal effort is saved but numeric RPE is missing for a substitution progression gate.
- UI question:
  - Is the backend `execution_note` enough?
  - Or should the per-exercise formatter also explain the reason in natural Hebrew?

### Findings extracted

- `WorkoutsPanel` already renders `execution_note`, so the user would see the main backend message.
- But adjustment reasons also have friendly per-exercise explanations through `formatAdjustmentExplanation()`.
- Leaving the new reason without a formatter would be quiet and inconsistent with nearby reasons.
- Raw reason codes still must not reach the DOM.

### Changes made

- Updated `frontend/src/formatters.ts`:
  - added `progression_gate_missing_rpe`:
    - `נשארים בגרסה הנוכחית - מאמץ מילולי נשמר, אבל צריך RPE 1-10 לפני שמתקדמים שלב.`
- Updated `frontend/src/WorkoutsPanel.test.tsx`:
  - added a held progression-gate fixture.
  - added UI coverage that:
    - shows the Hebrew hold explanation;
    - includes `מאמץ מילולי נשמר`;
    - includes `RPE 1-10`;
    - does not leak `progression_gate_missing_rpe`.

### Tests and checks

- WorkoutsPanel:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `22 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Product behavior represented by UI test:
  - next-workout panel shows the held gate reason in natural Hebrew.
  - raw reason code remains hidden.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One formatter entry and one UI test.
  - No extra component state or duplicated business logic.

### Failures and fixes

- Initial patch target used an old test name.
- Fixed by locating the current `renders per-exercise Hebrew adjustment explanations...` and `renders verbal effort adjustment...` tests, then inserting the new fixture/test near them.

### Next research target

- Loop 94 should inspect whether the backend provider/context knowledge now distinguishes:
  - ordinary verbal-effort small progressions;
  - substitution-gate holds that require numeric RPE.
- Product question:
  - Does the AI provider context need a compact rule so generated coach text does not tell the user to advance a substitution gate from `בשליטה` alone?

---

## Loop 94 - Compact provider context carries the substitution-gate RPE rule

### Research question

- Backend and UI now distinguish:
  - ordinary verbal effort;
  - substitution progression gates that require numeric RPE before advancing.
- Remaining risk:
  - provider-routed AI responses could still see only `בשליטה=מאמץ מילולי, לא מספר` and tell the user to advance a substitution gate from verbal effort alone.

### Findings extracted

- The full knowledge center already contained the substitution-gate rule:
  - after replacement/regression, require clean completion, `RPE 8` or lower, and no pain before moving one step.
  - if RPE/pain is missing, save the log but do not advance.
- The compact provider payload had the verbal-effort rule, but not the substitution-gate distinction.
- The provider context is tightly budgeted, so the rule needed to be added without increasing payload size.

### Changes made

- Updated `backend/app/services/coaching_knowledge.py`:
  - compact `coaching_behavior` now includes:
    - `שער החלפה:RPE 1-10+כאב`
  - kept existing compact-language contracts:
    - `עברית ישראלית טבעית`
    - `RPE/RIR/DOMS`
    - `סטים/חזרות לא מערכות`
    - `דילואד/progressive overload`
    - `בלי bullet`
    - `לא לנחש`
  - shortened adjacent coaching behavior lines to preserve budget.
- Updated `backend/tests/test_coaching_knowledge.py`:
  - provider budget test now requires the compact substitution-gate rule.
- Updated `backend/tests/test_token_optimization.py`:
  - optimized workout-log request test now requires:
    - `מאמץ מילולי` and `לא מספר`;
    - `שער החלפה`, `RPE 1-10`, and `כאב`;
    - rule survives `optimized.input_components["tools"]`.

### Tests and checks

- Initial focused knowledge test failed:
  - `len(str(workout_context)) == 8385`, over the `<8350` budget.
- First compression restored the budget but broke existing language guidance expectations:
  - missing `עברית ישראלית טבעית`
  - missing `דילואד/progressive overload`
  - missing `bullet`
- Final compact wording preserved those contracts and stayed under budget.
- Knowledge budget test:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom --basetemp .pytest-tmp-loop94-knowledge-budget-7`
  - Result: `1 passed`.
- Full knowledge tests:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop94-knowledge-full-7`
  - Result: `112 passed`.
- Token optimization tests:
  - `python -m pytest backend/tests/test_token_optimization.py --basetemp .pytest-tmp-loop94-token-full-3`
  - Result: `5 passed`.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- Manual optimized context probe with the correct nested shape showed compact `coaching_behavior` contains:
  - `מאמץ מילולי לא מספר`
  - `שער החלפה:RPE 1-10+כאב`
- PowerShell corrupted Hebrew literals in boolean checks, so the durable proof is the UTF-8 pytest assertions.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One compact sentence and two assertions.
  - No budget increase.
  - No new provider prompt section.

### Failures and fixes

- Multiple provider-budget failures caught prompt bloat.
- Fixed by compressing only neighboring compact behavior wording, not by raising limits.
- Manual PowerShell Hebrew substring checks were unreliable; replaced with normal pytest assertions.

### Next research target

- Loop 95 should inspect if any remaining tests/docs still describe progression gates as `RPE/כאב` without explaining the verbal-effort save path.
- Focus areas:
  - `CALO BRAIN/01_PRODUCT/02-Product-Behavior.md`
  - `CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md`
  - `backend/tests/test_coaching_knowledge.py` assertions around progression gates.

---

## Loop 95 - Docs and full knowledge distinguish saving verbal effort from advancing gates

### Research question

- Behavior now says:
  - verbal effort can be saved;
  - substitution/regression gates still require numeric RPE and pain status before advancing.
- Remaining risk:
  - source-of-truth docs or knowledge tests could still describe progression gates as only `RPE/כאב` without the verbal-effort save path.

### Findings extracted

- Product behavior docs mentioned verbal effort preservation but not the substitution-gate advance rule.
- Prompt registry mentioned not inventing numeric RPE/RIR from verbal effort but not the gate rule.
- Full knowledge already had several RPE/pain gate rules, but assertions did not require the explicit `מאמץ מילולי` save-vs-advance distinction.

### Changes made

- Updated `CALO BRAIN/01_PRODUCT/02-Product-Behavior.md`:
  - after substitution/regression gate, verbal effort can be saved;
  - advancing requires numeric `RPE 1-10` plus pain status;
  - if missing, keep the current version and ask for the missing signal.
- Updated `CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md`:
  - provider prompts must save verbal effort but not advance a substitution/regression progression gate from verbal effort alone.
- Updated `backend/app/services/coaching_knowledge.py`:
  - scoped edit rule now says verbal effort is saved but not enough to raise a step without RPE/pain.
  - RPE/RIR calibration rule now explicitly covers `לוג חופשי או מאמץ מילולי` aimed at a progression gate.
- Updated `backend/tests/test_coaching_knowledge.py`:
  - assertions now require `מאמץ מילולי` in the relevant progression-gate knowledge rules.

### Tests and checks

- Knowledge tests:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop95-knowledge`
  - Result: `112 passed`.
- Documentation/knowledge grep:
  - confirmed `RPE 1-10`, `verbal effort can be saved`, `do not advance`, and `מאמץ מילולי` appear in the intended docs/rules.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- No runtime behavior changed in this loop.
- Product proof is documentation alignment plus knowledge assertions.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - One doc bullet, one prompt-registry bullet, two knowledge sentence updates, two assertions.
  - No new runtime path.

### Failures and fixes

- No failing tests after implementation.

### Next research target

- Loop 96 should run a consolidated affected test matrix for the verbal-effort / substitution-gate changes:
  - backend dashboard, workout logs, training adaptation, coaching knowledge, token optimization;
  - frontend WorkoutsPanel and DashboardPanel;
  - frontend build.
- Product question:
  - Are there cross-file regressions hidden by only running focused tests in separate loops?

---

## Loop 96 - Consolidated affected test matrix for verbal-effort gate work

### Research question

- Several loops changed related behavior across backend services, provider context, docs, and frontend UI.
- Product question:
  - Are there cross-file regressions hidden by focused tests from individual loops?

### Findings extracted

- No cross-file regression surfaced in the affected matrix.
- The backend now consistently saves verbal effort, avoids fake RPE/RIR, and holds substitution gates without numeric RPE.
- The frontend now allows verbal effort logging while explaining that numeric RPE is required only to advance the gate.

### Tests and checks

- Dashboard API:
  - `python -m pytest backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop96-dashboard`
  - Result: `15 passed`.
- Workout logs API:
  - `python -m pytest backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-loop96-workout-logs`
  - Result: `31 passed`.
- Training adaptation:
  - `python -m pytest backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop96-training`
  - Result: `15 passed`.
- Coaching knowledge:
  - `python -m pytest backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop96-knowledge`
  - Result: `112 passed`.
- Token optimization:
  - `python -m pytest backend/tests/test_token_optimization.py --basetemp .pytest-tmp-loop96-token`
  - Result: `5 passed`.
- WorkoutsPanel:
  - `npm.cmd --prefix frontend test -- --run WorkoutsPanel.test.tsx`
  - Result: `22 passed`.
- DashboardPanel:
  - `npm.cmd --prefix frontend test -- --run DashboardPanel.test.tsx`
  - Result: `4 passed`.
- Frontend build:
  - `npm.cmd run build`
  - Result: passed.
- `git diff --check`:
  - Clean; CRLF warnings only.

### Manual/product check

- This loop was automated verification only.
- Previous manual probes already covered:
  - Hebrew return-after-break tracking copy;
  - qualitative `כבד מדי` dashboard behavior;
  - substitution gate hold after `היה בשליטה בלי כאב` without RPE.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Verification matrix only.
  - No new abstractions or scope expansion.

### Failures and fixes

- No failures in the consolidated affected matrix.

### Next research target

- Loop 97 should return to the plan-horizon builder quality itself:
  - inspect single workout, weekly, two-week, and monthly generated outputs after the recent logging/gate changes.
  - manually probe Hebrew requests for each horizon.
  - look for whether plan copy still feels like generic templates instead of horizon-specific coaching.

---

## Loop 97 - Re-audit plan horizons with broader coach/practitioner sources

### Research question

- After the verbal-effort and progression-gate changes, do the four plan horizons still produce distinct, practical Hebrew plans?
- Does the saved plan object carry the broader source base the product now uses, including practitioner/coaching sources and Israeli Hebrew pages?

### Sources reviewed

- ACSM updated resistance training guidelines:
  - https://acsm.org/resistance-training-guidelines-update-2026/
  - Findings: consistency beats a "perfect" routine; advanced techniques and frequent failure are optional for general healthy adults; progression should remain goal-specific and sustainable.
- NSCA resistance training frequency:
  - https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
  - Findings: beginners usually benefit from 2-3 nonconsecutive full-body sessions; intermediates can use 3-4 days and split routines to protect recovery.
- HPRC / NSCA exercise order:
  - https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training
  - Findings: place power/technical work first, then multi-joint/core work, then assistance work; fatigue increases form breakdown risk.
- Wingate strength training article:
  - https://wingate.org.il/%D7%90%D7%99%D7%9E%D7%95%D7%A0%D7%99-%D7%9B%D7%95%D7%97-%D7%95%D7%AA%D7%95%D7%97%D7%9C%D7%AA-%D7%97%D7%99%D7%99%D7%9D-%D7%90%D7%A8%D7%95%D7%9B%D7%94/
  - Findings: Hebrew public-facing framing emphasizes functional strength, health, and realistic expectations, not only hypertrophy language.
- FitStreet Hebrew coach-authored plan-building article:
  - https://fitstreet.co.il/workout-plan/
  - Findings: choose a goal, choose a weekly frequency the user can maintain, select exercises by movement pattern, prefer accessible exercises that can be progressed, and keep rest between the same muscle groups.
- Fitnessophy Hebrew workout-plan guide:
  - https://www.fitnessophy.com/workout-plans/
  - Findings: FBW is common for beginners and can run 2-4 times weekly with rest between sessions; AB/full-body split language is natural Hebrew user language.
- RP Strength volume landmarks:
  - https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth
  - Findings: volume is useful only inside recoverable bounds; track performance, soreness/recovery, and adjust weekly instead of adding sets blindly.
- Stronger by Science complete strength guide:
  - https://www.strongerbyscience.com/complete-strength-training-guide/
  - Findings: strength planning should respect lift practice, technical skill, joints/connective tissue, and training stage.
- Barbell Medicine pain in training:
  - https://www.barbellmedicine.com/blog/pain-in-training-what-do/
  - Findings: pain-related programming should find a tolerable entry point, adjust load/range/exercise/tempo/frequency, and progress only with stable 24-48h symptoms.
- Facebook search attempt:
  - Public Facebook search/pages were not accessible through the current search/browser path, so I did not encode Facebook-specific claims. I used accessible coach-authored Israeli pages instead.

### Findings extracted

- The current builder already separates `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan` in persisted objects and progression schedules.
- The current Hebrew API path correctly infers:
  - single workout from "תן לי אימון יחיד קצר בבית עכשיו";
  - weekly plan from "תבנה לי תוכנית שבועית למתחיל בלי ציוד";
  - two-week plan from "תבנה לי תוכנית לשבועיים עם משקולות יד בלבד";
  - monthly gym plan from "תבנה לי תוכנית חודשית לחדר כושר לחיזוק ועלייה במסת שריר".
- The chat route also behaves correctly:
  - single workout is saved as `single_workout` and does not replace an active plan;
  - weekly plan is saved as `weekly_plan` and becomes current.
- Product gap found:
  - the generated plan's `source_refs` did not include the broader RP / Stronger by Science / Barbell Medicine practitioner references, even though the knowledge center already uses related concepts.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - added `RP Strength training volume landmarks`;
  - added `Stronger by Science complete strength training guide`;
  - added `Barbell Medicine pain in training`.
- Updated `backend/tests/test_workout_plans_api.py`:
  - the source-backed four-week plan test now verifies RP Strength and Barbell Medicine are included in saved plan source references.

### Tests and checks

- `python -m pytest backend/tests/test_workout_plan_builder.py --basetemp .pytest-tmp-loop97-builder`
  - Result: `5 passed`.
- First targeted source-ref test command used the old test name:
  - Result: no tests collected.
  - Fix: reran with the current test name.
- `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_builds_source_backed_four_week_upper_lower_plan --basetemp .pytest-tmp-loop97-source-refs`
  - Result: `1 passed`.
- `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons --basetemp .pytest-tmp-loop97-horizons`
  - Result: `1 passed`.
- `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop97-workout-plans`
  - Result: `32 passed`.
- `git diff --check`
  - Clean; CRLF warnings only.

### Manual Hebrew checks

- Initial manual probe with raw Hebrew in PowerShell was invalid:
  - all prompts fell back to `monthly_plan`;
  - root cause was shell encoding, not product behavior.
- Repeated the same probe with Unicode escapes:
  - single: `single_workout`, `duration_weeks=1`, `days_per_week=1`, one progression item, tracking includes `מאמץ מילולי`;
  - weekly: `weekly_plan`, `duration_weeks=1`, one progression item, tracking includes `מאמץ מילולי`;
  - two-week: `two_week_plan`, `duration_weeks=2`, `equipment=["dumbbells"]`, two progression items;
  - monthly gym: `monthly_plan`, `duration_weeks=4`, gym equipment inferred, four progression items.
- Chat route:
  - single workout reply states it is one-off and does not replace the active plan;
  - weekly reply creates a current weekly plan and gives one next action with RPE/verbal-effort/pain tracking.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - No new architecture, no new schema, no prompt rewrite.
  - Only persisted source references and one existing test were touched.

### Failures and fixes

- Raw-Hebrew PowerShell probe produced a false negative due encoding.
  - Fixed by rerunning with Unicode escapes.
- One pytest command used a stale test name.
  - Fixed by locating and running the current test.

### Next research target

- Loop 98 should inspect whether generated plans expose enough goal intent in saved data and chat copy when the user asks for a mixed goal such as strength plus hypertrophy.
- Specific question:
  - Does a Hebrew prompt like "לחיזוק ועלייה במסת שריר" pick the right primary goal, and does the plan explain the tradeoff without asking unnecessary follow-up questions?

## Loop 98 - Mixed Hebrew strength + hypertrophy intent

### Research sources

- ACSM 2026 resistance training guidelines update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
  - Findings: resistance training should be individualized; strength emphasis uses heavier loads while hypertrophy emphasizes higher weekly volume. Consistency and adherence remain more important than complex programming for most adults.
- NSCA resistance training frequency:
  - https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
  - Findings: frequency depends on training status, overall workload, and recovery. Intermediate users can use 3-4 weekly sessions with split routines to raise frequency while preserving recovery.
- Stronger by Science complete strength training guide:
  - https://www.strongerbyscience.com/complete-strength-training-guide/
  - Findings: strength requires muscle size, lift-specific practice, healthy connective tissue, and stage-aware programming; mixed goals should not chase every outcome equally.
- RP Strength training volume landmarks:
  - https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth
  - Findings: hypertrophy planning should manage working sets, RIR, progression, and recovery limits rather than blindly adding volume.

### Findings extracted

- A prompt like "תבנה לי תוכנית חודשית לחדר כושר לחיזוק ועלייה במסת שריר" has two legitimate goals:
  - strength signal: "לחיזוק";
  - hypertrophy signal: "עלייה במסת שריר".
- The existing builder picked `build_muscle`, which is acceptable because the user explicitly asks for mass gain, but the bot did not explain that assumption.
- Product rule extracted:
  - when a Hebrew request mixes strength and muscle-mass language, choose one primary goal without asking a questionnaire, but persist and surface the tradeoff as an assumption.
- Pure "לחיזוק" without muscle-mass language should infer `improve_strength`.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - added compact strength and hypertrophy signal helpers;
  - pure Hebrew "לחיזוק" now routes to `improve_strength`;
  - mixed strength + muscle-mass requests now persist an assumption that muscle building is the primary focus and strength will progress through the main exercises.
- Updated `backend/tests/test_workout_plans_api.py`:
  - added coverage for mixed Hebrew strength + muscle-mass requests;
  - added coverage that "לחיזוק" alone stays on the strength path.

### Tests and checks

- First run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_handles_mixed_hebrew_strength_and_muscle_goal --basetemp .pytest-tmp-loop98-mixed-goal`
  - Result: failed because the assertion expected "מוקד ראשי" while the bot returned the more natural "המוקד הראשי".
  - Fix: corrected the test to match the actual Hebrew phrasing.
- Second run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_handles_mixed_hebrew_strength_and_muscle_goal --basetemp .pytest-tmp-loop98-mixed-goal`
  - Result: failed because the test overfit strength reps as `4-6`, while the generated strength path used `5-8` with 120-second rest and 1-2 RIR.
  - Fix: asserted strength-path markers instead of an overly specific first-exercise rep range.
- Final targeted run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_handles_mixed_hebrew_strength_and_muscle_goal --basetemp .pytest-tmp-loop98-mixed-goal`
  - Result: `1 passed`.
- Full relevant API file:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop98-workout-plans`
  - Result: `33 passed`.
- `git diff --check`
  - Clean; CRLF warnings only.

### Manual Hebrew checks

- `/api/chat` prompt:
  - "תבנה לי תוכנית חודשית לחדר כושר לחיזוק ועלייה במסת שריר"
- Result:
  - status `200`;
  - reply key is `response`;
  - saved plan type: `monthly_plan`;
  - saved goal: `build_muscle`;
  - reply includes the assumption that the request combined strength and muscle mass, that muscle building is the primary focus, and that strength progresses through the main exercises;
  - no long questionnaire was asked.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Two helper functions, one persisted assumption, one focused API test.
  - No schema change, no new routing layer, no prompt rewrite.

### Failures and fixes

- Test phrasing was too brittle around Hebrew copy.
  - Fixed by matching the actual natural phrase.
- Test overfit a specific strength rep range.
  - Fixed by checking safer strength-path markers: goal, progression rule, rest, and RIR note.

### Next research target

- Loop 99 should inspect plan updates after the saved plan exists:
  - When the user says in Hebrew "תחליף לי תרגיל" or "אין לי מכונה/ספסל" after a monthly plan, does the bot update the structured plan narrowly instead of rebuilding a new plan?
  - Verify saved `plan_edit_history`, exercise substitutions, safety behavior, and chat copy.

## Loop 99 - Scoped saved-plan edits for unavailable cable equipment

### Research sources

- ACSM 2026 resistance training guidelines update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
  - Findings: programs should be individualized for goals, enjoyment and safety; nontraditional tools such as bands, bodyweight and home routines can still support strength and hypertrophy.
- NSCA resistance training frequency:
  - https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
  - Findings: training frequency and split structure should respect training status, workload, recovery and practical schedule constraints.
- Stronger by Science complete strength training guide:
  - https://www.strongerbyscience.com/complete-strength-training-guide/
  - Findings: strength planning depends on specific practice, muscle size, joint/connective tissue health and stage-aware prioritization.
- RP Strength training volume landmarks:
  - https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth
  - Findings: exercise choice and volume should be adjusted to recovery capacity; replacements should preserve the target stimulus instead of blindly adding work.

### Findings extracted

- Existing code already supported several high-value scoped edits:
  - no bench;
  - row machine unavailable;
  - push-up too hard;
  - knee/shoulder/low-back pain substitutions;
  - temporary volume reduction.
- Manual probe found a real Hebrew gap:
  - user: "אין לי כבלים בתוכנית, תחליף רק את מה שצריך";
  - result before fix: local tool response asked a generic clarification question, while the saved plan still contained cable/pulley names and alternatives.
- Product rule extracted:
  - when missing equipment is clear and scoped, edit only exercises/alternatives that depend on that equipment, preserve the same movement pattern, and do not create a replacement plan candidate.

### Changes made

- Updated `backend/app/services/workout_service.py`:
  - added `remove_cable` scoped edit detection for Hebrew/English cable, cables, כבל, כבלים and פולי;
  - added removal/replacement helpers that strip cable/pulley names and alternatives while preserving movement pattern;
  - syncs the edited plan JSON and workout/exercise rows;
  - writes `plan_edit_history` with `edit_type=remove_cable`.
- Updated `backend/app/services/coaching_knowledge.py`:
  - added scoped-plan-edit rule for missing cable/pulley equipment.
- Updated tests:
  - `backend/tests/test_coach_intent_service.py`;
  - `backend/tests/test_coach_engine.py`;
  - `backend/tests/test_coaching_knowledge.py`.

### Tests and checks

- First focused run:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_scoped_active_plan_edits backend/tests/test_coach_engine.py::test_chat_scoped_cable_unavailable_removes_cable_refs_without_replacement backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols --basetemp .pytest-tmp-loop99-cable-focused`
  - Result: failed because the user-facing message said "בלי לבנות חדשה" instead of the clearer "בלי לבנות תוכנית חדשה".
  - Fix: updated the response copy.
- Focused rerun:
  - same command.
  - Result: `3 passed`.
- Broader scoped edit suite:
  - `python -m pytest backend/tests/test_coach_engine.py -k scoped backend/tests/test_coach_intent_service.py --basetemp .pytest-tmp-loop99-scoped-suite`
  - Result: `12 passed, 121 deselected`.
- `git diff --check`
  - Clean; CRLF warnings only.

### Manual Hebrew checks

- Setup:
  - generated a four-day intermediate gym hypertrophy plan.
- `/api/chat` prompt:
  - "אין לי כבלים בתוכנית, תחליף רק את מה שצריך"
- Result:
  - status `200`;
  - provider status `local_tool`;
  - one saved plan remained;
  - no pending replacement plan was created;
  - `plan_edit_history[-1].edit_type == remove_cable`;
  - `changed_exercises == 12`;
  - exercise names and alternatives no longer contain כבל or פולי;
  - reply gives one next action: perform the no-cable versions, keep the same movement pattern, and log RPE/verbal effort and pain.

### Ponytail Review

- Result:
  - Lean already. Ship.
- Rationale:
  - Adds one scoped edit type and focused tests.
  - No schema change, no route change, no new builder.

### Failures and fixes

- Initial manual probe showed a generic clarification response despite clear missing equipment.
  - Fixed with `remove_cable` scoped edit handling.
- Test caught vague Hebrew copy.
  - Fixed response wording to "בלי לבנות תוכנית חדשה".

### Next research target

- Loop 100 should inspect whether logged workouts after a cable-removal edit keep progression conservative:
  - after the user logs a successful no-cable substituted exercise, does the next workout avoid recommending return to a harder cable/pulley alternative?
  - Verify workout logging, execution plan, progression gate, and dashboard next action.

## Loop 100 - Knowledge-center duplicate cleanup and plan-type vocabulary audit

### Research sources

- Existing source-backed knowledge center:
  - `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
- Runtime plan-type implementation:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/app/services/workout_service.py`
  - `backend/app/schemas.py`
  - `backend/app/api/workouts.py`
- Frontend display path:
  - `frontend/src/planFormatters.ts`
  - `frontend/src/WorkoutsPanel.tsx`

### Findings extracted

- Runtime behavior is already mostly aligned with the four canonical horizons:
  - `single_workout`
  - `weekly_plan`
  - `two_week_plan`
  - `monthly_plan`
- `single_session` remains useful only as an incoming compatibility alias and is normalized to `single_workout` before persistence.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md` had 11 repeated copies of the same knowledge document.
- The duplicate knowledge document repeatedly described `single_session` as the one-off plan vocabulary, which conflicts with the current canonical system.

### Changes made

- Cleaned `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md` from 11 duplicate copies to one source-backed document.
- Added normal frontmatter to the cleaned document.
- Updated the implementation note to say:
  - persistent plans use `weekly_plan`, `two_week_plan`, and `monthly_plan`;
  - one-off plans use `single_workout`;
  - legacy `single_session` is accepted only as an incoming compatibility alias.

### Tests and checks

- Duplicate verification:
  - `rg -n "^# Coaching Knowledge$|^## Implementation$|single_session|single_workout|Multi-week workout plans are capped" "CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md"`
  - Result: one implementation note remains; no repeated document headings.
- Size check:
  - before: 3,707 measured lines / 547,413 characters;
  - after: 344 measured lines / 50,156 characters.
- `git diff --check -- "CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md"`
  - Result: clean.
- First pytest command used a wrong test node name:
  - `test_workout_plan_api_distinguishes_weekly_two_week_and_monthly_horizons`
  - Result: failed because the test name does not exist.
- Corrected focused run:
  - `python -m pytest backend/tests/test_workout_plan_builder.py backend/tests/test_workout_schema.py backend/tests/test_workout_plans_api.py::test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons --basetemp .pytest-tmp-goal-plan-type-doc-clean`
  - Result: `13 passed`.

### Ponytail Review

- Result:
  - Lean enough. Keep compatibility alias; do not split request/response schema yet.
- Rationale:
  - The alias is covered by tests and normalizes before saved output.
  - Splitting schema types now would add code without a current broken user flow.
  - Cleaning the duplicated knowledge document removes real maintenance noise.

### Next research target

- Loop 101 should inspect logged workouts after cable-removal edits:
  - after a successful no-cable substituted exercise log, verify the next workout does not recommend returning to cable/pulley work;
  - check workout logging, execution plan, progression gate, and dashboard next action.

## Loop 101 - Direct workout-log path after cable-removal edit

### Research sources

- Existing scoped edit and progression-gate implementation:
  - `backend/app/services/workout_service.py`
  - `backend/app/services/training_adaptation_service.py`
- Existing route coverage:
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_workout_logs_api.py`
- Source-backed rule already in the knowledge center:
  - equipment substitutions should preserve movement pattern and avoid returning to unavailable equipment.

### Findings extracted

- Chat already had coverage for logging after cable removal:
  - `test_chat_workout_log_after_cable_substitution_keeps_progression_generic`
- The direct `/api/workout-logs` path did not have equivalent regression coverage.
- This matters because the Workouts UI logs structured workouts through `/api/workout-logs`, not through chat.
- Runtime behavior was already correct:
  - after a clean structured log, the adjusted exercise uses `substitution_progression_gate`;
  - `progression_next_step` stays `None`;
  - actionable next-workout fields do not recommend cable/pulley work.

### Changes made

- Added `backend/tests/test_workout_logs_api.py::test_direct_log_after_cable_substitution_keeps_progression_generic`.
- The test creates a one-day gym hypertrophy plan, applies the Hebrew no-cable scoped edit, logs the edited exercise through `/api/workout-logs`, and verifies the next execution plan stays generic and no-cable.
- No production code change was needed.

### Tests and checks

- First focused run:
  - `python -m pytest backend/tests/test_workout_logs_api.py::test_direct_log_after_cable_substitution_keeps_progression_generic backend/tests/test_coach_engine.py::test_chat_workout_log_after_cable_substitution_keeps_progression_generic --basetemp .pytest-tmp-loop101-cable-log-focused`
  - Result: failed because the test treated historical notes like `כבל/פולי חסר` as an actionable cable recommendation.
  - Fix: narrowed the assertion to actionable fields only: exercise name, execution note, and alternatives.
- Focused rerun:
  - same command.
  - Result: `2 passed`.
- Affected regression:
  - `python -m pytest backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_workout_plans_api.py backend/tests/test_dashboard_api.py backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop101-affected`
  - Result: `219 passed`.

### Ponytail Review

- Result:
  - No production code change. Test-only gap closed.
- Rationale:
  - Existing behavior was correct.
  - The missing proof was on the direct logging route used by the UI.
  - Adding another service branch would have been waste.

### Next research target

- Loop 102 should inspect the Dashboard next-action path after scoped substitutions:
  - verify progression-gate/no-cable state appears as a useful next action;
  - verify it does not leak internal reason codes or tell the user to use unavailable equipment.

## Loop 102 - Dashboard next action after no-cable substitution gate

### Research sources

- Dashboard backend:
  - `backend/app/services/dashboard_service.py`
- Workout progression state:
  - `backend/app/services/workout_service.py`
  - `backend/app/services/training_adaptation_service.py`
- Dashboard frontend:
  - `frontend/src/DashboardPanel.tsx`
  - `frontend/src/formatters.ts`

### Findings extracted

- The Dashboard already summarizes `substitution_progression_gate` through `next_workout.progression_gate`.
- Existing dashboard tests covered a regressed push-up progression gate and missing-RPE hold.
- No dashboard test covered the no-cable scoped-edit flow.
- The frontend does not generate dashboard guidance itself; it renders `next_recommended_action` from the backend and has separate tests for not leaking raw reason codes.

### Changes made

- Added `backend/tests/test_dashboard_api.py::test_dashboard_no_cable_progression_gate_does_not_recommend_unavailable_equipment`.
- The test builds a one-day gym plan, applies the Hebrew no-cable edit, logs the edited exercise through `/api/workout-logs`, then checks `/api/dashboard`.
- Verified:
  - `progression_gate` is present;
  - the next action says to progress one step conservatively and log instead of guessing;
  - the action does not leak `substitution_progression_gate`;
  - the action does not recommend `כבל` or `פולי`.
- No production code change was needed.

### Tests and checks

- Focused dashboard run:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_no_cable_progression_gate_does_not_recommend_unavailable_equipment backend/tests/test_dashboard_api.py::test_dashboard_surfaces_progression_gate_after_regressed_exercise_clean_log backend/tests/test_dashboard_api.py::test_dashboard_holds_progression_gate_after_verbal_effort_without_rpe --basetemp .pytest-tmp-loop102-dashboard-cable`
  - Result: `3 passed`.
- Affected backend regression:
  - `python -m pytest backend/tests/test_dashboard_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coach_engine.py backend/tests/test_training_adaptation_service.py --basetemp .pytest-tmp-loop102-affected`
  - Result: `181 passed`.
- Frontend dashboard check:
  - `npm.cmd --prefix frontend test -- DashboardPanel.test.tsx --run`
  - Result: `4 passed`.

### Ponytail Review

- Result:
  - Test-only proof. No production code needed.
- Rationale:
  - Backend behavior was already correct.
  - Frontend is a renderer for the backend action, so duplicating logic in UI would be wrong.

### Next research target

- Loop 103 should inspect current prompt/context size after the knowledge-center rebuild:
  - verify provider context still contains the workout-plan horizon protocols;
  - verify provider context does not carry the full duplicated knowledge document;
  - run token/context tests and fix only real prompt bloat or dropped critical rules.

## Loop 103 - Provider context horizon types and prompt budget

### Research sources

- Provider knowledge projection:
  - `backend/app/services/coaching_knowledge.py`
- Token/context compaction:
  - `backend/app/services/token_budgeting.py`
  - `backend/app/services/context_builder.py`
- Existing regression coverage:
  - `backend/tests/test_coaching_knowledge.py`
  - `backend/tests/test_context_builder.py`
  - `backend/tests/test_token_optimization.py`

### Findings extracted

- The full knowledge center already contains `plan_horizon_protocols` for:
  - `single_workout`
  - `weekly_plan`
  - `two_week_plan`
  - `monthly_plan`
- The provider context correctly does not send the full protocol table to the model.
- The compact provider context did include `plan_horizon_summary`, but the summary only said "אימון יחיד/שבוע/שבועיים/חודש".
- That was human-readable, but it did not carry stable canonical type markers into the optimized prompt.
- Adding canonical markers directly to the compact summary is lower risk than sending the whole protocol table.

### Changes made

- Updated `backend/app/services/coaching_knowledge.py`:
  - `plan_horizon_summary` now includes the canonical ids `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan`.
  - Kept the summary short enough to survive `_KNOWLEDGE_LIMITS["plan_horizon_summary"]`.
  - Reduced provider `safety_boundaries` projection from 3 items to 2 items to preserve prompt headroom without weakening the full knowledge center.
- Updated `backend/tests/test_coaching_knowledge.py`:
  - provider context now asserts the compact horizon summary includes canonical plan ids.
- Updated `backend/tests/test_token_optimization.py`:
  - compact workout-plan context now asserts those ids survive `compact_provider_context`.

### Tests and checks

- Manual provider-context probe:
  - provider `plan_horizon_summary` length: `136`.
  - compact `plan_horizon_summary` length: `136`.
  - compact context retained all four ids.
- Focused run:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_full_coach_summaries_for_workout_plan backend/tests/test_token_optimization.py::test_compact_workout_plan_context_keeps_builder_rules_and_retrieved_actions backend/tests/test_context_builder.py::test_context_builder_includes_compact_coaching_knowledge --basetemp .pytest-tmp-loop103-focused`
  - Result: `3 passed`.
- Wider context/token run:
  - `python -m pytest backend/tests/test_coaching_knowledge.py backend/tests/test_context_builder.py backend/tests/test_token_optimization.py --basetemp .pytest-tmp-loop103-context`
  - First result: `3 failed, 138 passed`.
  - Failure reason: `workout_plan` provider context grew from the new horizon markers and exceeded the existing `< 8350` prompt budget guard.
  - Fix: trim provider-only `safety_boundaries` projection from 3 items to 2.
  - Rerun result: `141 passed`.

### Ponytail Review

- Result:
  - Small provider-context patch, not a prompt rewrite.
- Rationale:
  - Canonical ids solve the routing/schema ambiguity directly.
  - Sending the whole protocol table would increase prompt size and duplicate existing knowledge retrieval.
  - Raising the prompt budget would hide the regression instead of fixing it.

### Next research target

- Loop 104 should manually test Hebrew workout-plan conversations through the real chat path:
  - single workout request;
  - weekly plan request;
  - two-week plan request;
  - monthly plan request;
  - pain/missing-critical-info case;
  - verify the bot asks one critical question only when needed and saves structured plans with the right `plan_type`.

## Loop 104 - Hebrew chat probes for plan horizons

### Research sources

- Chat orchestration and routing:
  - `backend/app/services/coach_engine.py`
  - `backend/app/services/coach_intent_service.py`
- Workout plan persistence:
  - `backend/app/services/workout_service.py`
  - `backend/app/services/workout_plan_builder.py`
- Existing Hebrew chat regression tests:
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_coach_intent_service.py`
  - `backend/tests/test_workout_plans_api.py`

### Findings extracted

- Existing tests already cover natural Hebrew plan requests for:
  - one-off/single workout;
  - weekly plan;
  - two-week plan;
  - monthly plan;
  - vague pain before plan generation;
  - current-plan replacement/candidate behavior.
- The real chat path uses `CoachIntentService -> CoachEngine -> WorkoutService -> WorkoutPlanBuilder`.
- Single workouts are saved as structured `WorkoutPlan` records but are not made current.
- Persistent plans use current/candidate behavior:
  - the first persistent plan becomes current;
  - a later persistent plan becomes a replacement candidate until the user confirms.
- Vague pain with a plan request asks one critical safety question and does not save a plan.

### Manual Hebrew conversation probe

- Ran a temporary `/api/chat` probe through `TestClient` with onboarding loaded.
- Messages tested:
  - `תן לי אימון יחיד היום בבית 30 דקות`
  - `תבנה לי תוכנית שבועית למתחיל בלי ציוד`
  - `תבנה לי תוכנית לשבועיים עם משקולות`
  - `תבנה לי תוכנית חודשית של 4 ימים בחדר כושר להיפרטרופיה, אני ברמה בינונית`
  - `יש לי כאב, תבנה לי תוכנית כוח`
- Results:
  - single: `200`, `local_tool`, latest saved `plan_type=single_workout`, `is_current=False`.
  - weekly: `200`, `local_tool`, latest saved `plan_type=weekly_plan`, `is_current=True`.
  - two-week: `200`, `local_tool`, latest saved `plan_type=two_week_plan`, `is_current=False` because a current weekly plan already existed.
  - monthly: `200`, `local_tool`, latest saved `plan_type=monthly_plan`, `is_current=False` because a current persistent plan already existed.
  - vague pain: `200`, `local_tool`, plan count unchanged, response asks where the pain is and whether it is sharp/worsening/limiting movement.

### Changes made

- No production code change.
- No new test added in this loop because existing targeted tests already cover the behavior and the manual probe confirmed the end-to-end chat path.

### Tests and checks

- Focused Hebrew chat run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_weekly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving --basetemp .pytest-tmp-loop104-hebrew-chat-focused`
  - Result: `5 passed`.
- Affected chat/planning run:
  - `python -m pytest backend/tests/test_coach_engine.py backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plan_builder.py --basetemp .pytest-tmp-loop104-chat-affected`
  - Result: `124 passed`.

### Ponytail Review

- Result:
  - No code change.
- Rationale:
  - The requested behavior already has targeted regression tests.
  - Adding a broad duplicate test would make the suite slower without improving failure localization.
  - The manual probe gives end-to-end proof through the real chat route.

### Next research target

- Loop 105 should inspect missing critical info behavior in more detail:
  - verify the bot does not ask a long questionnaire for minimal plan requests;
  - verify assumptions are persisted in `decision_inputs`;
  - verify pain/location/equipment questions remain one-question and only appear when critical.

## Loop 105 - Missing critical info vs safe assumptions

### Research sources

- Planning defaults and persisted assumptions:
  - `backend/app/services/workout_service.py`
  - `backend/app/services/workout_plan_builder.py`
- Pain clarification text:
  - `backend/app/services/pain_text.py`
- Existing API and chat tests:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- The planner already distinguishes critical and non-critical missing information.
- Non-critical missing info is inferred conservatively and persisted in `decision_inputs.assumptions`.
- Minimal plan requests do not trigger a long questionnaire.
- Single-workout requests without a duration default to 30 minutes instead of asking.
- Persistent plan requests without a duration default to 45 minutes.
- Missing equipment defaults to bodyweight when no profile or prompt equipment exists.
- Vague pain with a plan request is treated as critical:
  - no plan is saved;
  - the response asks one safety question about pain location and whether it is sharp/worsening/limiting movement.
- Scoped plan edits with vague pain also ask one question and do not mutate the active plan.

### Changes made

- No production code change.
- No new test added because the relevant behaviors already have focused regression tests.

### Tests and checks

- Focused missing-info run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_conservative_assumptions_for_minimal_prompt backend/tests/test_workout_plans_api.py::test_single_workout_without_duration_defaults_to_short_practical_session backend/tests/test_workout_plans_api.py::test_workout_plan_api_requires_pain_area_for_vague_soft_pain backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request backend/tests/test_coach_engine.py::test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving backend/tests/test_coach_engine.py::test_chat_vague_scoped_plan_edit_asks_one_question_without_changing_plan --basetemp .pytest-tmp-loop105-missing-info-focused`
  - Result: `6 passed`.

### Ponytail Review

- Result:
  - No code change.
- Rationale:
  - The implementation already matches the desired behavior.
  - Adding duplicate tests would not improve failure granularity.
  - The next useful work is a different risk area, not rewriting defaults that are already covered.

### Next research target

- Loop 106 should inspect progression schedules inside saved plans:
  - weekly plans should not pretend to have multi-week progression;
  - two-week plans should clearly describe week 1 and week 2;
  - monthly plans should show week 1-4 progression/recovery;
  - progression should differ by experience level and goal where relevant.

## Loop 106 - Horizon-specific progression schedules

### Research sources

- Progression schedule generator:
  - `backend/app/services/workout_plan_builder.py`
- API plan serialization and persistence:
  - `backend/app/services/workout_service.py`
- Existing progression tests:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_workout_plan_builder.py`

### Findings extracted

- Progression schedules are already separated by horizon:
  - `single_workout`: one execution/logging instruction, no forced progression.
  - `weekly_plan`: one-week execution and tracking only.
  - `two_week_plan`: week 1 baseline, week 2 progression only if logs are stable.
  - `monthly_plan`: four-week sequence with calibration, progression, and week 4 check/maintenance or volume reduction.
- Monthly plans already had explicit beginner vs advanced progression coverage.
- Two-week plans had beginner/intermediate/advanced logic in production, but no dedicated API test proving beginner vs advanced behavior.

### Changes made

- Added `backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level`.
- The test verifies:
  - beginner two-week plan uses `RPE 5-7`;
  - beginner week 2 does not progress or add sets if week 1 is not stable;
  - advanced two-week plan uses `RPE 7-9`;
  - advanced week 2 permits one accessory set only when logs are stable;
  - advanced fallback can reduce `20-30%` volume.
- No production code change was needed.

### Tests and checks

- New focused test:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level --basetemp .pytest-tmp-loop106-two-week-progression`
  - Result: `1 passed`.
- Progression focused run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level backend/tests/test_workout_plan_builder.py --basetemp .pytest-tmp-loop106-progression-focused`
  - Result: `10 passed`.
- Full workout plan API run:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop106-workout-plans-api`
  - Result: `40 passed`.

### Ponytail Review

- Result:
  - Test-only change.
- Rationale:
  - Production behavior already matched the desired rule.
  - The missing value was regression coverage for two-week beginner vs advanced progression.

### Next research target

- Loop 107 should inspect exercise selection by goal and equipment:
  - hypertrophy vs strength vs endurance vs mobility first exercise and rep/rest choices;
  - bodyweight/home/gym/dumbbells-only equipment constraints;
  - ensure substitutions and alternatives do not leak unavailable equipment.

## Loop 107 - Exercise selection and equipment leakage

### Research sources

- Exercise catalog and selection:
  - `backend/app/services/workout_plan_builder.py`
- Existing API/chat equipment coverage:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- Goal-specific exercise selection was already covered for:
  - strength: lower reps, longer rest;
  - hypertrophy: 8-12 reps and volume progression;
  - fat loss support: strength plus short rests and light aerobic note;
  - endurance: first action is base aerobic work;
  - mobility: first actions are mobility and balance.
- Equipment-specific names were mostly correct.
- Real issue found:
  - bodyweight/no-equipment plans did not leak unavailable equipment in exercise names or alternatives;
  - but progression/regression text for pull movements could still say `גומייה`;
  - dumbbells-only plans could include `ספסל` in a horizontal pull alternative.
- This is a product issue because users asking for `בלי ציוד` or `משקולות יד בלבד` should not receive unavailable equipment in any actionable field.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`:
  - horizontal pull progression/regression now depends on equipment mode.
  - vertical pull progression/regression now depends on equipment mode.
  - dumbbells-only horizontal pull alternative no longer uses a bench.
  - dumbbells-only horizontal push alternative no longer implies incline bench work.
  - glute bridge alternatives now depend on equipment mode.
- Updated `backend/tests/test_workout_plans_api.py`:
  - strengthened `test_workout_plan_tailors_exercises_by_equipment_and_experience`.
  - The test now scans all days and checks exercise name, notes, alternatives, progression, and regression.
  - It asserts no `גומייה`, `ספסל`, `כבל`, `פולי`, or `מכונה` leaks into bodyweight/no-equipment or dumbbells-only plans.

### Tests and checks

- Focused equipment test:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience --basetemp .pytest-tmp-loop107-equipment-focused`
  - Result: `1 passed`.
- Manual API probe:
  - bodyweight plan equipment: `['bodyweight']`.
  - dumbbells-only plan equipment: `['dumbbells']`.
  - actionable exercise text for both had no `גומייה`, `ספסל`, `כבל`, `פולי`, or `מכונה`.
- Affected regression:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py::test_chat_endpoint_infers_hebrew_single_workout_gym_duration_and_uses_neutral_saved_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_scoped_cable_unavailable_removes_cable_refs_without_replacement backend/tests/test_coach_engine.py::test_chat_scoped_no_bench_edit_updates_current_plan_without_replacement --basetemp .pytest-tmp-loop107-equipment-affected`
  - Result: `45 passed`.

### Ponytail Review

- Result:
  - Small domain fix plus stronger regression coverage.
- Rationale:
  - The bug was in actionable exercise text, not in routing or prompt wording.
  - Fixing at the catalog helper level prevents the same leak across API and chat.
  - No new abstraction beyond small mode-specific helpers was needed.

### Next research target

- Loop 108 should inspect structured persistence/read models:
  - `WorkoutPlan`, `Workout`, and `WorkoutExercise` rows should stay aligned after generated plans and scoped edits;
  - serialized API/chat plans should not differ from persisted rows in equipment, alternatives, sets/reps/rest, or plan type.

## Loop 108 - Workout plan JSON and row persistence alignment

### Research sources

- Plan generation and row creation:
  - `backend/app/services/workout_service.py`
- Structured plan model output:
  - `backend/app/services/workout_plan_builder.py`
- Existing row/edit tests:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_workout_logs_api.py`

### Findings extracted

- `WorkoutPlan.plan_json` is the saved structured plan object.
- `Workout` and `WorkoutExercise` rows are created from the structured plan and are used by next-workout and logging flows.
- Scoped edits call `_sync_plan_rows_from_json`, so changed names, sets, reps, rest, notes, and alternatives should propagate from JSON to rows.
- Existing tests checked the existence of at least one row and several scoped-edit row updates.
- Missing proof:
  - there was no API test proving every generated day and every generated exercise row matches the saved plan JSON.

### Changes made

- Added `backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_workout_rows_matching_plan_json`.
- The test generates a two-week dumbbells-only plan and verifies:
  - number of `Workout` rows equals number of days;
  - each row name/difficulty/workout_json matches the plan day;
  - each `WorkoutExercise` row matches name, sets, reps/duration, rest, notes, and alternatives from the corresponding plan exercise.
- No production code change was needed.

### Tests and checks

- New focused test:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_workout_rows_matching_plan_json --basetemp .pytest-tmp-loop108-row-sync-focused`
  - Result: `1 passed`.
- Row sync affected run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_generates_and_saves_structured_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_workout_rows_matching_plan_json backend/tests/test_coach_engine.py::test_chat_scoped_no_bench_edit_updates_current_plan_without_replacement backend/tests/test_coach_engine.py::test_chat_scoped_reduce_volume_edit_updates_sets_without_replacement backend/tests/test_coach_engine.py::test_chat_scoped_cable_unavailable_removes_cable_refs_without_replacement backend/tests/test_coach_engine.py::test_chat_scoped_knee_pain_edit_updates_squat_without_replacement backend/tests/test_workout_logs_api.py::test_direct_log_after_cable_substitution_keeps_progression_generic --basetemp .pytest-tmp-loop108-row-sync-affected`
  - Result: `7 passed`.
- Full workout plan API run:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop108-workout-plans-api`
  - Result: `41 passed`.

### Ponytail Review

- Result:
  - Test-only proof.
- Rationale:
  - Production synchronization already worked.
  - The useful slice was preventing a future bug where JSON and loggable rows drift apart.

### Next research target

- Loop 109 should inspect chat response text quality for saved workout plans:
  - no raw internal split names;
  - no storage-confirmation phrasing as the main value;
  - response should state assumptions briefly, next action, tracking, safety, and correct horizon.

## Loop 109 - Chat response quality and bench-equipment regression

### Research sources

- Chat response formatter:
  - `backend/app/services/coach_engine.py`
- Plan equipment catalog and scoped edits:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/app/services/workout_service.py`
- Chat and workout-plan regression tests:
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_workout_plans_api.py`

### Findings extracted

- The chat formatter already separates:
  - single workout responses;
  - current persistent plan responses;
  - replacement-candidate plan responses.
- Useful user-facing response requirements are present in code:
  - correct horizon label;
  - brief assumptions;
  - first workout / first exercise as the next action;
  - tracking of `RPE` or verbal effort, pain, and what was completed.
- Missing proof:
  - only one chat test checked for raw internal split ids such as `full_body` / `upper_lower`;
  - weekly, two-week, monthly, and single-workout chat paths did not consistently assert no internal plan ids and no storage-confirmation phrasing.
- Regression discovered during wider run:
  - a plan requested with `equipment=["dumbbells", "bench"]` no longer used a bench exercise after the dumbbells-only equipment cleanup;
  - therefore the later "אין לי ספסל" scoped edit had no bench-dependent exercise to change and did not add a `ציוד חסר` note.

### Changes made

- Added `assert_no_raw_plan_labels()` to `backend/tests/test_coach_engine.py`.
- Strengthened chat tests for:
  - English workout-plan request;
  - single workout request with existing current plan;
  - Hebrew inferred single workout;
  - Hebrew weekly plan;
  - Hebrew monthly plan;
  - Hebrew two-week plan.
- Fixed the bench-equipment root cause in `backend/app/services/workout_plan_builder.py`:
  - dumbbells-only plans still avoid bench references;
  - dumbbells-plus-bench plans now use a bench horizontal-push variation;
  - scoped no-bench edits can replace that exercise and mark it as equipment-missing.

### Tests and checks

- Chat response focused run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_workout_plan_intent_to_module backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current backend/tests/test_coach_engine.py::test_chat_endpoint_infers_hebrew_single_workout_gym_duration_and_uses_neutral_saved_response backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_weekly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response --basetemp .pytest-tmp-loop109-chat-response-focused`
  - Result: `6 passed`.
- Initial full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop109-coach-engine`
  - Result: `114 passed, 2 failed`.
  - Real failure: no-bench substitution no longer added `ציוד חסר` because the source plan did not use a bench exercise.
  - Environmental/transient failure: one later test hit `WinError 10055` socket buffer exhaustion after many `TestClient` instances.
- Bench regression focused run after fix:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_workout_log_after_no_bench_substitution_keeps_progression_generic --basetemp .pytest-tmp-loop109-no-bench-fixed`
  - Result: `1 passed`.
- Dumbbells-only guard:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience --basetemp .pytest-tmp-loop109-dumbbells-only-guard`
  - Result: `1 passed`.
- Full chat rerun:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop109-coach-engine-rerun`
  - Result: `116 passed`.

### Ponytail Review

- Result:
  - Small source fix plus stronger response regression tests.
- Rationale:
  - The correct fix was not to weaken the test or add a note artificially during edit.
  - If a user explicitly has a bench, the generated plan may use it; if they later lose access, scoped edit should remove it and gate progression.
  - The dumbbells-only leakage guard stayed intact.

### Next research target

- Loop 110 should research and verify progression and deload language in saved plan outputs:
  - beginner/intermediate/advanced progression should be visible enough for users;
  - monthly plans should include a practical deload/recovery rule;
  - responses should avoid over-prescribing load jumps when logs are missing or pain is present.

## Loop 110 - Progression and deload visibility in saved monthly plans

### Research sources

- ACSM 2026 resistance training guidelines update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
- NSCA preparatory period / periodization overview:
  - https://www.nsca.com/education/articles/kinetic-select/preparatory-period/
- NSCA foundations of fitness programming progression principles:
  - https://www.nsca.com/contentassets/693872c8a25245a7ba49fc5527a236b9/foundations-of-fitness-programming-quiz-preview.pdf
- Frontiers deloading coach-practice research:
  - https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.1073223/full
- NSCA Strength & Conditioning Journal practical deloading review:
  - https://doras.dcu.ie/31501/1/a_practical_approach_to_deloading__recommendations.203%282%29.pdf

### Findings extracted

- ACSM's current emphasis is consistency, individualization, and goal-appropriate load/volume rather than chasing complex programming for general adults.
- NSCA progression guidance treats progressive overload as systematic modification over time: load, sets, reps, rest, frequency, or exercise difficulty.
- NSCA also emphasizes that progression should be individual and based on adaptation speed, not only a pre-written calendar.
- Deloading is a purposeful reduction in training stress to manage fatigue, improve recovery, and prepare the next training cycle.
- Practical deload levers include reducing effort intensity, training volume, duration, frequency, or exercise demand.
- For this product, the useful rule is:
  - monthly plans should keep progression practical but make week 4 a check/deload gate when RPE rises, performance drops, pain accumulates, or adherence slips.

### Changes made

- Updated `backend/app/services/workout_plan_builder.py`.
- Added `_progression_model(plan_type)`.
- Monthly plans now store a top-level `progression_model` that explicitly says:
  - use double progression first;
  - week 4 is a check/deload week;
  - if RPE rises, performance drops, pain accumulates, or sessions are missed, reduce volume by `20-40%` before the next block.
- Weekly and two-week plans keep the simpler double-progression model and do not mention week 4/deload.
- No extra knowledge-center table was added because:
  - `deload_rules`, `program_lifecycle_protocols`, `periodization_summary`, and provider-context `deload_rules` already exist and are tested;
  - the real missing piece was visibility in the saved plan object returned to the user.

### Tests and checks

- Focused progression run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level --basetemp .pytest-tmp-loop110-progression-focused`
  - Result: `3 passed`.
- Affected builder/chat run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response backend/tests/test_coach_engine.py::test_chat_workout_log_after_no_bench_substitution_keeps_progression_generic --basetemp .pytest-tmp-loop110-affected`
  - Result: `44 passed`.
- Manual Hebrew chat probe:
  - Prompt: `תבנה לי תוכנית חודשית למתקדם עם משקל גוף, 3 ימים בשבוע`
  - First attempt failed due PowerShell Hebrew encoding, not app logic; the app correctly returned the mojibake guard.
  - Retried with Unicode escapes.
  - Result: `200`, `provider_status=local_tool`, saved `plan_type=monthly_plan`.
  - Saved `progression_model` includes `שבוע בדיקה/דילואד`, `ביצועים יורדים`, and `20-40% נפח`.

### Ponytail Review

- Result:
  - One small product-visible rule in an existing field.
- Rationale:
  - Adding another periodization subsystem would be premature.
  - The knowledge center already had the source-backed lifecycle/deload rules.
  - The actual product gap was that a user opening a saved monthly plan might not see the recovery gate clearly enough.

### Next research target

- Loop 111 should inspect plan outputs for equipment/location consistency in the visible chat response:
  - home/bodyweight plans should not sound like gym plans;
  - dumbbells-only should not imply unavailable bench/bands/machines;
  - gym plans should still use practical gym equipment when requested.

## Loop 111 - Hebrew bodyweight equipment override

### Research sources

- Equipment inference service:
  - `backend/app/services/workout_service.py`
- Workout-plan exercise catalog:
  - `backend/app/services/workout_plan_builder.py`
- Hebrew chat/API coverage:
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_workout_plans_api.py`

### Findings extracted

- Manual Loop 110 chat probe exposed a real product bug:
  - prompt: `תבנה לי תוכנית חודשית למתקדם עם משקל גוף, 3 ימים בשבוע`;
  - profile equipment: `['dumbbells']`;
  - saved plan still used dumbbells and opened with `סקוואט גביע עם משקולת`.
- Root cause:
  - `_infer_equipment()` recognized `בלי ציוד`, `ללא ציוד`, `bodyweight`, and `no equipment`;
  - it did not recognize the natural Hebrew phrase `משקל גוף`;
  - therefore the service fell back to profile equipment.
- Product rule:
  - explicit equipment in the current user message must override profile equipment;
  - Hebrew `משקל גוף` means bodyweight/no-equipment programming unless the user also requests a specific external tool.

### Changes made

- Strengthened `backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response`.
- The test now verifies:
  - saved `equipment_needed` is `['bodyweight']`;
  - generated plan days do not contain `משקולת`.
- Confirmed failing test before production fix:
  - failure showed `equipment_needed == ['dumbbells']`.
- Updated `backend/app/services/workout_service.py`:
  - `_infer_equipment()` now treats `משקל גוף`, `משקל-גוף`, `body weight`, and `body-weight` as `['bodyweight']`.

### Tests and checks

- Failing proof before fix:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response --basetemp .pytest-tmp-loop111-bodyweight-failing`
  - Result: failed with `['dumbbells'] == ['bodyweight']`.
- Focused rerun after fix:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response --basetemp .pytest-tmp-loop111-bodyweight-fixed`
  - Result: `1 passed`.
- Equipment affected run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_home_plan_prompt_overrides_saved_gym_equipment_when_equipment_missing backend/tests/test_workout_plans_api.py::test_single_workout_plan_infers_hebrew_gym_and_duration_from_prompt_before_profile_defaults backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_workout_plans_api.py::test_workout_plan_api_generates_and_saves_structured_plan backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_workout_log_after_no_bench_substitution_keeps_progression_generic --basetemp .pytest-tmp-loop111-equipment-affected`
  - Result: `7 passed`.
- Manual Hebrew chat probe:
  - Prompt: `תן לי תוכנית מוביליטי חודשית עם משקל גוף`.
  - Profile equipment: valid onboarding payload with dumbbells.
  - Result: `200`, `provider_status=local_tool`, saved `equipment_needed=['bodyweight']`.
  - First exercises: `זרימת מוביליטי ירך-גב-כתף`, `שיווי משקל והעברת משקל`, `סקוואט לקופסה`.
- Full workout-plan API run:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop111-workout-plans-api`
  - Result: `41 passed`.

### Ponytail Review

- Result:
  - One phrase-level inference fix, no architecture change.
- Rationale:
  - The problem was not in the plan builder or response formatter.
  - It was a missing Hebrew phrase in equipment inference.
  - Fixing inference preserves the existing precedence rule: request equipment > inferred equipment > profile equipment > bodyweight default.

### Next research target

- Loop 112 should inspect whether visible chat responses mention equipment/location assumptions clearly enough:
  - if equipment is inferred from the prompt, the response may not need to say it every time;
  - if equipment falls back to a safe assumption, the response should briefly state that assumption;
  - avoid making the response long or questionnaire-like.

## Loop 112 - Prioritize practical assumptions in chat responses

### Research sources

- Assumption generation:
  - `backend/app/services/workout_service.py`
- Chat response formatter:
  - `backend/app/services/coach_engine.py`
- Chat/API assumption coverage:
  - `backend/tests/test_coach_engine.py`
  - `backend/tests/test_workout_plans_api.py`

### Findings extracted

- The saved plan JSON already kept conservative assumptions for minimal requests:
  - default monthly horizon;
  - general fitness goal;
  - 3 workouts/week;
  - 45 minutes;
  - bodyweight;
  - beginner level.
- The visible chat response only showed the first two assumptions.
- For a minimal Hebrew request like `תבנה לי תוכנית אימונים`, the response mentioned horizon and goal but hid the assumptions users need to execute the plan:
  - weekly frequency;
  - session duration;
  - equipment.
- Product rule:
  - do not expose a long questionnaire or dump all assumptions;
  - show up to three practical assumptions, prioritizing execution-critical details.

### Changes made

- Updated `backend/app/services/coach_engine.py`.
- Added `_visible_plan_assumptions()`.
- `_plan_assumptions_text()` now prioritizes assumptions in this order:
  - training days/frequency;
  - session duration;
  - equipment;
  - plan horizon;
  - goal;
  - experience level.
- Visible assumptions are still capped at three items.
- Strengthened `backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request`.

### Tests and checks

- Failing proof before fix:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request --basetemp .pytest-tmp-loop112-assumptions-failing`
  - Result: failed because the response did not include `3 אימונים בשבוע`.
- Focused rerun after fix:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request --basetemp .pytest-tmp-loop112-assumptions-fixed`
  - Result: `1 passed`.
- Affected assumption/chat run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_weekly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current backend/tests/test_coach_engine.py::test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving backend/tests/test_workout_plans_api.py::test_workout_plan_api_persists_conservative_assumptions_for_minimal_prompt --basetemp .pytest-tmp-loop112-chat-assumptions-affected`
  - Result: `6 passed`.
- Manual Hebrew chat probe:
  - Prompt: `תבנה לי תוכנית אימונים`.
  - Result: `200`, `provider_status=local_tool`.
  - Visible assumptions now include:
    - `3 אימונים בשבוע`;
    - `45 דקות`;
    - `משקל גוף`.
  - Saved plan still keeps the full assumption list.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop112-coach-engine`
  - Result: `116 passed`.

### Ponytail Review

- Result:
  - Response-formatting fix only.
- Rationale:
  - The stored structured data was already correct.
  - The gap was display prioritization, not planning logic.
  - Showing three assumptions is still concise and avoids a long questionnaire.

### Next research target

- Loop 113 should inspect safety/pain handling in workout-plan generation:
  - vague pain should ask one critical question and save no plan;
  - scoped mild pain should build conservatively;
  - generated substitutions should not promise diagnosis or treatment.

## Loop 113 - Pain and safety wording for workout-plan generation

### Research sources

- Mayo Clinic warning symptoms during exertion and shortness of breath:
  - https://www.mayoclinic.org/symptoms/shortness-of-breath/basics/when-to-see-doctor/sym-20050890
  - https://www.mayoclinic.org/tests-procedures/stress-test/about/pac-20385234
- Exercise is Medicine low-back pain exercise guidance:
  - https://exerciseismedicine.org/assets/page_documents/EIM%20Rx%20series_Exercising%20with%20Lower%20Back%20Pain_2.pdf
- Barbell Medicine pain-in-training guidance:
  - https://www.barbellmedicine.com/blog/pain-in-training-what-do/
- Safety and pain services:
  - `backend/app/services/safety_service.py`
  - `backend/app/services/pain_text.py`
  - `backend/app/services/coach_engine.py`
  - `backend/app/services/workout_service.py`

### Findings extracted

- Red-flag symptoms during exercise remain hard stops:
  - chest pain;
  - dizziness/fainting;
  - unusual shortness of breath;
  - palpitations.
- Vague pain is missing critical safety information and should ask one short question before generating a plan.
- Mild, localized musculoskeletal pain can be handled as conservative coaching:
  - no diagnosis;
  - reduce load/range/difficulty;
  - stay in a pain-free or non-worsening range;
  - stop if sharp, worsening, radiating, or otherwise concerning.
- Current code already had the right routing:
  - vague pain blocks plan saving;
  - red flags trigger safety override;
  - localized knee pain builds an adapted plan.
- Gap found:
  - the localized-pain chat response did not explicitly say `לא אבחנה`;
  - it said `בניתי את התוכנית סביב זה`, which was acceptable but less conservative than `התאמתי שמרנית לטווח ללא כאב`.

### Changes made

- Strengthened `backend/tests/test_coach_engine.py::test_chat_endpoint_pain_plus_plan_request_builds_modified_plan`.
- The test now requires:
  - `לא אבחנה`;
  - `טווח ללא כאב`;
  - stop/no-pushing-through-pain language;
  - no `ריפוי` or `טיפול` claim.
- Updated `backend/app/services/coach_engine.py` pain acknowledgement:
  - from `בניתי את התוכנית סביב זה`;
  - to `זו לא אבחנה; התאמתי את התוכנית שמרנית לטווח ללא כאב`.

### Tests and checks

- Baseline safety run before wording change:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_pain_plus_plan_request_builds_modified_plan backend/tests/test_coach_engine.py::test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving backend/tests/test_coach_engine.py::test_chat_endpoint_red_flag_blocks_plan_even_with_plan_request backend/tests/test_workout_plans_api.py::test_workout_plan_api_requires_pain_area_for_vague_soft_pain backend/tests/test_workout_plans_api.py::test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan --basetemp .pytest-tmp-loop113-safety-baseline`
  - Result: `5 passed`.
- Failing proof after stronger wording test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_pain_plus_plan_request_builds_modified_plan --basetemp .pytest-tmp-loop113-pain-wording-failing`
  - Result: failed because response did not include `לא אבחנה`.
- Focused rerun after fix:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_pain_plus_plan_request_builds_modified_plan --basetemp .pytest-tmp-loop113-pain-wording-fixed`
  - Result: `1 passed`.
- Safety affected run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_pain_plus_plan_request_builds_modified_plan backend/tests/test_coach_engine.py::test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving backend/tests/test_coach_engine.py::test_chat_endpoint_red_flag_blocks_plan_even_with_plan_request backend/tests/test_coach_engine.py::test_chat_scoped_knee_pain_edit_updates_squat_without_replacement backend/tests/test_coach_engine.py::test_chat_scoped_vague_pain_edit_asks_safety_question_without_changing_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_blocks_red_flag_symptoms_before_saving_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_requires_pain_area_for_vague_soft_pain backend/tests/test_workout_plans_api.py::test_knee_sensitive_plan_avoids_primary_lunge_work --basetemp .pytest-tmp-loop113-safety-affected`
  - Result: `9 passed`.
- Manual Hebrew probes:
  - Vague pain prompt: `יש לי כאב, תבנה לי תוכנית כוח`.
  - Result: `provider_status=local_tool`, asks where/quality of pain, saved plans count `0`.
  - Mild knee pain prompt: `יש לי כאב ברך קל, תבנה לי תוכנית כוח של 2 ימים בלי ציוד`.
  - Result: `provider_status=local_tool`, `safety_flagged=False`, saved `monthly_plan`, limitations `רגישות בברך`, response includes `לא אבחנה`.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop113-coach-engine`
  - Result: `116 passed`.

### Ponytail Review

- Result:
  - Wording hardening only.
- Rationale:
  - The routing and persistence behavior were already correct.
  - The useful improvement was making medical scope explicit in the user-visible response.
  - No new safety subsystem was needed.

### Next research target

- Loop 114 should inspect whether single-workout plans differ enough from persistent plans:
  - single workout should not become current active plan;
  - it should avoid weekly/monthly progression language;
  - it should still include warmup, substitutions, tracking, and safety notes.

## Loop 114 - Single workout progression model separation

### Research sources

- Single-workout builder and persistence:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/app/services/workout_service.py`
- Chat response formatter:
  - `backend/app/services/coach_engine.py`
- Existing single-workout coverage:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- Single workouts were already correctly separated at persistence level:
  - `plan_type=single_workout`;
  - `duration_weeks=1`;
  - `days_per_week=1`;
  - `is_current=False`;
  - current monthly/weekly plan is not replaced.
- Chat response already says:
  - `אימון יחיד`;
  - `אימון חד-פעמי`;
  - `לא מחליף את התוכנית הפעילה`.
- Gap found:
  - `progression_model` still used the generic persistent-plan text `התקדמות כפולה`;
  - this is not weekly/monthly text, but it is still a multi-session progression model and should not be the main model for a one-off workout.

### Changes made

- Strengthened `backend/tests/test_workout_plans_api.py::test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan`.
- The test now requires:
  - `progression_model` includes `אימון יחיד`;
  - no `התקדמות כפולה`;
  - no `שבוע`;
  - no `חודש`.
- Updated `backend/app/services/workout_plan_builder.py::_progression_model()`.
- Single workouts now store:
  - `אימון יחיד: לבצע היום, לתעד מה הושלם, RPE או מאמץ מילולי וכאב, ולא להעלות עומס עתידי בלי לוג נוסף.`

### Tests and checks

- Failing proof before fix:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan --basetemp .pytest-tmp-loop114-single-progression-failing`
  - Result: failed because `progression_model` still contained generic `התקדמות כפולה`.
- Focused single-workout run after fix:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan backend/tests/test_workout_plans_api.py::test_single_workout_without_duration_defaults_to_short_practical_session backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current backend/tests/test_coach_engine.py::test_chat_endpoint_infers_hebrew_single_workout_gym_duration_and_uses_neutral_saved_response backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_hebrew_single_workout_with_soft_pain --basetemp .pytest-tmp-loop114-single-focused`
  - Result: `5 passed`.
- Full workout-plan API run:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop114-workout-plans-api`
  - Result: `41 passed`.
- Manual Hebrew chat probe:
  - Prompt: `תן לי אימון יחיד היום בבית 30 דקות`.
  - Result: `200`, `provider_status=local_tool`, saved `plan_type=single_workout`, `is_current=False`.
  - Response says it is one-off and does not replace the active plan.
  - Saved `progression_model` is one-off tracking guidance, not multi-session double progression.

### Ponytail Review

- Result:
  - One helper branch plus a regression assertion.
- Rationale:
  - The persistence separation already worked.
  - The product gap was a stored plan field that still sounded like a continuing plan.
  - No new plan type or storage model was needed.

### Next research target

- Loop 115 should inspect two-week plans as a distinct horizon:
  - two-week plans should not behave like abbreviated monthly plans;
  - progression and chat response should mention week 1/week 2 and end-of-block review;
  - candidate replacement behavior should keep active plan intact until confirmation.

## Loop 115 - Two-week plan candidate behavior

### Research sources

- Two-week horizon inference and progression:
  - `backend/app/services/workout_plan_builder.py`
  - `backend/app/services/workout_service.py`
- Candidate replacement chat flow:
  - `backend/app/services/coach_engine.py`
- Existing two-week tests:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- Two-week plans already have distinct planning behavior:
  - `plan_type=two_week_plan`;
  - `duration_weeks=2`;
  - two progression schedule entries;
  - tracking guidance with `שבוע 1`, `שבוע 2`, and `בסוף שבוע 2`.
- Chat response already surfaces:
  - `תוכנית לשבועיים`;
  - week 1 / week 2 progression gate;
  - end-of-block review before another block.
- Missing proof:
  - there was direct candidate replacement coverage for a new monthly plan;
  - there was not direct chat coverage for requesting a two-week plan while a persistent plan is already active.

### Changes made

- Added `backend/tests/test_coach_engine.py::test_chat_new_two_week_plan_with_current_creates_candidate_and_keeps_current`.
- The test verifies:
  - response mentions `תוכנית לשבועיים`, `שבוע 1`, and `שבוע 2`;
  - response says the candidate does not replace the active plan yet;
  - current plan remains `is_current=True`;
  - new two-week plan is `is_current=False`;
  - pending action is `activate_workout_plan`;
  - no raw internal plan labels leak into the response.
- No production code change was needed.

### Tests and checks

- New focused test:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_new_two_week_plan_with_current_creates_candidate_and_keeps_current --basetemp .pytest-tmp-loop115-two-week-candidate`
  - Result: `1 passed`.
- Two-week affected run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response backend/tests/test_coach_engine.py::test_chat_new_two_week_plan_with_current_creates_candidate_and_keeps_current backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response --basetemp .pytest-tmp-loop115-two-week-affected`
  - Result: `6 passed`.
- Manual Hebrew chat probe with active monthly plan:
  - Prompt: `תבנה לי תוכנית לשבועיים עם משקולות`.
  - Result: `200`, `provider_status=local_tool`.
  - Plans:
    - current monthly plan remains `True`;
    - two-week candidate plan is `False`.
  - Pending action: `activate_workout_plan` for the two-week candidate.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop115-coach-engine`
  - Result: `117 passed`.

### Ponytail Review

- Result:
  - Test-only coverage.
- Rationale:
  - The production behavior was already correct.
  - The missing part was regression proof that a two-week plan uses the same safe activation gate as monthly plans.

### Next research target

- Loop 116 should inspect monthly plan UX and persistence:
  - monthly plan should be current when no existing persistent plan exists;
  - with an existing plan it should become a candidate;
  - saved monthly plan should expose four-week schedule and deload/check week without chat becoming too long.

## Loop 116 - Monthly plan chat persistence and candidate proof

### Research sources

- Monthly plan construction:
  - `backend/app/services/workout_plan_builder.py`
- Chat activation and candidate flow:
  - `backend/app/services/coach_engine.py`
- Existing monthly API and chat coverage:
  - `backend/tests/test_workout_plans_api.py`
  - `backend/tests/test_coach_engine.py`

### Findings extracted

- The builder already stores monthly plans with:
  - `plan_type=monthly_plan`;
  - four progression schedule entries;
  - a week 4 check/deload rule;
  - `20-40%` volume reduction guidance when fatigue, pain, missed sessions, or performance drops appear.
- Chat UX intentionally keeps the response short:
  - it says this is a monthly plan;
  - it tells the user to review at the end of each week;
  - it does not dump detailed deload rules into the immediate response.
- Missing proof:
  - chat-created monthly plans were not directly asserting the saved deload/check-week model;
  - monthly candidates created while another plan is current were not directly asserting the saved four-week progression model.

### Changes made

- Strengthened `backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word`.
- Strengthened `backend/tests/test_coach_engine.py::test_chat_new_monthly_plan_with_current_creates_candidate_and_asks_for_replacement`.
- The new assertions verify:
  - no existing plan: saved monthly plan is `is_current=True`;
  - existing plan: active plan remains current and the new monthly plan is `is_current=False`;
  - saved monthly plan has four progression schedule entries;
  - saved `progression_model` includes `שבוע 4`, `דילואד`, and `20-40%`;
  - chat response does not expose raw `דילואד` detail and remains under 650 characters.
- No production code change was needed.

### Tests and checks

- Focused monthly run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_new_monthly_plan_with_current_creates_candidate_and_asks_for_replacement backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level --basetemp .pytest-tmp-loop116-monthly-focused`
  - Result: `3 passed`.
- Manual Hebrew monthly probe without existing plan:
  - Prompt: `תבנה לי תוכנית חודשית של 4 ימים בחדר כושר להיפרטרופיה, אני ברמה בינונית`.
  - Result: `200`, `provider_status=local_tool`.
  - Response mentions monthly plan and does not mention `דילואד`.
  - Saved plan: `monthly_plan`, `is_current=True`, `days_per_week=4`, four schedule entries, model contains week 4, deload, and `20-40%`.
- Manual Hebrew monthly candidate probe with existing plan:
  - Prompt: `תבנה לי תוכנית חודשית חדשה של 4 ימים עם משקולות להיפרטרופיה`.
  - Result: `200`, `provider_status=local_tool`.
  - Current plan remains `is_current=True`.
  - Candidate monthly plan is `is_current=False`, has four progression entries, and model contains deload.
  - Pending action: `activate_workout_plan`.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop116-coach-engine`
  - Result: `117 passed`.

### Failures / notes

- First manual probe attempt used `sqlmodel` by mistake; the repo tests use `sqlalchemy`.
- Second manual probe attempt proved the first case but Windows locked the SQLite temp DB during `TemporaryDirectory` cleanup.
- Final manual probe used stable `.pytest-tmp-loop116-manual-*` directories and passed.

### Ponytail Review

- Result:
  - Test-only coverage.
- Rationale:
  - Production behavior already matched the intended monthly plan design.
  - The missing part was regression proof at the chat persistence boundary.

### Next research target

- Loop 117 should inspect goal-specific plan content quality:
  - hypertrophy plans should bias toward sufficient weekly muscle exposure and practical rep ranges;
  - strength plans should bias toward lower reps, longer rests, and higher RPE while staying safe;
  - endurance and mobility plans should avoid looking like generic strength plans with a renamed goal.

## Loop 117 - Mobility as a first-class goal and goal-specific content quality

### Research sources

- ACSM 2026 resistance training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
- NSCA preparatory-period resistance training guidance:
  - https://www.nsca.com/education/articles/kinetic-select/preparatory-period/
- NSCA Foundations of Fitness Programming:
  - https://www.nsca.com/contentassets/693872c8a25245a7ba49fc5527a236b9/foundations-of-fitness-programming-quiz-preview.pdf
- ACSM / CDC physical activity guidance:
  - https://acsm.org/education-resources/trending-topics-resources/physical-activity-guidelines/
- NSCA rest interval guidance:
  - https://www.nsca.com/contentassets/fb8a7be6eb174934bb8844703c4de4cc/ptq-10.1.3-how-to-manipulate-rest-intervals-to-maixmize-strength-training-effectiveness.pdf

### Findings extracted

- Strength:
  - heavy/core lifts should be early in the session;
  - lower rep ranges and longer rests fit strength better than dense circuits;
  - remote coaching should avoid frequent max testing and technical failure.
- Hypertrophy:
  - volume is the main lever;
  - 6-12 or 8-15 rep ranges are practical anchors;
  - progression should consider recovery and should not chase failure in every set.
- Endurance:
  - use FITT logic and talk-test/RPE;
  - progress duration or frequency before intensity;
  - beginner/intermediate endurance should not start with too much HIIT.
- Mobility:
  - dynamic warmups and movement prep are not the same as static flexibility;
  - mobility programming should emphasize useful range, control, breathing, and balance;
  - static flexibility fits better after warmup or as a separate lower-intensity session.

### Findings in the codebase

- `WorkoutPlanBuilder` already had different variables for strength, hypertrophy, fat loss, endurance, and mobility-focused prompts.
- Weak product/data issue:
  - mobility prompts were inferred as `improve_fitness`;
  - the exercises were mobility-focused, but the saved plan goal and dashboard identity were generic fitness.
- That is a real product problem because saved plans, dashboard state, and future adaptation rules depend on structured goal identity.

### Changes made

- Added canonical `improve_mobility` to backend goal schema.
- Updated prompt inference:
  - `mobility`, `flexibility`, `מוביליטי`, `גמישות`, and `תנועתיות` now infer `improve_mobility`.
- Updated deterministic builder:
  - `improve_mobility` now uses mobility variables even when the goal is supplied explicitly without mobility words in the prompt.
  - Added Hebrew label `שיפור מוביליטי`.
- Updated knowledge center:
  - added `improve_mobility` goal playbook;
  - added mobility entry to goal-specific programming rules;
  - updated source document to define mobility as a first-class goal, not an alias of `improve_fitness`.
- Updated frontend:
  - onboarding goal selector includes `שיפור מוביליטי`;
  - dashboard renders `improve_mobility` as `שיפור מוביליטי` instead of unknown/internal code.

### Tests and checks

- Focused backend run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_goal_and_scenario_playbooks backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_goal_specific_programming_rules backend/tests/test_workout_schema.py --basetemp .pytest-tmp-loop117-mobility-focused`
  - Result: `8 passed`.
- Focused frontend run:
  - `npm --prefix frontend test -- --run DashboardPanel.test.tsx Onboarding.test.tsx`
  - Result: `2 passed`, `6 tests passed`.
- Manual Hebrew mobility chat probe:
  - Prompt: `תן לי תוכנית מוביליטי חודשית עם משקל גוף`.
  - Result: `200`, `provider_status=local_tool`.
  - Saved plan: `goal=improve_mobility`, `plan_type=monthly_plan`, `equipment_needed=['bodyweight']`.
  - First exercises include mobility and balance.
- Manual Hebrew endurance chat probe:
  - Prompt: `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`.
  - Result: `200`, `provider_status=local_tool`.
  - Saved plan: `goal=improve_endurance`, `plan_type=two_week_plan`.
  - First exercise is cardio, avoids running, and offers walking/bike-style alternatives.
- Affected backend run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py backend/tests/test_workout_schema.py --basetemp .pytest-tmp-loop117-backend-affected`
  - Result: `157 passed`.
- Chat mobility run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_previews_candidate_plan_first_action_before_replacement_confirmation --basetemp .pytest-tmp-loop117-coach-mobility`
  - Result: `2 passed`.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop117-coach-engine`
  - Result: `117 passed`.
- Full frontend run:
  - `npm --prefix frontend test -- --run`
  - Result: `9 passed`, `50 tests passed`.

### Failures / notes

- One intermediate pytest command referenced a non-existent test name.
- Rerun with the correct chat test names passed.

### Ponytail Review

- Result:
  - Small data-identity fix, not a new planning engine.
- Rationale:
  - The builder already knew how to generate mobility-style sessions.
  - The missing part was preserving user intent as structured product state across API, chat, knowledge, and UI.

### Next research target

- Loop 118 should inspect fat-loss support:
  - fat-loss plans should preserve strength and muscle while adding practical walking/cardio support;
  - they must avoid punishment language, extreme diet implications, or calorie-burn certainty;
  - chat responses should give one next action and avoid turning workout generation into nutrition counseling.

## Loop 118 - Fat-loss support without punishment framing or calorie-burn claims

### Research sources

- ACSM weight-loss physical activity position stand summary:
  - https://www.sportgeneeskunde.com/wp-content/uploads/ACSM-Position-Stand-Appropriate-physical-activity-intervention-Strategies-for-Weight-Loss-and-Prevention-of-Weight-Regain-for-Adults.pdf
- NSCA Foundations of Fitness Programming, weight-loss and nutrition scope:
  - https://www.nsca.com/contentassets/693872c8a25245a7ba49fc5527a236b9/foundations-of-fitness-programming-quiz-preview.pdf
- Academy of Nutrition and Dietetics Evidence Analysis Library, weight-management summary:
  - https://www.andeal.org/template.cfm?key=4187&template=guide_summary
- NSCA article on individual variables and overreaching risk:
  - https://www.nsca.com/education/articles/ptq/a-coach-and-trainers-challenge-individual-variables-in-health-fitness-and-nutrition/
- ACSM weight-loss mythbusting:
  - https://acsm.org/mythbusting-weight-loss/
- Exercise is Medicine weight-loss activity handout:
  - https://exerciseismedicine.org/assets/page_documents/EIM%20Rx%20series_Exercising%20to%20Lose%20Weight_2.pdf

### Findings extracted

- Fat-loss support should be framed as body-composition and habit support, not punishment.
- Exercise helps preserve function and muscle during weight loss and supports maintenance, but workout plans should not claim exact calorie burn.
- Resistance training should remain a core anchor while walking/cardio is progressed gradually.
- Trainers/coaches can provide general nutrition education, but should not prescribe specific diets or supplements as if acting as dietitians.
- When fatigue, hunger, sleep, or performance worsen, adding more intensity is often the wrong first move.

### Findings in the codebase

- `WorkoutPlanBuilder` already inferred `lose_fat` for fat-loss/cutting/Hebrew `חיטוב`.
- Fat-loss plans already used shorter rests and a note to add light cardio.
- Weak points found:
  - fat-loss progression text used negative punishment framing as a warning;
  - chat intent did not classify `תבנה לי תוכנית חיטוב ביתית לשבוע` as a workout plan because it lacked explicit `אימון`/`כושר` language and did not fit the horizon/timeboxed rules.

### Changes made

- Updated fat-loss training variables:
  - `effort`: now emphasizes consistency and preserving strength;
  - `effort_note`: now emphasizes controlled effort and movement quality;
  - `day_note`: strength remains the anchor, with optional 10-20 minutes walking/light cardio at talk-test pace;
  - `progression_rule`: progress by 5-10 minutes walking/light cardio or 500-1,000 steps before intensity;
  - `recovery_note`: keeps the extreme-diet warning while adding sleep.
- Updated chat intent classification:
  - body-composition plan language such as `חיטוב`, `להתחטב`, `ירידה בשומן`, `fat loss`, or `cutting` can route to `workout_plan`;
  - only when paired with plan creation language and no food/menu/nutrition language;
  - `תוכנית חיטוב עם תפריט` is explicitly not forced into workout-plan routing.
- Updated knowledge-source implementation notes for fat-loss workout plans.

### Tests and checks

- Initial focused run failed:
  - `test_workout_plan_adjusts_training_variables_by_goal` failed because `json` was not imported in the test file.
  - New chat fat-loss test failed because provider status was `not_configured`, showing the message routed to general chat instead of local workout-plan generation.
- Root cause:
  - `_is_workout_plan()` required workout/gym language or a recognized horizon, and did not treat Hebrew `תוכנית חיטוב` as body-composition workout-plan language.
- Focused rerun:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_common_hebrew_equipment_and_missed_workout_guidance backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_hebrew_fat_loss_plan_without_punishment_or_calorie_claims --basetemp .pytest-tmp-loop118-fat-loss-focused-rerun`
  - Result: `4 passed`.
- Manual Hebrew fat-loss chat probe:
  - Prompt: `תבנה לי תוכנית חיטוב ביתית לשבוע`.
  - Result: `200`, `provider_status=local_tool`.
  - Saved plan: `goal=lose_fat`, `plan_type=weekly_plan`.
  - Response has one next action and no calorie/punishment language.
  - Saved plan includes walking and 500-1,000 step progression, with no punishment language.
- Affected run:
  - `python -m pytest backend/tests/test_coach_intent_service.py backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop118-intent-plans`
  - Result: `68 passed`.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop118-coach-engine`
  - Result: `118 passed`.

### Ponytail Review

- Result:
  - Small intent and wording fix.
- Rationale:
  - No new fat-loss subsystem was needed.
  - The useful product change was preserving a common Hebrew request as structured workout-plan intent while keeping diet/menu language out of workout routing.

### Next research target

- Loop 119 should inspect equipment-specific plan quality:
  - home/bodyweight/dumbbells/gym plans should produce distinct practical exercises, not only different labels;
  - substitutions should preserve movement patterns and safety;
  - chat should not ask extra questions when the prompt already gives enough critical equipment context.

## Loop 119 - Equipment-specific plan quality for bands, dumbbells, bodyweight, and gym

### Research sources

- HPRC / NSCA exercise-order guidance:
  - https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training
- ACSM 2026 resistance-training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
- ACSM resistance-training basics brochure:
  - https://www.prescriptiontogetactive.com/static/pdfs/resistance-training-ACSM.pdf

### Findings extracted

- Equipment is a constraint and an adherence lever, not a proof of plan quality.
- Effective resistance training can use machines, free weights, elastic resistance, bodyweight, and home objects when the exercises preserve the intended movement pattern.
- Beginners often benefit from stable variations, but the plan should not force gym machines when the user asks for home, bands, dumbbells only, or bodyweight.
- Exercise order should keep large, multi-joint patterns early enough that fatigue does not degrade technique.
- Substitutions should preserve the pattern and resistance direction as much as possible instead of swapping by muscle name only.

### Findings in the codebase

- `WorkoutService._infer_equipment()` already detects natural Hebrew equipment phrases such as `חדר כושר`, `גומייה`, `משקולות`, and `בלי ציוד`.
- The manual shell probe initially looked broken because direct Hebrew in a PowerShell pipe was not reliable; rerunning with Unicode escapes showed the API infers the right equipment.
- `WorkoutPlanBuilder` already had separate equipment modes for gym, dumbbells, bands, and bodyweight.
- Weak point found:
  - in band mode, squat and lunge names still fell back to bodyweight-style primary names while band-specific alternatives existed.

### Changes made

- Updated band-mode exercise naming in `backend/app/services/workout_plan_builder.py`:
  - beginner squat now starts as `סקוואט לקופסה עם גומייה קלה`;
  - non-beginner band squat now starts as `סקוואט עם גומייה`;
  - band lunge now starts as a band-specific supported lunge or split squat.
- Expanded `test_workout_plan_tailors_exercises_by_equipment_and_experience`:
  - adds natural Hebrew `גומייה בלבד` prompt coverage;
  - asserts saved equipment is `resistance bands`;
  - asserts band exercises include `גומייה`;
  - asserts no machine, cable, pulley, bench, or dumbbell terms leak into a bands-only plan.

### Tests and checks

- Focused equipment/API run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_workout_plans_api.py::test_home_plan_prompt_overrides_saved_gym_equipment_when_equipment_missing backend/tests/test_workout_plans_api.py::test_single_workout_plan_infers_hebrew_gym_and_duration_from_prompt_before_profile_defaults --basetemp .pytest-tmp-loop119-equipment-focused`
  - Result: `3 passed`.
- Focused chat run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_weekly_plan_without_workout_word backend/tests/test_coach_engine.py::test_chat_endpoint_answers_equipment_and_missed_workout_guidance_locally --basetemp .pytest-tmp-loop119-chat-focused`
  - Result: `2 passed`.
- Full workout-plan API run:
  - `python -m pytest backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-loop119-workout-plans-full`
  - Result: `41 passed`.
- Manual Hebrew chat probes:
  - Prompt: `תבנה לי תוכנית שבועית עם גומייה בלבד למתחיל`.
  - Result: `200`, `provider_status=local_tool`.
  - Saved plan: `plan_type=weekly_plan`, `equipment_needed=['resistance bands']`.
  - First day exercises include `סקוואט לקופסה עם גומייה קלה`, `לחיצת חזה עם גומייה`, `חתירה עם גומייה`, and `היפ הינג' עם גומייה`.
  - Prompt: `תבנה לי תוכנית שבועית בחדר כושר להיפרטרופיה`.
  - Result: `200`, `provider_status=local_tool`.
  - Saved plan: `plan_type=weekly_plan`, `equipment_needed=['חדר כושר', 'משקולות יד', 'מכונות']`.
  - First day exercises include machine-based gym selections.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop119-coach-engine-full`
  - Result: `118 passed`.

### Failures / notes

- Initial manual probe with direct Hebrew inside a PowerShell heredoc showed all equipment as `bodyweight`.
- Root cause:
  - the shell pipe mangled the Hebrew input; the product behavior was correct when probed with Unicode escapes and through pytest files.
- A manual script also briefly failed with `ModuleNotFoundError: No module named 'sqlmodel'`.
- Root cause:
  - the project tests use `sqlalchemy.select`; rerunning the probe with the correct import passed.

### Ponytail Review

- Result:
  - Small catalog and test hardening, not a new equipment engine.
- Rationale:
  - Equipment inference and mode separation already existed.
  - The practical gap was making band-only plans visibly band-specific and guarding against unavailable-equipment leakage.

### Next research target

- Loop 120 should inspect pain, injury, and limitation handling inside workout-plan generation:
  - when to modify a plan locally vs ask one critical follow-up;
  - when to avoid plan generation and route to conservative safety guidance;
  - how limitations should affect exercise selection, substitutions, volume, RPE, and Hebrew safety wording.

## Loop 120 - Pain, injury, and limitation handling for workout plans

### Research sources

- Exercise is Medicine lower-back-pain exercise handout:
  - https://exerciseismedicine.org/assets/page_documents/EIM%20Rx%20series_Exercising%20with%20Lower%20Back%20Pain_2.pdf
- Barbell Medicine pain-in-training entry-point guidance:
  - https://www.barbellmedicine.com/blog/pain-in-training-what-do/
- Mayo Clinic stress-test stop symptoms:
  - https://www.mayoclinic.org/tests-procedures/stress-test/about/pac-20385234
- Exercise is Medicine preparticipation screening questionnaire:
  - https://www.exerciseismedicine.org/wp-content/uploads/2021/04/EIM-exercise-preparticipation-screening.pdf
- NHS back pain red flags and activity guidance:
  - https://www.nhs.uk/conditions/back-pain/
- ACSM 2026 resistance-training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/

### Findings extracted

- Red flags such as chest pain, unusual breathlessness, dizziness, fainting, irregular heartbeat, neurological symptoms, or rapidly worsening pain should stop workout generation and route to conservative safety/referral language.
- Non-specific back pain does not automatically mean bed rest; staying active can help, but exercises should stop or be modified when pain worsens.
- For pain during a lift, the practical first move is to find a tolerable entry point: lower load, shorten range of motion, reduce volume, or temporarily change the exercise.
- Progression after pain should wait for stable or improved symptoms over the next 24-48 hours.
- The bot should avoid diagnosis language. It can adapt training conservatively but should not claim to treat or fix the injury.

### Findings in the codebase

- Strong existing coverage already existed:
  - red-flag symptoms block plan creation;
  - vague pain asks for one critical clarification;
  - knee pain builds a modified plan;
  - scoped plan edits can already change knee, shoulder, and low-back-sensitive exercises.
- Weak point found:
  - `extract_pain_area()` recognized `גב תחתון` but not natural Hebrew `כאב גב`.
  - Because of that, `כואב לי הגב בדדליפט` could fall into vague-pain clarification even when the exercise context clearly points to a hinge/deadlift adaptation.
  - New plan generation also lacked a low-back-sensitive catalog adaptation, so a plan with `כאב גב` could still keep a deadlift-like hinge as primary.

### Changes made

- Updated `backend/app/services/pain_text.py`:
  - recognizes general `גב` / `כאב גב` / `back` as a pain area after the more specific `גב תחתון` and `גב עליון` checks.
- Updated `backend/app/services/workout_plan_builder.py`:
  - added low-back limitation detection;
  - adapts hip-hinge work to `היפ הינג' לקיר`;
  - uses glute bridge, dead bug, stick hinge, or light range-limited hinge as alternatives depending on equipment;
  - adds safety notes for radiation, numbness, weakness, sharp pain, or worsening after training;
  - progression now waits for a stable 24-48 hour response.
- Updated `backend/app/services/workout_service.py`:
  - scoped pain edits now treat general `גב` with deadlift/hinge language as a low-back-sensitive hinge substitution.
- Updated `backend/app/services/coaching_knowledge.py`:
  - compact provider context now includes the hinge/deadlift back-pain rule while staying inside the prompt budget.
- Updated `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`:
  - added NHS, Barbell Medicine, and Mayo Clinic sources;
  - added an implementation note for `כאב גב` around hinge/deadlift work.

### Tests and checks

- Focused pain run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan backend/tests/test_workout_plans_api.py::test_workout_plan_api_treats_general_back_pain_as_hinge_constraint backend/tests/test_workout_plans_api.py::test_workout_plan_api_requires_pain_area_for_vague_soft_pain backend/tests/test_coach_engine.py::test_chat_scoped_general_back_pain_edit_updates_hinge_without_replacement --basetemp .pytest-tmp-loop120-pain-focused`
  - Result: `4 passed`.
- Focused knowledge run:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_limitation_adaptation_summary_for_workouts_only backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_movement_limitation_adaptations --basetemp .pytest-tmp-loop120-knowledge-focused`
  - Result: `2 passed`.
- Manual Hebrew chat probes:
  - Prompt: `יש לי כאב גב קל בדדליפט, תבנה לי תוכנית שבועית כוח של 2 ימים בלי ציוד`.
  - Result: `200`, `provider_status=local_tool`, `safety_flagged=False`.
  - Saved plan: `plan_type=weekly_plan`, `limitations=רגישות בגב`, hip-hinge exercises changed to `היפ הינג' לקיר`.
  - Prompt: `יש לי כאב, תבנה לי תוכנית כוח`.
  - Result: `200`, `provider_status=local_tool`, no saved plan, asks where the pain is and whether it is sharp/worsening/limiting.
  - Prompt: `כואב לי החזה ויש לי סחרחורת בזמן אימון, תבנה לי תוכנית`.
  - Result: `200`, `provider_status=safety_override`, `safety_flagged=True`, no saved plan, safety event `dangerous_symptoms`.
- Initial relevant full run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop120-relevant-full`
  - Result: `269 passed`, `3 failed`.
- Root cause:
  - the added provider-context limitation summary pushed `len(str(workout_context))` to `8364`, above the existing `<8350` prompt-budget guard.
- Budget rerun after shortening the summary:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_one_compact_environment_cue_without_new_section backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_fueling_risk_guidance_without_prompt_bloat --basetemp .pytest-tmp-loop120-budget-rerun`
  - Result: `3 passed`.
- Relevant full rerun:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop120-relevant-full-rerun`
  - Result: `272 passed`.

### Ponytail Review

- Result:
  - Narrow pain-area and hinge-regression fix.
- Rationale:
  - The repo already had a safety layer, a pain parser, scoped plan edits, and limitation knowledge.
  - Building a new injury system would have been premature; the valuable fix was making a common Hebrew phrase hit the existing conservative path.

### Next research target

- Loop 121 should inspect missing-critical-info behavior:
  - the bot should not ask a long questionnaire;
  - it should ask only when safety or plan feasibility is blocked;
  - otherwise it should infer safely, state assumptions, and save a usable plan.

## Loop 121 - Minimal critical-info policy for short Hebrew plan requests

### Research sources

- ACSM 2026 resistance-training position stand / consistency and individualization:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/
- ODPHP / Community Guide, individually adapted health behavior change programs:
  - https://odphp.health.gov/healthypeople/tools-action/browse-evidence-based-resources/physical-activity-individually-adapted-health-behavior-change-programs
- CDC adult physical activity guidelines:
  - https://www.cdc.gov/physical-activity-basics/guidelines/adults.html
- CDC guide to strategies to increase physical activity, individually adapted programs:
  - https://www.cdc.gov/diabetes/news/media/pdfs/CDC-guide-strategies-increase-physical-activity.pdf

### Findings extracted

- For adherence, the first useful action matters more than collecting a perfect intake form.
- Individually adapted programs improve participation by using goal-setting, problem-solving, and routines that fit the person's needs and readiness.
- CDC guidance supports breaking activity into manageable chunks and getting started; missing perfect details should not block all movement.
- The product rule should be:
  - ask only when safety or feasibility is blocked;
  - otherwise infer conservatively, show short assumptions, save structured data, and let the user refine later.

### Findings in the codebase

- Existing behavior already handled `תבנה לי תוכנית אימונים` well:
  - chat routes to local workout-plan generation;
  - the response shows a brief `הנחות:` section;
  - saved `decision_inputs.assumptions` keeps the full structured assumptions.
- Weak point found:
  - `תבנה לי תוכנית` and `תן לי תכנית` routed to `general_chat`.
  - In a Hebrew-first AI Fitness Coach, this is too conservative: it withholds the core product value even though safe defaults are available.
- Guardrail needed:
  - `תן לי תוכנית תזונה` must not be captured as a workout plan.
  - explanatory questions like `מה ההבדל בין תוכנית שבועית לחודשית` must stay informational, not create a plan.

### Changes made

- Updated `backend/app/services/coach_intent_service.py`:
  - added `minimal_plan_request` routing;
  - creation language + `תוכנית/תכנית/plan` now routes to `workout_plan` if there is no nutrition/menu language and no question framing.
- Updated `backend/app/services/coaching_knowledge.py`:
  - added a `critical_info_policy` rule that short requests like `תבנה לי תוכנית` are enough to build a conservative workout plan in this product context.
- Updated `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`:
  - added implementation note: missing goal/equipment/level/days/duration become visible assumptions instead of a pre-plan questionnaire.
- Updated tests:
  - intent tests now cover `תבנה לי תוכנית`, `תן לי תכנית`, and `תן לי תוכנית תזונה`;
  - chat minimal-plan test now uses the shorter `תבנה לי תוכנית`;
  - knowledge test now asserts the new critical-info rule exists.

### Tests and checks

- Initial manual intent probe:
  - `תבנה לי תוכנית` -> `general_chat` before the fix.
  - `תן לי תכנית` -> `general_chat` before the fix.
  - `תן לי תוכנית תזונה` -> `general_chat`.
  - `מה ההבדל בין תוכנית שבועית לחודשית` -> `general_chat`.
- Focused intent/chat run:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_natural_hebrew_want_plan_requests backend/tests/test_coach_intent_service.py::test_intent_service_detects_hebrew_training_week_creation_as_workout_plan backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request --basetemp .pytest-tmp-loop121-minimal-focused`
  - Result: `3 passed`.
- Post-fix manual intent probe:
  - `תבנה לי תוכנית` -> `workout_plan`.
  - `תן לי תכנית` -> `workout_plan`.
  - `תן לי תוכנית תזונה` -> `general_chat`.
  - `מה ההבדל בין תוכנית שבועית לחודשית` -> `general_chat`.
- Manual Hebrew chat probe:
  - Prompt: `תבנה לי תוכנית`.
  - Result: `200`, `provider_status=local_tool`, `safety_flagged=False`.
  - Saved plan: `plan_type=monthly_plan`, `days_per_week=3`, `session_length_minutes=45`, `equipment_needed=['bodyweight']`.
  - Response includes only three visible assumptions while saved `decision_inputs.assumptions` keeps six assumptions.
- Intermediate pytest issue:
  - One command referenced a non-existent test name: `test_coaching_knowledge_contains_plan_horizon_and_critical_info_policy`.
  - Corrected to `test_coaching_knowledge_contains_plan_horizon_protocols`.
- Focused final run:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_natural_hebrew_want_plan_requests backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom --basetemp .pytest-tmp-loop121-focused-final`
  - Result: `4 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_coach_intent_service.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop121-relevant-full`
  - Result: `257 passed`.

### Ponytail Review

- Result:
  - One routing condition and tests.
- Rationale:
  - The plan builder and assumption system already existed.
  - The missing behavior was intent routing for the shortest natural Hebrew request, not a new onboarding or questionnaire feature.

### Next research target

- Loop 122 should inspect single-workout vs persistent-plan behavior:
  - a one-off workout should not overwrite the active weekly/two-week/monthly plan;
  - the response should make the difference clear in natural Hebrew;
  - tracking guidance should still tell the user what to log.

## Loop 122 - Single workout separation from active workout plans

### Research sources

- ACSM physical activity guidelines summary:
  - https://acsm.org/education-resources/trending-topics-resources/physical-activity-guidelines/
- CDC adult physical activity guidelines:
  - https://www.cdc.gov/physical-activity-basics/guidelines/adults.html
- NSCA/resistance-training frequency evidence summary:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8363540/
- ACSM 2026 resistance-training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/

### Findings extracted

- A single workout can be a useful adherence action, especially when time is limited.
- CDC guidance supports spreading activity across the week and breaking it into smaller chunks.
- A one-off session should not be treated as a full progression block.
- Resistance training still needs repeated exposure and recovery; a single good or bad workout should not rewrite the active plan.
- Product rule:
  - save the one-off workout for tracking;
  - do not make it the active weekly/two-week/monthly plan;
  - do not create replacement confirmation;
  - tell the user what to do and what to log.

### Findings in the codebase

- `WorkoutService.generate_plan()` already separates `single_workout` from persistent plan types.
- Existing behavior already:
  - keeps current persistent plans active;
  - saves `single_workout` as `is_current=False`;
  - rejects activation of single workouts;
  - omits raw labels such as `single_workout` from chat responses;
  - says in Hebrew that a one-off workout does not replace the active plan.
- Weak point found:
  - the strongest “existing active plan + one-off request” chat test used English input.
  - The product is Hebrew-first, so the regression guard should use natural Hebrew.

### Changes made

- Updated `test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current` in `backend/tests/test_coach_engine.py`:
  - request is now `תן לי אימון אחד להיום, 20 דקות, בבית`;
  - asserts response includes `אימון חד-פעמי` and `לא מחליף את התוכנית הפעילה`;
  - asserts the one-off plan has `plan_type=single_workout`, `session_length_minutes=20`, `equipment_needed=['bodyweight']`;
  - asserts the existing current plan remains current;
  - asserts no `PendingAction` was created.
- No production logic change was needed in this loop.

### Tests and checks

- Manual Hebrew chat probe:
  - First created a weekly current plan: `תבנה לי תוכנית שבועית של 3 ימים עם משקולות`.
  - Then requested: `תן לי אימון אחד להיום, 20 דקות, בבית`.
  - Result: `200`, `provider_status=local_tool`.
  - Response says it is an `אימון חד-פעמי` and does not replace the active plan.
  - DB state: weekly plan remains `is_current=True`; single workout saved as `is_current=False`; no pending replacement action.
- Focused run:
  - `python -m pytest backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current backend/tests/test_coach_engine.py::test_chat_endpoint_infers_hebrew_single_workout_gym_duration_and_uses_neutral_saved_response backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_hebrew_single_workout_with_soft_pain backend/tests/test_workout_plans_api.py::test_single_workout_plan_infers_hebrew_gym_and_duration_from_prompt_before_profile_defaults backend/tests/test_workout_plans_api.py::test_single_workout_without_duration_defaults_to_short_practical_session --basetemp .pytest-tmp-loop122-single-focused`
  - Result: `5 passed`.
- Full chat run:
  - `python -m pytest backend/tests/test_coach_engine.py --basetemp .pytest-tmp-loop122-coach-engine-full`
  - Result: `118 passed`.

### Ponytail Review

- Result:
  - Test hardening only.
- Rationale:
  - Production behavior already matched the desired product rule.
  - Changing implementation would have added churn without increasing product correctness.

### Next research target

- Loop 123 should inspect progression and tracking after workout logs:
  - plan progression should depend on logged completion, RPE/effort, pain, and missed sessions;
  - missing RPE should ask one small follow-up or use effort wording, not block logging;
  - dashboard/next action should not recommend progression after pain or poor recovery.

## Loop 123 - Progression gates after workout logs

### Research sources

- ACSM 2026 resistance-training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
- ACSM Resistance Training brochure:
  - https://www.prescriptiontogetactive.com/static/pdfs/resistance-training-ACSM.pdf
- Barbell Medicine lifting rehab mistakes:
  - https://www.barbellmedicine.com/blog/lifting-rehab-mistakes/
- ACSM progression models position stand summary:
  - https://www.sportgeneeskunde.com/wp-content/uploads/ACSM-Position-Stand-Progression-Models-in-Resistance-Training-for-Healthy-Adults.pdf
- Helms et al. RIR-based RPE application in resistance training:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC4961270/

### Findings extracted

- Progression is a gate, not a reward for a single completed workout.
- A small load or rep increase is reasonable only when the current work is performed cleanly, without pain, and with manageable effort.
- ACSM progression language supports changing one variable at a time and using conservative load increases only after the current workload is comfortably performed.
- Pain, increasing symptoms, or worsening 24-48h response should hold or reduce load rather than progress.
- RPE/RIR and qualitative effort are useful, but they are not the same data:
  - `קל מדי` can justify a small correction because it directly indicates underload;
  - `כבד מדי` or near-failure language should reduce/hold;
  - `בשליטה` without RPE/RIR is useful tracking language but should maintain the current version and ask for effort/pain tracking before raising load.

### Findings in the codebase

- `TrainingAdaptationService` already handled pain, high RPE/RIR, missed sessions, repeated adherence risk, and substitution progression gates.
- The narrow gap was normal exercise logs with natural Hebrew controlled effort:
  - `היה מאתגר אבל בשליטה, בלי כאב`
  - previous behavior treated this as `progress_candidate`;
  - that could recommend a small progression without numeric RPE/RIR or repeated clean evidence.
- Dashboard and next-workout execution both consumed the same adaptation payload, so the safest fix was in the service layer rather than only in response text.

### Changes made

- `backend/app/services/training_adaptation_service.py`
  - `controlled` qualitative effort without RPE/RIR now returns:
    - `load_signal=maintain`;
    - `reason=qualitative_controlled_effort`;
    - next action to keep the current version and log `RPE 1-10` or `RIR` plus pain before raising load.
  - `_result_supports_progression()` no longer treats `controlled` alone as progression evidence.
  - `underloaded` qualitative effort still supports a small correction because it directly reports the load was too easy.
- `backend/app/services/coach_engine.py`
  - Chat response for controlled effort now says to repeat the same structure and log `RPE 1-10` or `RIR` and pain before increasing load.
- `backend/app/services/coaching_knowledge.py`
  - Compact provider guidance now says Hebrew qualitative effort is not a number, and `בשליטה` alone means maintain.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added the workout-log progression gate rule to the knowledge source.
- Tests updated/added:
  - training adaptation service controlled-effort test;
  - next-workout API controlled-effort test;
  - chat controlled-effort response test;
  - dashboard controlled-effort next-action test.

### Tests and checks

- Focused controlled-effort run:
  - `python -m pytest backend/tests/test_training_adaptation_service.py::test_training_adaptation_uses_qualitative_controlled_effort_without_fake_metrics backend/tests/test_workout_logs_api.py::test_next_workout_uses_controlled_verbal_effort_without_fake_metrics backend/tests/test_coach_engine.py::test_chat_endpoint_natural_hebrew_controlled_log_keeps_verbal_effort backend/tests/test_dashboard_api.py::test_dashboard_holds_progression_after_controlled_verbal_effort_without_rpe --basetemp .pytest-tmp-loop123-controlled-focused`
  - Result: `4 passed`.
- First relevant full run:
  - `python -m pytest backend/tests/test_training_adaptation_service.py backend/tests/test_workout_logs_api.py backend/tests/test_dashboard_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop123-relevant-full`
  - Result: `295 passed, 1 failed`.
  - Failure: provider context test expected the phrase `מאמץ מילולי` plus `לא מספר`; fixed by restoring that wording.
- Budget rerun:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom --basetemp .pytest-tmp-loop123-knowledge-budget-rerun`
  - Result: `1 passed`.
- Second relevant full run:
  - Result: `295 passed, 1 failed`.
  - Failure: Hebrew language context test expected `עברית ישראלית טבעית`; fixed by preserving that phrase and shortening the same rule elsewhere to keep prompt budget.
- Final knowledge rerun:
  - `python -m pytest backend/tests/test_coaching_knowledge.py::test_workout_provider_context_keeps_prompt_budget_headroom backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_hebrew_language_guidance --basetemp .pytest-tmp-loop123-knowledge-two`
  - Result: `2 passed`.
- Final relevant full run:
  - `python -m pytest backend/tests/test_training_adaptation_service.py backend/tests/test_workout_logs_api.py backend/tests/test_dashboard_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop123-relevant-full-final`
  - Result: `296 passed`.

### Manual Hebrew probes

- `עשיתי {exercise} 3x10. היה מאתגר אבל בשליטה, בלי כאב.`
  - `rpe=null`, `effort_signal=controlled`, `pain_flag=false`.
  - Dashboard: `load_signal=maintain`, `reason=qualitative_controlled_effort`.
  - Next action: keep current version and log `RPE 1-10` or `RIR` and pain before raising load.
- `עשיתי {exercise} 3x10. היה קל מדי ונשאר לי מלא כוח, בלי כאב.`
  - `effort_signal=underloaded`.
  - Dashboard: `load_signal=progress_candidate`, `reason=qualitative_underload`.
  - Next action: small load increase or slower tempo, no big jump.
- `עשיתי {exercise} 3x10. היה כאב בברך בזמן האימון.`
  - `pain_flag=true`.
  - Dashboard: `load_signal=pain_caution`, `reason=pain_reported`.
  - Next action: easier variation, comfortable range, lower load before any progression.

### Ponytail Review

- Result:
  - Small service-layer correction, not a new progression subsystem.
- Rationale:
  - Existing adaptation architecture was mostly correct.
  - The bug was a specific overinterpretation of natural Hebrew effort language.
  - Fixing the central adaptation service kept chat, next workout, and dashboard aligned.

### Next research target

- Loop 124 should inspect monthly and two-week progression blocks:
  - whether week-to-week rules, deload/reassessment language, and plan horizon separation are consistent;
  - whether monthly plans avoid pretending every week must increase load;
  - whether two-week plans are framed as a short block or trial block rather than a full mesocycle.

## Loop 124 - Two-week and monthly progression blocks

### Research sources

- ACSM 2026 resistance-training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
- ACSM progression models in resistance training:
  - https://tourniquets.org/wp-content/uploads/PDFs/ACSM-Progression-models-in-resistance-training-for-healthy-adults-2009.pdf
- NSCA preparatory period excerpt:
  - https://www.nsca.com/education/articles/kinetic-select/preparatory-period/
- Practical approach to deloading:
  - https://doras.dcu.ie/31501/1/a_practical_approach_to_deloading__recommendations.203%282%29.pdf
- Frontiers deloading practices:
  - https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.1073223/full

### Findings extracted

- ACSM 2026 emphasizes consistency, individualization, safety, and simple programs before complex periodization for most healthy adults.
- ACSM progression guidance supports small progression only after the current workload is completed above target across repeated sessions.
- NSCA periodization material frames phases as changes in intensity/volume across time, with recovery weeks/microcycles used to manage fatigue.
- Deloading is reduced training stress to manage fatigue and improve readiness; it can be preplanned or reactive and usually changes volume, effort, duration, frequency, or exercise selection.
- Product rules:
  - a two-week plan is a short trial block, not a full mesocycle;
  - week 2 may progress only when week 1 has stable completion, pain, and RPE/RIR logs;
  - a monthly plan should not imply every week must increase load;
  - week 4 is check/maintenance or conditional deload, not an automatic punishment week;
  - qualitative Hebrew effort like `בשליטה` remains tracking language, but alone means maintain and collect RPE/RIR before raising load.

### Findings in the codebase

- The workout builder already separated:
  - `single_workout`;
  - `weekly_plan`;
  - `two_week_plan`;
  - `monthly_plan`.
- Existing tests already covered horizon inference, saved plan types, plan duration, and some monthly/two-week progression schedules.
- Narrow gap found:
  - several progression schedule lines still allowed `RPE או מאמץ מילולי` as a progression gate.
  - That conflicted with Loop 123, where `בשליטה` without RPE/RIR became `maintain` rather than `progress_candidate`.

### Changes made

- `backend/app/services/workout_plan_builder.py`
  - Two-week beginner:
    - week 1 now asks for `RPE 5-7` or `RIR 2-4`.
    - week 2 progresses only with no pain and `RPE 7 ומטה` or `RIR 2-4`.
    - if there is only qualitative effort, it says to keep the current version and not add sets.
  - Two-week intermediate/advanced:
    - week 2 progression now requires stable `RPE/RIR`, pain and completion/performance logs.
    - qualitative effort alone means hold or reduce rather than progress.
  - Monthly beginner:
    - week 2 adds a rep only with no pain and stable numeric effort; qualitative effort alone means hold and log a number.
    - week 2 explicitly says not to add sets yet.
  - Monthly intermediate/advanced:
    - week 2/3 progression now requires stable `RPE/RIR`, sleep, pain and performance signals.
  - Tracking guidance:
    - two-week/monthly plans explicitly say qualitative effort alone means maintain.
- `backend/app/services/coaching_knowledge.py`
  - `plan_horizon_protocols` now encode:
    - two-week short block progression requires `RPE/RIR`;
    - monthly week 4 is conditional check/maintenance/deload;
    - verbal effort alone is not a progression gate.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added horizon progression rule matching the service behavior.
- `backend/tests/test_workout_plans_api.py`
  - Strengthened horizon tests to assert `RPE/RIR` gates and qualitative-effort hold language.
- `backend/tests/test_coaching_knowledge.py`
  - Strengthened plan horizon protocol tests to assert the same rules in the knowledge center.

### Tests and checks

- First focused horizon run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_two_week_horizon_in_response backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word --basetemp .pytest-tmp-loop124-horizon-focused`
  - Result: `3 passed, 2 failed`.
  - Failures were useful text expectations:
    - two-week beginner path needed explicit `אם לא`;
    - monthly beginner path needed explicit `לא להוסיף סטים`.
  - Fixed by preserving both phrases while keeping the RPE/RIR gate.
- Focused reruns:
  - `.pytest-tmp-loop124-horizon-focused-second-rerun`
  - Result: `5 passed`.
- Strengthened-test rerun:
  - `.pytest-tmp-loop124-horizon-focused-tests-updated-rerun`
  - Result: `5 passed`.
- Focused knowledge + horizon run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons backend/tests/test_workout_plans_api.py::test_monthly_progression_schedule_respects_experience_level backend/tests/test_workout_plans_api.py::test_two_week_progression_schedule_respects_experience_level backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_full_coach_summaries_for_workout_plan --basetemp .pytest-tmp-loop124-knowledge-horizon-focused`
  - Result: `5 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_training_adaptation_service.py backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop124-relevant-full`
  - Result: `304 passed`.

### Manual Hebrew probes

- `תבנה לי תוכנית לשבועיים למתחיל בלי ציוד`
  - `plan_type=two_week_plan`, `duration_weeks=2`.
  - Week 1: learn movement with `RPE 5-7` or `RIR 2-4`.
  - Week 2: add one clean rep only with no pain and numeric effort; qualitative effort alone means keep and do not add sets.
- `תבנה לי תוכנית חודשית למתחיל בלי ציוד`
  - `plan_type=monthly_plan`, `duration_weeks=4`.
  - Week 2: add a clean rep only with no pain and stable `RPE/RIR`; qualitative effort alone means keep and log a number.
  - Week 4: check/maintain; reduce 20-30% volume if pain, misses or unusual RPE.
- `תבנה לי תוכנית חודשית למתקדם במכון`
  - Week 2/3 progression requires stable `RPE/RIR`, performance, sleep and pain.
  - Week 4: check/maintenance with possible 20-40% volume reduction before another block.

### Ponytail Review

- Result:
  - Narrow text/rule alignment change.
- Rationale:
  - The plan horizon system already existed and had meaningful tests.
  - The needed fix was consistency with the new progression gate rule, not a rewrite of plan generation.

### Next research target

- Loop 125 should inspect goal-specific plan outputs for endurance and mobility:
  - whether endurance and mobility plans use goal-appropriate progression instead of strength/hypertrophy assumptions;
  - whether the single/weekly/two-week/monthly separation still holds for non-strength goals;
  - whether Hebrew responses avoid overpromising fat loss, cardio gains, mobility fixes, or pain treatment.

## Loop 125 - Goal-specific endurance, mobility, and fat-loss support

### Research sources

- CDC measuring physical activity intensity and talk test:
  - https://www.cdc.gov/physical-activity-basics/measuring/index.html
- ACSM physical activity guideline summary:
  - https://acsm.org/education-resources/trending-topics-resources/physical-activity-guidelines/
- ACSM stretching and flexibility guidance:
  - https://acsm.org/stretching-and-flexibility-guidelines-update/
- CDC adult physical activity guidelines:
  - https://www.cdc.gov/physical-activity-basics/guidelines/adults.html
- ACSM effective resistance training program infographic:
  - https://acsm.org/effective-resistance-training-program-infographic/

### Findings extracted

- Endurance/cardiorespiratory plans should progress mainly by duration, frequency, or easy volume before intensity.
- Talk test and RPE are appropriate practical intensity tools for general users.
- Mobility/flexibility work should use comfortable range, control, breathing, balance and no sharp pain; it should not be measured primarily by load or RIR.
- Fat-loss support plans should keep strength as an anchor and add accessible steps or light cardio gradually.
- Fat-loss plans must not promise exact calorie burn, use exercise as punishment, or push extreme dieting.
- Experience level should change dose, complexity and progression tolerance, but should not overwrite the goal's intensity language:
  - endurance uses talk test/RPE and duration/frequency;
  - mobility uses range/control/breathing/RPE;
  - fat-loss support uses strength consistency plus steps/cardio, not calorie-burn certainty.

### Findings in the codebase

- The builder already had goal-specific exercise choices:
  - endurance first exercise: `אירובי בסיסי בקצב שיחה`;
  - mobility first exercise: `זרימת מוביליטי ירך-גב-כתף`;
  - fat loss support: strength anchor plus walking/cardio and step progression.
- Narrow gaps found:
  - `_experience_training_variables()` overwrote endurance/mobility effort language with strength-style `חזרות ברזרבה`.
  - `_tracking_guidance()` used a generic strength metric line: `חזרות, משקל, RIR`.
  - spacing guidance for mobility/endurance could mention `full-body`, which is not the right user-facing framing for these goals.

### Changes made

- `backend/app/services/workout_plan_builder.py`
  - Added `goal_focus="fat_loss"` for fat-loss support variables.
  - Updated `_experience_training_variables()`:
    - beginner/advanced still change sets and complexity;
    - endurance keeps talk test/RPE and duration/frequency framing;
    - mobility keeps range/control/breathing/no sharp pain framing;
    - fat-loss keeps strength/consistency/no-punishment framing.
  - Updated `_tracking_guidance()`:
    - endurance tracking now asks for duration, distance/pace if available, talk test/RPE, pain, breathing and completion;
    - mobility tracking now asks for central movement, comfortable range, control, breathing, pain and completion;
    - generic `חזרות/משקל/RIR` no longer appears in endurance or mobility tracking.
  - Updated `_weekly_spacing_guidance()`:
    - endurance spacing talks about aerobic days, easy days/rest and conversational pace;
    - mobility spacing talks about mobility/balance days, range/control and no sharp pain;
    - no `full-body` wording leaks into endurance or mobility tracking.
- `backend/app/services/coaching_knowledge.py`
  - Added knowledge rule: experience level changes dose/complexity, not the intensity metric for endurance or mobility.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added goal-specific intensity rule.
- `backend/tests/test_workout_plans_api.py`
  - Strengthened tests to assert:
    - endurance tracking includes `talk test`;
    - mobility tracking includes `RPE 4-6` and `טווח נוח`;
    - endurance/mobility tracking does not include `RIR`, `ברזרבה`, `משקל אם יש`, or `full-body`.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertion for the goal-specific intensity rule.

### Tests and checks

- Focused goal run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_hebrew_fat_loss_plan_without_punishment_or_calorie_claims backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response --basetemp .pytest-tmp-loop125-goal-focused-rerun`
  - Result: `5 passed`.
- Focused knowledge + goal run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_plan_adjusts_training_variables_by_goal backend/tests/test_workout_plans_api.py::test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus backend/tests/test_coach_engine.py::test_chat_endpoint_dispatches_hebrew_fat_loss_plan_without_punishment_or_calorie_claims backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response backend/tests/test_coach_engine.py::test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_goal_specific_programming_rules --basetemp .pytest-tmp-loop125-goal-knowledge-focused-rerun`
  - Result: `6 passed`.
- First relevant full run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_training_adaptation_service.py backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop125-relevant-full`
  - Result: `304 passed`.
- Manual probe exposed remaining issue:
  - endurance/mobility tracking no longer had goal-specific effort overwritten, but still included generic strength tracking language and full-body spacing.
- After tracking/spacing fixes:
  - focused run `.pytest-tmp-loop125-spacing-focused-rerun`: `4 passed`.
  - final relevant full run `.pytest-tmp-loop125-relevant-full-third-final`: `304 passed`.

### Manual Hebrew probes

- `תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה`
  - Tracking now asks for duration, distance/pace if available, `talk test` or RPE, pain, breathing and completion.
  - No `RIR`, no `ברזרבה`, no `משקל אם יש`, no `full-body`.
  - Spacing says to spread aerobic days and keep most work conversational.
- `תן לי תוכנית מוביליטי חודשית עם משקל גוף`
  - Tracking now asks for central movement, comfortable range, control, breathing, pain and completion.
  - No `RIR`, no `ברזרבה`, no `משקל אם יש`, no `full-body`.
  - Spacing says to spread mobility/balance days so range/control improve without sharp pain or accumulated fatigue.
- `תבנה לי תוכנית חיטוב ביתית לשבוע`
  - Keeps strength as anchor.
  - Progression is walking/light cardio or 500-1,000 steps gradually before intensity.
  - No calorie-burn certainty and no punishment framing.

### Ponytail Review

- Result:
  - Small goal-specific override fix.
- Rationale:
  - The builder already had useful goal-specific exercise selection.
  - The real bug was a shared helper leaking strength metrics into non-strength goals.
  - Fixing the helper and tracking guidance preserved existing architecture.

### Next research target

- Loop 126 should inspect beginner/intermediate/advanced split selection and weekly recovery:
  - whether 4-day beginner plans are still too dense;
  - whether advanced bodyweight/gym plans get enough specificity without overcomplication;
  - whether Hebrew responses surface spacing/recovery assumptions clearly without long explanations.

## Loop 126 - Split selection and beginner recovery density

### Research sources

- NSCA resistance-training frequency:
  - https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/
- ACSM progression models position stand:
  - https://pubmed.ncbi.nlm.nih.gov/19204579/
- ACSM progression models PDF:
  - https://tourniquets.org/wp-content/uploads/PDFs/ACSM-Progression-models-in-resistance-training-for-healthy-adults-2009.pdf
- ACSM resistance training brochure:
  - https://www.prescriptiontogetactive.com/static/pdfs/resistance-training-ACSM.pdf
- HPRC/NSCA exercise order guidance:
  - https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training

### Findings extracted

- NSCA guidance supports 2-3 nonconsecutive full-body days for beginners.
- ACSM progression models support:
  - novice: 2-3 days/week;
  - intermediate: 3-4 days/week, with 4 days often as split routines;
  - advanced: higher frequency only when recovery and training history support it.
- Beginners may benefit from repeated practice of basic movement patterns, but dense consecutive full-body training should reduce volume rather than just warn in prose.
- Recovery spacing is a real program variable:
  - same muscle/demand repeated on consecutive days needs lower stress or a different focus;
  - missed sessions should not be repaid by stacking harder days.

### Findings in the codebase

- Split selection already matched most rules:
  - up to 3 days -> full-body;
  - 4-day intermediate -> upper/lower;
  - advanced higher-frequency -> push/pull/legs.
- Existing beginner 4-day full-body Hebrew spacing test already expected:
  - explicit spacing guidance;
  - RPE 5-7;
  - minimum version language.
- Narrow gap found:
  - the saved plan only said to reduce sets on dense days;
  - it did not actually reduce sets in days 3-4.

### Changes made

- `backend/app/services/workout_plan_builder.py`
  - Added spacing reduction for beginner 4-day full-body plans when the prompt indicates dense/consecutive days.
  - Days 3-4 now reduce each exercise by one set in the saved structured plan.
  - Added day notes and exercise notes explaining the dense-day reduction.
  - Added `_reduce_exercise_for_spacing()` and `_reduce_set_text_once()` helpers for safe set-text reduction.
- `backend/app/services/coaching_knowledge.py`
  - Added weekly-structure rule that dense 4-day beginner full-body plans should reduce volume in days 3-4 in the saved plan, not only mention recovery.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added split and recovery rule.
- `backend/tests/test_workout_plans_api.py`
  - Strengthened the 4-day beginner consecutive Hebrew test to assert:
    - day 1 still has 2 sets;
    - days 3-4 have 1 set;
    - day and exercise notes include dense-day wording.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertion for the 4-day beginner dense-plan rule.

### Tests and checks

- Focused split run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_four_day_beginner_full_body_includes_recovery_spacing_for_consecutive_hebrew_request backend/tests/test_workout_plans_api.py::test_full_body_plan_rotates_day_emphasis_without_losing_balance backend/tests/test_workout_plans_api.py::test_workout_plan_api_builds_source_backed_four_week_upper_lower_plan backend/tests/test_workout_plans_api.py::test_workout_plan_tailors_exercises_by_equipment_and_experience backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_spacing_for_four_day_beginner_hebrew_plan --basetemp .pytest-tmp-loop126-split-focused`
  - Result: `5 passed`.
- Focused split + knowledge run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_four_day_beginner_full_body_includes_recovery_spacing_for_consecutive_hebrew_request backend/tests/test_workout_plans_api.py::test_full_body_plan_rotates_day_emphasis_without_losing_balance backend/tests/test_workout_plans_api.py::test_workout_plan_api_builds_source_backed_four_week_upper_lower_plan backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_weekly_structure_protocols backend/tests/test_coach_engine.py::test_chat_endpoint_mentions_spacing_for_four_day_beginner_hebrew_plan --basetemp .pytest-tmp-loop126-split-knowledge-focused`
  - Result: `5 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py backend/tests/test_training_adaptation_service.py backend/tests/test_dashboard_api.py --basetemp .pytest-tmp-loop126-relevant-full`
  - Result: `304 passed`.

### Manual Hebrew probe

- `תבנה לי תוכנית חודשית למתחיל בלי ציוד, 4 ימים בשבוע, ראשון עד רביעי ברצף`
  - `training_split=full_body`.
  - Spacing guidance says 4 full-body days for a beginner should be spaced, and if dense, reduce days 3-4.
  - Saved plan first-exercise set counts: `["2", "2", "1", "1"]`.
  - Days 3-4 notes include `ימים צפופים`.
  - Day 3 exercise notes include `להפחית סט אחד ולשמור RPE 5-7`.

### Ponytail Review

- Result:
  - A narrow data correction instead of a split rewrite.
- Rationale:
  - Split selection was mostly sound.
  - The bug was inconsistency between spacing prose and persisted plan data.

### Next research target

- Loop 127 should inspect saved-plan mutation and replacement flows:
  - whether scoped edits, new candidate plans, one-off sessions and active plans remain clearly separated;
  - whether Hebrew responses explain replacement/one-off behavior without raw internal labels;
  - whether tests cover enough real user phrasing around “תחליף”, “תעדכן”, “תוכנית חדשה”, and “אימון להיום”.

## Loop 127 - Saved-plan replacement, scoped edits, and one-off state safety

### Research sources

- ACSM 2026 resistance training guideline update:
  - https://acsm.org/resistance-training-guidelines-update-2026/
- ACSM CPT behavior-change competencies crosswalk:
  - https://acsm.org/wp-content/uploads/2025/01/acsm-cpt-crosswalk.pdf
- ACSM CEP exercise-prescription modification competencies:
  - https://acsm.org/wp-content/uploads/2025/01/acsm-cep-crosswalk.pdf
- Baretta et al. implementation of goal-setting components in physical activity apps:
  - https://journals.sagepub.com/doi/10.1177/2055207619862706
- Sniehotta et al. action and coping planning for physical activity:
  - https://d-nb.info/1104173190/34
- Kansas State University Physical Activity Intervention Research Laboratory relapse-prevention handout:
  - https://www.hhs.k-state.edu/health-sciences/research/labs/pair/relapse-prevention.pdf

### Findings extracted

- ACSM’s current resistance-training framing emphasizes consistency and individualization over chasing perfect complex plans.
- ACSM CPT/CEP competencies support adapting exercise prescriptions based on compliance, signs/symptoms, progress tracking, behavioral readiness and adherence strategies.
- Goal-setting research supports action planning, evaluation and re-evaluation; fixed goals without re-evaluation are weaker for behavior change.
- Coping planning is especially relevant for maintaining behavior after barriers or missed sessions.
- Product rule extracted:
  - plan-state transitions must be explicit and recoverable;
  - a new long-horizon plan should be a candidate, not an automatic overwrite;
  - scoped edits should mutate only the relevant active-plan part;
  - one-off workouts should never implicitly confirm, decline, or replace an active-plan candidate.

### Findings in the codebase

- Good existing foundation:
  - `WorkoutService.generate_plan()` already keeps persistent candidates non-current when a current plan exists.
  - `PendingActionService` already confirms/declines candidate activation and deletes declined candidates.
  - `single_workout` plans already persist as non-current one-off objects.
  - `apply_scoped_plan_edit()` already edits active-plan rows for equipment, pain, pushup regression and volume changes.
- Narrow routing gaps found:
  - Hebrew full-replacement phrases such as `תחליף לי את כל התוכנית לתוכנית חודשית חדשה במכון` classified as `workout_plan_edit`, which led to scoped-edit clarification instead of a replacement candidate.
  - Structural rewrite phrasing such as `תעדכן לי את התוכנית לתוכנית של 4 ימים בשבוע` also classified as scoped edit.
  - Natural Hebrew one-off phrasing without a command verb, such as `אימון להיום 20 דקות בלי ציוד`, classified as general chat instead of `single_workout`.

### Changes made

- `backend/app/services/coach_intent_service.py`
  - Added `_has_workout_plan_question_framing()` helper.
  - Added `_is_full_workout_plan_replacement()` before scoped-edit classification.
  - Full-plan replacement now routes to `workout_plan` when the user says things like:
    - `תחליף לי את כל התוכנית`;
    - `תוכנית חדשה במקום הקיימת`;
    - `תעדכן לי את התוכנית לתוכנית של 4 ימים בשבוע`.
  - Preserved scoped edit for phrases like:
    - `אין לי ספסל בתוכנית, תחליף רק את מה שצריך`;
    - `תחליף לי את הדדליפט בתוכנית`.
  - Added bare single-session detection for natural Hebrew requests like `אימון להיום 20 דקות בלי ציוד` and `אימון עכשיו בבית`.
  - Guarded against past-session phrasing like `אימון היום היה קשה` becoming a new workout-plan request.
- `backend/app/services/coaching_knowledge.py`
  - Added compact `plan_state_summary` to provider context.
  - Kept provider context under the existing prompt-budget ceiling by shortening horizon/state summaries and reducing base provider rules from 4 to 3.
  - Strengthened `single_workout` rules:
    - natural `אימון להיום` phrasing is a single workout;
    - one-off workouts do not resolve pending replacement actions.
  - Strengthened `plan_replacement_policy`:
    - full replacement phrases create a non-current candidate and require confirmation, not scoped edit.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added Baretta and Sniehotta behavior-change sources.
  - Added plan-state implementation rule for full replacement, scoped edit, and one-off workout behavior.
- `backend/tests/test_coach_intent_service.py`
  - Added full-plan replacement intent tests.
  - Added bare Hebrew today-workout intent tests.
- `backend/tests/test_coach_engine.py`
  - Added chat test proving Hebrew full replacement creates a candidate, keeps current active, asks for `כן להחליף`, and does not ask scoped-edit clarification.
  - Added chat test proving `אימון להיום 20 דקות בלי ציוד` saves a one-off and does not replace the active plan.
- `backend/tests/test_coaching_knowledge.py`
  - Added provider `plan_state_summary` assertions.
  - Added knowledge assertions for full replacement and one-off state boundaries.

### Tests and checks

- Focused loop run:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_routes_full_plan_replacement_to_plan_builder backend/tests/test_coach_intent_service.py::test_intent_service_detects_bare_hebrew_today_workout_request backend/tests/test_coach_engine.py::test_chat_hebrew_full_plan_replacement_creates_candidate_not_scoped_edit backend/tests/test_coach_engine.py::test_chat_bare_hebrew_today_workout_stays_one_off_with_active_plan backend/tests/test_coaching_knowledge.py::test_provider_context_includes_compact_full_coach_summaries_for_workout_plan backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols --basetemp .pytest-tmp-loop127-focused`
  - Result: `6 passed`.
- First relevant full run:
  - `python -m pytest backend/tests/test_coach_intent_service.py backend/tests/test_coach_engine.py backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop127-relevant-full`
  - Result: `333 passed, 4 failed`.
  - Failures:
    - one transient Windows `WinError 10055` socket-buffer failure inside `TestClient`;
    - three real provider-context budget failures because `workout_plan` context grew to `8476` chars over the `8350` ceiling.
- Fix after failures:
  - shortened `plan_horizon_summary`;
  - shortened `plan_state_summary`;
  - reduced provider base `rules` slice from 4 to 3.
  - verified `workout_plan` provider context length is `8307`.
- Focused reruns:
  - Knowledge/budget rerun: `5 passed`.
  - Socket-failed test rerun: `1 passed`.
- Final relevant full run:
  - `python -m pytest backend/tests/test_coach_intent_service.py backend/tests/test_coach_engine.py backend/tests/test_workout_plans_api.py backend/tests/test_workout_logs_api.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop127-relevant-full-rerun`
  - Result: `337 passed`.

### Manual Hebrew probes

- Current active monthly plan exists, then user says:
  - `תחליף לי את כל התוכנית לתוכנית חודשית חדשה במכון`
  - Result:
    - response says candidate does not replace yet;
    - current plan stays active;
    - candidate is `monthly_plan`, `is_current=false`;
    - pending action points at candidate.
- While the replacement candidate is still pending, user says:
  - `אימון להיום 20 דקות בלי ציוד`
  - Result:
    - response says `אימון חד-פעמי`;
    - pending replacement remains open;
    - one-off count is `1`;
    - one-off is `is_current=false`;
    - one-off duration is `20`.
- User then says:
  - `כן להחליף`
  - Result:
    - response says the new plan is active;
    - candidate becomes active;
    - old active plan is deleted;
    - one-off workout remains preserved.

### Ponytail Review

- Result:
  - Small classifier and context fix; no rewrite of pending-action architecture.
- Rationale:
  - The persistence model was already sound.
  - The bug was intent routing around natural Hebrew state-change phrasing.
  - Keeping the fix at routing + tests preserves the existing service boundaries.

### Next research target

- Loop 128 should inspect active-plan update semantics after scoped edits:
  - whether row sync handles removed/added exercises, not only changed existing rows;
  - whether plan edit history is enough for dashboard/context builder;
  - whether Hebrew responses distinguish “changed active plan” from “new candidate” in all scoped-edit cases.
## Loop 128 - Scoped Edit Row Sync and Log History

### Research sources

- ACSM Clinical Exercise Physiologist crosswalk: https://acsm.org/wp-content/uploads/2025/01/acsm-cep-crosswalk.pdf
- JMIR mHealth adherence measurement framework: https://www.jmir.org/2022/6/e30817
- ACSM CPT behavior-change competencies: https://acsm.org/wp-content/uploads/2025/01/acsm-cpt-crosswalk.pdf

### Findings extracted

- ACSM CEP competencies include teaching intensity with RPE/talk test, evaluating and modifying exercise prescription based on compliance, signs/symptoms and physiologic response, and using systems for tracking progress.
- mHealth adherence work reinforces that self-monitoring only helps when the tracked structure matches the plan the user is actually following.
- Product rule: `plan_json` is not enough. If users log against `Workout` and `WorkoutExercise` rows, scoped active-plan edits must keep those rows synchronized.
- Product rule: historical logs are coaching evidence. If an edited plan removes a workout day, detach old `WorkoutLog.workout_id` instead of deleting the log.

### Changes made

- `backend/app/services/workout_service.py`
  - Fixed `_sync_plan_rows_from_json()` so active-plan JSON edits add missing `Workout` rows, update existing rows, and delete extra workout days.
  - Added `_sync_workout_exercise_rows()` so exercise rows are added, updated, or removed to match the edited day JSON.
  - Preserved workout-log history when a day is removed by setting `WorkoutLog.workout_id=None` before deleting the old `Workout` row.
  - Fixed a nullable-field risk by creating new `Workout` and `WorkoutExercise` rows with required `name` fields before flushing.
- `backend/app/services/coaching_knowledge.py`
  - Added scoped-plan implementation rules: sync `Workout`/`WorkoutExercise` rows to `plan_json`, and detach logs instead of deleting history.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added the persistence rule for scoped edits and log-history preservation.
- `backend/tests/test_workout_plans_api.py`
  - Added a test proving `_sync_plan_rows_from_json()` removes and adds exercise rows to match edited JSON.
  - Added a test proving removing a day deletes the old workout row while preserving the workout log with `workout_id=None`.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertions that scoped-plan implementation rules mention `WorkoutExercise`, `plan_json`, `WorkoutLog.workout_id`, and log history.

### Tests and checks

- Focused loop run:
  - `python -m pytest backend/tests/test_workout_plans_api.py::test_workout_service_sync_plan_rows_adds_and_removes_exercise_rows backend/tests/test_workout_plans_api.py::test_workout_service_sync_plan_rows_removes_extra_workouts_without_deleting_logs backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols --basetemp .pytest-tmp-loop128-focused`
  - Result: `3 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_workout_logs_api.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop128-relevant-full`
  - Result: `310 passed`.

### Manual Hebrew probe

- First manual probe failed before the scoped edit because the temporary DB path was reused and no active plan was found. I reran with a fresh DB and Unicode-escaped Hebrew strings to avoid PowerShell encoding ambiguity.
- Fresh manual flow:
  - User creates a Hebrew monthly gym plan with bench available.
  - User says in Hebrew that they do not have a bench and asks to replace only what is needed.
  - Result:
    - response status `200`;
    - provider status `local_tool`;
    - `plan_json` exercise count stayed aligned with `WorkoutExercise` row count: `15 == 15`;
    - `bench_in_plan_json_after=False`;
    - `bench_in_rows_after=False`;
    - `plan_edit_history` length became `1`;
    - `row_sync_ok=True`.

### Next research target

- Loop 129 should inspect active-plan context/dashboard behavior after scoped edits:
  - whether next-workout and dashboard summaries display the edited exercise rows rather than stale names;
  - whether plan edit history should surface in provider context or remain internal;
  - whether Hebrew responses for scoped edit should include one tracking instruction tied to the edited exercise.
## Loop 129 - Dashboard and Next-Workout State After Scoped Edits

### Research sources

- ACSM 2026 fitness trends, mobile exercise apps and progress tracking: https://acsm.org/top-fitness-trends-2026/
- JMIR mHealth prompts and self-monitoring exercise behavior: https://mhealth.jmir.org/2019/9/e12956/
- JMIR MyBehavior personalized feedback from logged behavior: https://mhealth.jmir.org/2015/2/e42/
- JMIR systematic review of mobile apps for health behavior change: https://mhealth.jmir.org/2020/3/e17046/

### Findings extracted

- ACSM frames apps as supplemental tools whose value depends on structure, self-monitoring, goal setting, progress tracking, user engagement, and program quality.
- JMIR prompt data suggests self-monitoring and exercise behavior can increase after timely prompts, but effects depend on engagement and context.
- Personalized feedback literature supports low-effort suggestions based on prior tracked behavior, not generic advice disconnected from logs.
- Systematic reviews are cautious: apps alone do not reliably change outcomes. The product should therefore make dashboard actions concrete, loggable, and connected to real plan rows.

### Changes made

- `backend/app/services/dashboard_service.py`
  - Changed dashboard `current_workout_plan` serialization from `WorkoutService.serialize_plan(plan)` to `workout_service.serialize_plan_with_rows(plan)`.
  - This keeps dashboard plan days aligned with current `Workout` and `WorkoutExercise` rows, including `workout_id` and `exercise_id`.
- `backend/app/services/coaching_knowledge.py`
  - Added `adherence_dashboard_review.implementation_rules` requiring dashboard and next-workout surfaces to use synced rows and keep loggable IDs available after scoped edits.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added a dashboard/next-workout serialization rule tied to scoped edits and logging.
- `backend/tests/test_dashboard_api.py`
  - Added `test_dashboard_current_plan_uses_edited_workout_rows_after_scoped_edit`.
  - The test proves that after a no-bench scoped edit, dashboard current plan exposes `workout_id`/`exercise_id`, next workout matches the edited first exercise, and bench is gone from exercise/equipment surfaces.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertions for dashboard implementation rules mentioning `WorkoutExercise`, `plan_json`, `workout_id`, and `exercise_id`.

### Tests and checks

- First focused run:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_current_plan_uses_edited_workout_rows_after_scoped_edit backend/tests/test_dashboard_api.py::test_dashboard_next_recommended_action_reflects_available_state backend/tests/test_workout_logs_api.py::test_next_workout_api_returns_first_workout_without_logs --basetemp .pytest-tmp-loop129-focused`
  - Result: `1 failed, 2 passed`.
  - Failure: the test asserted `bench` was absent from the whole serialized current plan, but `plan_edit_history.edit_type=remove_bench` legitimately contains the word `bench`.
  - Fix: narrowed the assertion to exercise/equipment surfaces only.
- Focused rerun:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_current_plan_uses_edited_workout_rows_after_scoped_edit backend/tests/test_dashboard_api.py::test_dashboard_next_recommended_action_reflects_available_state backend/tests/test_workout_logs_api.py::test_next_workout_api_returns_first_workout_without_logs --basetemp .pytest-tmp-loop129-focused-rerun`
  - Result: `3 passed`.
- Knowledge/dashboard focused run:
  - `python -m pytest backend/tests/test_dashboard_api.py::test_dashboard_current_plan_uses_edited_workout_rows_after_scoped_edit backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_progress_measurement_protocols --basetemp .pytest-tmp-loop129-knowledge-dashboard`
  - Result: `2 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_dashboard_api.py backend/tests/test_workout_logs_api.py backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop129-relevant-full`
  - Result: `328 passed`.

### Manual Hebrew probe

- Flow:
  - Hebrew chat creates a monthly gym plan with bench available.
  - Hebrew chat says the user has no bench and asks to replace only what is needed.
  - Dashboard is fetched afterward.
- Result:
  - `plan_status=200`;
  - `edit_status=200`;
  - `dashboard_status=200`;
  - `provider_status=local_tool`;
  - `first_day_workout_id=1`;
  - `next_workout_id=1`;
  - `first_exercise_id_present=True`;
  - `first_exercise_matches_dashboard=True`;
  - `bench_in_dashboard_exercises=False`;
  - `bench_in_dashboard_equipment=False`;
  - `next_action_has_log_instruction=True`.

### Next research target

- Loop 130 should inspect provider/context behavior after scoped edits:
  - whether `ContextBuilder` includes active plan rows or stale plan JSON only;
  - whether `plan_edit_history` should be summarized safely for the model;
  - whether Hebrew chat after an edit can answer "what changed in my plan?" from structured state without rereading full chat history.
## Loop 130 - Provider Context After Scoped Edits

### Research sources

- Systematic review of feedback generation and presentation in self-monitoring interventions: https://link.springer.com/article/10.1186/s12966-023-01555-6
- Systematic review of just-in-time adaptive interventions for physical activity: https://link.springer.com/article/10.1186/s12966-019-0792-7
- JMIR MyBehavior personalized feedback from logged behavior: https://mhealth.jmir.org/2015/2/e42/
- JMIR mobile prompts and self-monitoring exercise behavior: https://mhealth.jmir.org/2019/9/e12956/

### Findings extracted

- Feedback is more useful when tied to self-monitoring data and future goal setting, but evidence is mixed and feedback can become noisy or demotivating if poorly crafted.
- JITAI literature supports context-sensitive support based on current user status, but also warns about feasibility, timeliness, engagement, and insufficient evidence for broad claims.
- Product rule: provider context should carry enough structured active-plan state to answer practical questions like "what changed?", without sending full chat history or full plan dumps.
- Product rule: after scoped edits, the model needs a compact outline of loggable rows plus recent edit summaries, not stale `plan_json` metadata only.

### Changes made

- `backend/app/services/context_builder.py`
  - Reused one `WorkoutService` instance in `build()`.
  - Added compact `workout_outline` to `current_workout_plan`, derived from synced `Workout`/`WorkoutExercise` rows.
  - Added compact `recent_plan_edits` from `plan_edit_history`, including edit type, date, changed exercise count, and short summary.
- `backend/app/services/token_budgeting.py`
  - Preserved plan outline in optimized provider context as `current_workout_plan.outline`.
  - Preserved recent scoped edits in optimized provider context as `current_workout_plan.recent_edits`.
  - Kept limits tight: first 3 days and last 2 edits only.
- `backend/app/services/coaching_knowledge.py`
  - Added provider-context implementation rule for compact `workout_outline` and `recent_plan_edits`.
  - Restored compact horizon coverage so provider context still names `single_workout`, `weekly_plan`, `two_week_plan`, and `monthly_plan`.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added context rule for compact active-plan outline and recent edit summaries.
- `backend/tests/test_context_builder.py`
  - Added a test proving context after a no-bench scoped edit includes row IDs and recent edit summary.
- `backend/tests/test_token_optimization.py`
  - Added a test proving optimized context keeps plan outline and recent edits.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertion for the provider-context implementation rule.

### Tests and checks

- Focused loop run:
  - `python -m pytest backend/tests/test_context_builder.py::test_context_builder_includes_edited_plan_outline_and_recent_edits backend/tests/test_token_optimization.py::test_compact_provider_context_keeps_plan_outline_and_recent_edits backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_progress_measurement_protocols --basetemp .pytest-tmp-loop130-focused`
  - Result: `3 passed`.
- First context/token/knowledge run:
  - `python -m pytest backend/tests/test_context_builder.py backend/tests/test_token_optimization.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop130-context-token`
  - Result: `1 failed, 142 passed`.
  - Failure: `plan_horizon_summary` no longer included `weekly_plan`, so the four-plan-type compact contract was incomplete.
  - Fix: restored a compact provider horizon item naming all four plan types.
- Second context/token/knowledge run:
  - Result: `1 failed, 142 passed`.
  - Failure: the compact override lost the Hebrew phrases `אימון יחיד` and `שבועיים`.
  - Fix: added those Hebrew phrases back into the compact horizon line.
- Third context/token/knowledge run:
  - Result: `1 failed, 142 passed`.
  - Failure: the compact override lost the `כאב מעורפל` safety phrase.
  - Fix: restored `כאב מעורפל? ask`.
- Final context/token/knowledge run:
  - `python -m pytest backend/tests/test_context_builder.py backend/tests/test_token_optimization.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop130-context-token-rerun3`
  - Result: `143 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_context_builder.py backend/tests/test_token_optimization.py backend/tests/test_dashboard_api.py backend/tests/test_workout_logs_api.py backend/tests/test_workout_plans_api.py backend/tests/test_coach_engine.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop130-relevant-full`
  - Result: `359 passed`.

### Manual Hebrew probe

- Flow:
  - Hebrew chat creates a monthly gym plan with bench.
  - Hebrew chat says the user has no bench and asks to replace only what is needed.
  - Build `ContextBuilder` context for the Hebrew question "what changed in my plan?"
  - Build optimized provider request from that context.
- Result:
  - `plan_status=200`;
  - `edit_status=200`;
  - `provider_status=local_tool`;
  - `outline_count=3`;
  - `outline_first_has_workout_id=True`;
  - `outline_first_has_exercise_id=True`;
  - `recent_edit_type=remove_bench`;
  - `compact_outline_count=3`;
  - `compact_recent_edit_type=remove_bench`;
  - `question_not_in_recent_chat=True`;
  - `optimized_has_remove_bench=True`.

### Next research target

- Loop 131 should inspect actual chat behavior for "what changed in my plan?" and similar post-edit Hebrew questions:
  - decide if a local structured answer should handle this without provider;
  - ensure it references recent structured edits, not chat history;
  - keep the answer short with one next tracking action.
## Loop 131 - Local Post-Edit Plan Change Summary

### Research sources

- Feedback generation and presentation review: https://link.springer.com/article/10.1186/s12966-023-01555-6
- JITAI physical activity review: https://link.springer.com/article/10.1186/s12966-019-0792-7
- MyBehavior personalized low-effort suggestions from tracked behavior: https://mhealth.jmir.org/2015/2/e42/

### Findings extracted

- Feedback should be based on self-monitoring data, connect to future action, and avoid becoming noisy or generic.
- Post-edit questions are product-state questions. They should not require an LLM when `plan_edit_history` already contains the structured answer.
- Product rule: answer "what changed in my plan?" from the active plan's structured edit history, state that this was not a full plan replacement, and give one tracking action.

### Changes made

- `backend/app/services/coach_intent_service.py`
  - Added `workout_plan_change_summary` intent.
  - Detects Hebrew and English questions such as `מה השתנה לי בתוכנית?`, `מה שינית בתוכנית`, and `what changed in my plan?`.
  - Runs before `workout_plan_edit` so questions are not mistaken for new edit requests.
- `backend/app/services/coach_engine.py`
  - Added local handler for `workout_plan_change_summary`.
  - Added `_workout_plan_change_summary_response()` using the current active plan's `plan_edit_history`.
  - Added short edit summaries for no-bench, no-cable, row-machine replacement, push-up regression, pain substitution, and volume reduction.
  - Response includes one next tracking action with RPE/effort, pain, and completion.
- `backend/app/services/coaching_knowledge.py`
  - Added scoped-edit implementation rule: post-edit change-summary questions should answer from `plan_edit_history` and include one tracking action.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added the same structured-state rule for post-edit plan-change questions.
- `backend/tests/test_coach_intent_service.py`
  - Added intent tests for Hebrew and English post-edit change-summary questions.
- `backend/tests/test_coach_engine.py`
  - Added end-to-end chat test proving `מה השתנה לי בתוכנית?` returns a local structured answer after a no-bench edit.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertion for the new `plan_edit_history` implementation rule.

### Tests and checks

- Focused loop run:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_plan_change_summary_questions backend/tests/test_coach_engine.py::test_chat_plan_change_summary_uses_recent_structured_edit backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_plan_horizon_protocols --basetemp .pytest-tmp-loop131-focused`
  - Result: `3 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_coach_intent_service.py backend/tests/test_coach_engine.py backend/tests/test_context_builder.py backend/tests/test_token_optimization.py backend/tests/test_dashboard_api.py backend/tests/test_workout_logs_api.py backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop131-relevant-full`
  - Result: `390 passed`.

### Manual Hebrew probe

- Flow:
  - Hebrew chat creates a monthly gym plan with bench.
  - Hebrew chat says the user has no bench and asks to replace only what is needed.
  - Hebrew chat asks: `מה השתנה לי בתוכנית?`
- First probe:
  - Response text was correct and local, but printed boolean checks were false because the PowerShell inline script used direct Hebrew marker literals with encoding ambiguity.
- Second probe with Unicode-escaped markers:
  - `summary_provider=local_tool`;
  - `mentions_bench_removed_unicode=True`;
  - `mentions_not_full_replace_unicode=True`;
  - `mentions_tracking_unicode=True`.

### Next research target

- Loop 132 should inspect "show me/open my current plan" behavior:
  - whether users can retrieve the active structured plan through chat without provider;
  - whether response should summarize only next workout or expose full weekly/monthly structure;
  - whether the bot should avoid dumping a long monthly plan in chat and instead point to saved plan state.

## Loop 132 - Current Plan Summary From Saved State

### Research sources

- Feedback generation and presentation review: https://link.springer.com/article/10.1186/s12966-023-01555-6
- JITAI physical activity review: https://link.springer.com/article/10.1186/s12966-019-0792-7
- MyBehavior personalized low-effort suggestions from tracked behavior: https://mhealth.jmir.org/2015/2/e42/
- mHealth adherence measurement framework: https://www.jmir.org/2022/6/e30817

### Findings extracted

- Self-monitoring feedback should be tied to stored behavior data and should help the user choose the next action.
- For chat requests like "show me my plan", the product already has structured state; using a provider or dumping the whole monthly plan is wasteful.
- Product rule: answer current-plan chat questions from the saved active plan, show a short outline, keep it log-oriented, and explicitly avoid turning chat into a full-plan dump.

### Changes made

- `backend/app/services/coach_intent_service.py`
  - Added `current_workout_plan_summary` intent.
  - Detects Hebrew and English questions such as "תראה לי את התוכנית שלי", "מה התוכנית הפעילה שלי?", and "show me my current plan".
  - Runs before broad workout-plan edit handling so retrieval questions are not treated as new edits.
- `backend/app/services/coach_engine.py`
  - Added a local handler for `current_workout_plan_summary`.
  - Added `_current_workout_plan_summary_response()` using `WorkoutService.serialize_plan_with_rows()`.
  - Response includes plan name, plan type, duration, days per week, first three day summaries, and one next logging action.
  - Response explicitly avoids pasting the entire monthly plan into chat.
- `backend/app/services/coaching_knowledge.py`
  - Added an adherence/dashboard implementation rule for current-plan chat summaries.
- `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md`
  - Added the same rule to the knowledge-source notes.
- `backend/tests/test_coach_intent_service.py`
  - Added intent coverage for Hebrew and English current-plan questions.
- `backend/tests/test_coach_engine.py`
  - Added end-to-end chat coverage proving current-plan retrieval uses saved state and stays short.
- `backend/tests/test_coaching_knowledge.py`
  - Added assertion for the current-plan summary rule.

### Tests and checks

- Focused loop run:
  - `python -m pytest backend/tests/test_coach_intent_service.py::test_intent_service_detects_current_plan_summary_questions backend/tests/test_coach_engine.py::test_chat_current_plan_summary_uses_saved_plan_without_long_dump backend/tests/test_coaching_knowledge.py::test_coaching_knowledge_contains_progress_measurement_protocols --basetemp .pytest-tmp-loop132-focused`
  - Result: `3 passed`.
- Relevant full run:
  - `python -m pytest backend/tests/test_coach_intent_service.py backend/tests/test_coach_engine.py backend/tests/test_context_builder.py backend/tests/test_token_optimization.py backend/tests/test_dashboard_api.py backend/tests/test_workout_logs_api.py backend/tests/test_workout_plans_api.py backend/tests/test_coaching_knowledge.py --basetemp .pytest-tmp-loop132-relevant-full`
  - Result: `392 passed`.

### Manual Hebrew probe

- Flow:
  - Hebrew chat creates a monthly gym plan for 3 days per week.
  - Hebrew chat asks: `תראה לי את התוכנית שלי`.
- First probe:
  - Behavioral checks passed, but the inline script exited non-zero because Windows held the temporary SQLite file during cleanup.
- Clean rerun with explicit DB close/dispose:
  - `create_status=200`;
  - `create_provider=local_tool`;
  - `show_status=200`;
  - `show_provider=local_tool`;
  - `active_plan_exists=True`;
  - `intent=current_workout_plan_summary`;
  - `mentions_active_plan=True`;
  - `mentions_no_full_dump=True`;
  - `mentions_rpe=True`;
  - `response_len=447`;
  - `under_900_chars=True`.

### Next research target

- Loop 133 should inspect "open/start my next workout" behavior:
  - whether chat can retrieve the next loggable workout from the active plan without provider;
  - whether it exposes exercise IDs and a concise workout view rather than a plan-level summary;
  - whether it gives a practical start/log action with pain and RPE tracking.

## Audit Handoff P3 - Destructive Deletion and Status-Code Verification

### Verification target

- Confirm the legacy-memory cleanup migration is intentional and not referenced by live runtime code.
- Confirm the documented CALO BRAIN deletions/reductions do not leave live broken references.
- Confirm the single-workout activation status-code change to 400 does not break a client path that expects 404.

### Findings

- `supabase/migrations/202606230001_drop_legacy_memory_and_summaries.sql` is present and explicitly documents its destructive scope: dropping legacy `coaching_memories`, `memory_summaries`, and `weekly_summaries`.
- `backend/tests/test_supabase_integration.py` intentionally excludes this cleanup migration from the generic non-destructive migration guard and has a dedicated test asserting the three legacy drops.
- `rg "memory_summaries"` found only the old core schema migration, the cleanup migration, and the migration tests. No backend runtime service reads or writes `memory_summaries`.
- `CALO BRAIN/01_PRODUCT/02-Product-Behavior.md`, `CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md`, and `CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md` exist in the branch.
- `CALO BRAIN/05_OPERATIONS/03-Session-Handoffs.md` is absent. The remaining references found by `rg` are historical report/progress-log mentions, not live code or an active runtime dependency.
- `frontend/src/api.ts` no longer exports direct `activateWorkoutPlan()` / `discardWorkoutPlan()` helpers; search found no frontend caller for direct activation/discard.
- `frontend/src/WorkoutsPanel.tsx` uses pending-action confirmation through `resolvePendingAction()` for candidate activation, so the single-workout 400 status is not a frontend compatibility break.
- `backend/tests/test_workout_plans_api.py::test_activate_workout_plan_rejects_single_workout_and_keeps_current_plan` explicitly expects HTTP 400 for trying to activate a single workout.

### Commands run

- `git ls-files "supabase/migrations/202606230001_drop_legacy_memory_and_summaries.sql" "CALO BRAIN/01_PRODUCT/02-Product-Behavior.md" "CALO BRAIN/03_REFERENCE/03-Prompt-Registry.md" "CALO BRAIN/05_OPERATIONS/03-Session-Handoffs.md" "CALO BRAIN/06_RESEARCH/02-Coaching-Knowledge-Source.md"`
- `rg -n "02-Product-Behavior|03-Prompt-Registry|03-Session-Handoffs|02-Coaching-Knowledge-Source|202606230001_drop_legacy_memory_and_summaries|drop_legacy_memory|memory_summaries" --glob '!node_modules/**' --glob '!.git/**'`
- `rg -n "activateWorkoutPlan|resolvePendingAction|candidate_plan|validCandidatePlan|setError|catch" frontend/src/WorkoutsPanel.tsx frontend/src/api.ts frontend/src/WorkoutsPanel.test.tsx`
- `rg -n "404|400|single workout|single_workout|activate" frontend/src/WorkoutsPanel.test.tsx frontend/src/api.ts`

### Result

- No restore was needed.
- No code change was needed for the activation status-code path.
- Future destructive doc/database deletions should stay isolated from feature commits.

## Final Merge-Readiness Local Smoke - 2026-06-26

### Verification target

- Prove the current branch still runs the core local product loop after the workout-plan and audit cleanup changes.
- Keep live Supabase proof separate from local SQLite/no-auth proof.

### Command run

- Inline FastAPI `TestClient` smoke with file-backed SQLite under `.pytest-tmp`.

### Covered flow

- `GET /api/health`
- `GET /api/readiness`
- `POST /api/onboarding`
- `POST /api/chat` with a workout-plan request
- `GET /api/workout-plans/current`
- `GET /api/workouts/next`
- `POST /api/workout-logs`
- `GET /api/workout-logs/recent`
- `POST /api/meals/manual`
- `GET /api/meals/recent`
- `POST /api/body-metrics`
- `GET /api/dashboard`
- `GET /api/usage`
- `GET /api/settings/export`
- `POST /api/settings/reset`

### Result

- Smoke status: passed.
- Key output:
  - `health_status=ok`
  - `chat_provider_status=local_tool`
  - `plan_type=weekly_plan`
  - `workout_logged_status=completed`
  - `recent_logs=1`
  - `meal_confidence=medium`
  - `recent_meals=1`
  - `dashboard_next_action_present=true`
  - `export_has_workout_plans=true`
  - `reset_deleted_records=32`
  - `readiness_production_ready=false`
- Boundary: this proves local product flow only. `npm run verify:supabase` remains the required live Supabase/RLS/Storage proof.

## Final Hebrew-First UI Cleanup - 2026-06-26

### Verification target

- Keep the visible local/no-key and settings status UI Hebrew-first before merging.
- Keep test fixtures aligned with Hebrew-first product behavior so English mock copy does not hide regressions.

### Changes

- Translated the no-API-key provider alert in the app shell.
- Translated visible Supabase auth/storage labels and formatted Supabase status values.
- Updated frontend status fixtures for dashboard/settings smoke tests to Hebrew copy.
- Added frontend assertions that the old English local-mode/status/disclaimer strings do not reach the rendered UI.

### Checks run

- `npm --prefix frontend test -- --run App.test.tsx SettingsPanel.test.tsx`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run lint`
- `npm run lint`
- `npm run build`
- `npm test`
- `git diff --check`
- `python scripts/secret_scan.py`
- `git merge-tree --write-tree origin/main HEAD`

### Result

- Latest pushed commits:
  - `470757f Translate remaining settings status UI`
  - `d7ae8b5 Keep frontend status fixtures Hebrew-first`
- Frontend tests: `50 passed`.
- Full local suite: backend `586 passed`, frontend `50 passed`.
- Build, lint, diff check, and secret scan passed.
- Merge-tree against `origin/main` returned a tree id without conflicts.
- Boundary unchanged: live Supabase verification remains skipped/unproven until valid live credentials are available.

## Final Hebrew-First API Error Cleanup - 2026-06-26

### Verification target

- Keep API-facing error details Hebrew-first for auth, storage, pending actions, body metrics, workout plans, workout logs, and validation errors.
- Preserve status codes and deterministic behavior; only translate the returned detail text.

### Changes

- Translated Supabase auth token/config error details.
- Translated Supabase Storage required details for meal-image paths.
- Translated pending-action and body-metric not-found details.
- Translated workout-plan activation/deletion and workout-log reference errors.
- Translated workout-log and body-metric validation messages.

### Checks run

- `python -m pytest backend/tests/test_supabase_integration.py backend/tests/test_meal_upload_api.py backend/tests/test_workout_plans_api.py --basetemp .pytest-tmp-api-hebrew`
- `python -m pytest backend/tests/test_body_metrics_api.py backend/tests/test_coach_engine.py backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-api-hebrew-extra`
- `npm test`
- `npm run lint`
- `git diff --check`

### Result

- Latest pushed commit:
  - `015bc94 Translate API error details to Hebrew`
- Focused API tests: `81 passed`.
- Extra backend coverage: `166 passed`.
- Full local suite: backend `586 passed`, frontend `50 passed`.
- Lint and diff check passed.
- Boundary unchanged: live Supabase verification remains skipped/unproven until valid live credentials are available.

## Final Frontend Auth Error Cleanup - 2026-06-26

### Verification target

- Remove remaining English Supabase auth runtime error strings from the frontend helper.

### Changes

- Translated missing-config, failed-auth, and missing-token errors in `frontend/src/auth.ts`.

### Checks run

- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run lint`
- `git diff --check`

### Result

- Latest pushed commit:
  - `d86d586 Translate frontend auth errors to Hebrew`
- Frontend tests: `50 passed`.
- Frontend lint and diff check passed.
- Search for the old English auth/API status strings returned no runtime matches.

## Final Frontend API Error Consolidation - 2026-06-26

### Verification target

- Remove repeated English `API request failed` runtime errors from the shared frontend API client.
- Keep behavior the same while reducing duplicated error handling.

### Changes

- Added one shared `assertOk(response)` helper in `frontend/src/api.ts`.
- Replaced repeated per-endpoint `if (!response.ok)` blocks with the shared helper.
- Changed the frontend API failure message to Hebrew.
- Changed the fallback chat-session title default from `Coach chat` to `צ'אט מאמן`.

### Checks run

- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run lint`
- `npm test`
- `npm run build`
- `npm run lint`
- `git diff --check`

### Result

- Latest pushed commit:
  - `58e769f Centralize frontend API error handling`
- Full local suite: backend `586 passed`, frontend `50 passed`.
- Build, lint, and diff check passed.
- Search for the old `API request failed` and `Coach chat` runtime strings returned no matches.

## Final Hebrew-First Readiness Cleanup - 2026-06-26

### Verification target

- Keep `/api/readiness` diagnostic details Hebrew-first while preserving machine-readable status keys.

### Changes

- Translated readiness check details and issue messages.
- Kept `status`, check names, env var names, and boolean fields unchanged as API contract.

### Checks run

- `python -m pytest backend/tests/test_supabase_readiness.py --basetemp .pytest-tmp-readiness-hebrew`
- `npm test`
- `npm run lint`
- `git diff --check`

### Result

- Latest pushed commit:
  - `ae0faed Translate readiness details to Hebrew`
- Readiness tests: `4 passed`.
- Full local suite: backend `586 passed`, frontend `50 passed`.
- Lint and diff check passed.
- Boundary unchanged: live Supabase verification remains skipped/unproven until valid live credentials are available.

## Final Local Live Hebrew Smoke - 2026-06-26

### Verification target

- Verify the already-running local backend/frontend still respond after the final Hebrew-first cleanup commits.
- Confirm readiness/settings text is valid UTF-8 Hebrew, not only test-proven strings.

### Checks run

- `GET http://127.0.0.1:8000/api/readiness`
- `GET http://127.0.0.1:8000/api/settings`
- `GET http://127.0.0.1:5173`
- `GET http://127.0.0.1:5174`
- Explicit Python UTF-8 decode for readiness/settings response bodies.

### Result

- Backend health/readiness server responded.
- Frontend dev servers on ports `5173` and `5174` returned HTTP 200.
- Decoded readiness detail included: `SQLite למסד נתונים מקומי בפיתוח`.
- Decoded readiness issue included: `אימות Supabase לא נדרש`.
- Decoded settings disclaimer began with Hebrew medical-safety wording.
- Existing dev-server processes were left running because they may belong to the local workspace session.

## Final Frontend API Error Test Coverage - 2026-06-26

### Verification target

- Ensure the shared frontend API failure helper is directly covered, not only indirectly covered by UI tests.
- Preserve existing API-client coverage for Supabase bearer-token headers.

### Changes

- Expanded `frontend/src/api.test.ts` to assert the shared Hebrew API failure error.
- Added coverage for the Hebrew default chat-session title.
- Restored and kept the existing bearer-token header test.

### Checks run

- `npm --prefix frontend test -- --run api.test.ts`
- `npm --prefix frontend run lint`

### Result

- Latest pushed commit:
  - `5b8cc88 Cover frontend API Hebrew errors`
  - `8bd059c Fix API client test build typing`
- API client tests: `5 passed`.
- First full `npm run build` after adding the test failed on TypeScript mock-call tuple typing.
- Fixed the test with an explicit typed mock-call cast.
- Full local suite after the fix: backend `586 passed`, frontend `52 passed`.
- Build, lint, and diff check passed after the fix.
- Frontend lint passed.

## Final Schema Hebrew Validation Coverage - 2026-06-26

### Verification target

- Lock the Hebrew validation messages returned by workout-log and body-metric request schemas.
- Keep the check at the schema layer because the behavior already exists and only lacked direct coverage.

### Changes

- Added direct schema tests for empty workout logs, empty body metrics, invalid measurement names, and invalid measurement values.
- No production behavior changed.

### Checks run

- `python -m pytest backend/tests/test_workout_schema.py backend/tests/test_body_metrics_api.py backend/tests/test_workout_logs_api.py --basetemp .pytest-tmp-schema-hebrew`

### Result

- Focused schema/body-metric/workout-log suite: `44 passed`.

## Final Hebrew User Error Cleanup - 2026-06-26

### Verification target

- Remove the remaining direct `User not found` service errors from the Hebrew-first backend surface.

### Changes

- Translated missing-user service errors in coach engine, dashboard, settings export, and onboarding profile save.
- Added a ProfileService regression test for the Hebrew missing-user error.

### Checks run

- `python -m pytest backend/tests/test_profile_service.py backend/tests/test_dashboard_api.py backend/tests/test_settings_api.py backend/tests/test_coach_engine.py --basetemp .pytest-tmp-hebrew-user-errors`
- `rg -n "User not found" backend/app backend/tests -S`

### Result

- Focused service/API suite: `154 passed`.
- No `User not found` matches remain in backend app/tests.

## Final Auth Profile Hebrew Default Cleanup - 2026-06-26

### Verification target

- Remove the remaining English fallback name for Supabase-authenticated users without an email.

### Changes

- Changed the auth-user default display name from `Supabase user` to `משתמש Supabase`.
- Added a ProfileService regression test for this no-email auth-user path.

### Checks run

- `python -m pytest backend/tests/test_profile_service.py --basetemp .pytest-tmp-profile-auth-name`
- `rg -n "Supabase user" backend/app backend/tests -S`

### Result

- Profile service tests: `5 passed`.
- No `Supabase user` matches remain in backend app/tests.

## Final Supabase Live Verifier Attempt - 2026-06-26

### Verification target

- Re-check the repo's only external smoke script after the final local gates.

### Checks run

- `npm run verify:supabase`

### Result

- Failed before live proof with `invalid_credentials` from Supabase Auth sign-in.
- No local code change was made for this because the blocker is missing/invalid live test credentials, not a failing local invariant.
- Merge-readiness boundary remains: local tests/build/lint/merge-tree are proven; live Supabase user-isolation/storage proof still requires valid `SUPABASE_TEST_USER_*` credentials or a trusted `SUPABASE_SECRET_KEY`.
