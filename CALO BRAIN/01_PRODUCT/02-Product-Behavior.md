---
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
type: product
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
status: active
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
source_of_truth: true
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
updated: 2026-06-20
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
related_paths:
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
  - backend/app/services/context_builder.py
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
notes: >-
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
  System behavior guarantees and behavior contract
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
---
# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Generic English headings or phrases such as `Weekly summary`, `Action plan`, `recover tomorrow`, `workout`, or `protein timing` are not protected terms. Hebrew responses may keep professional terms such as RPE, RIR, DOMS, HIIT, Zone 2, full-body, push/pull/legs, split, deload, progressive overload, and common exercise names when they sound natural in Israeli fitness usage.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

The Hebrew language rule is not "translate every English fitness term." The coach should sound like a clear Israeli fitness coach: use סטים and חזרות, keep RPE/RIR/DOMS when useful, say דילואד or שבוע הורדת עומס, explain progressive overload as התקדמות הדרגתית, and avoid literal phrases like מערכות, הישנויות, פריקת עומס, or long textbook definitions in normal chat.

When the user explicitly asks not to be addressed in masculine or feminine language, chat answers and generated workout-plan guidance should use neutral Hebrew phrasing such as אפשר, כדאי, לבחור, לבצע, and avoid direct אתה/את forms where practical.

If a configured chat provider violates an explicit neutral-address request with direct masculine/feminine address or direct Hebrew commands such as `אתה`, `הוסף`, or `תוסיף`, the backend does not display that provider text. Knowledge intents fall back to the vetted local Hebrew answer when available; generic provider-backed chat returns a neutral Hebrew retry message instead of saving the offending response.

Common term-explanation and high-frequency coaching questions can bypass the provider and return deterministic local coaching answers. Current local coverage includes RPE/RIR, hypertrophy and hard sets, progression when sets feel easy, deload signals, DOMS, Zone 2, split choice, warmup/cooldown, low-energy one-action guidance, common equipment substitutions, returning after missed workouts, weekly action-plan guidance, stimulant/pre-workout supplement safety, workout-adjacent nutrition, and food-image calorie uncertainty. RPE/RIR answers should preserve the user's stated values instead of forcing every case into the default RPE 8 / RIR 2 explanation.

Workout plans are structured app data, but user-facing guidance fields inside them must still be Hebrew. `progression_model`, `recovery_note`, `safety_notes`, exercise `notes`, `progression`, and `regression` should not leak English operational phrasing such as “Stop”, “Use”, “Reduce”, or “Do not”. Internal status identifiers may remain in `decision_inputs` when they are not rendered as coaching copy.

For workout planning, provider context also includes a compact coaching decision framework: needs analysis, FITT-VP variables, exercise order, load/reps, volume, rest, deload triggers, and high-level technique cues for squat, hinge, push, pull, and core patterns.

Workout-plan contexts also include compact program-quality audit guidance. When the user asks whether a plan is good, the coach should identify the strongest part, name the central gap, and suggest one practical change based on goal fit, weekly structure, movement coverage, volume/recovery, progression, exercise fit, adherence feasibility, and safety scope.

For workout-plan and workout-log contexts, provider context also includes full-coach decision summaries: exercise prescription principles, simple periodization, cardiorespiratory intensity guidance, and warmup/mobility rules. This expands coaching capability without changing API state or adding new blockers.

Workout-plan and workout-log contexts include compact program adaptation guidance. The coach should use recent logs to decide whether to progress one variable, maintain, deload, swap an exercise, handle a plateau, recover from missed sessions, or return after a break. This is adaptation support, not a new refusal path.

Workout-plan and workout-log contexts include compact movement-limitation adaptation guidance. When the user reports common non-emergency limits around the knee, low back, shoulder, wrist, or mobility, the coach should adapt range of motion, load, angle, support, or exercise selection while staying non-diagnostic. This is not a new blocker; existing safety handling still covers sharp, worsening, dangerous, or medical symptoms.

Workout-plan and workout-log contexts include compact special-population guidance. For youth, pregnancy/postpartum, chronic conditions/disabilities, and older adults, the coach should scale intensity, volume, supervision, exercise selection, and progression to the user's ability and context. This expands planning knowledge only; it does not authorize medical advice or add new runtime blockers.

Workout-plan and workout-log contexts include compact instruction-coaching guidance. The coach should teach movements with short show-tell-do style instructions, one cue at a time, useful feedback frequency, warmup/cooldown framing, and technique safety checks. This improves coaching quality without adding new refusal paths or runtime blockers.

Workout-plan and workout-log contexts also include compact setup and equipment-safety guidance. The coach should remind users to adjust seats/pads/handles, use rack safeties or a suitable spotter for risky free-weight work, use simple brace/breathing cues, and switch to a stable variation when cueing is not enough. This is practical setup coaching, not a new medical or runtime blocking path.

Workout-plan and workout-log contexts include compact weekly-structure guidance. The coach should choose a realistic weekly structure from availability, experience, goal, recovery, and logs: often full-body for 2-3 days, upper/lower for many 4-day cases, and push/pull/legs or other advanced splits only when consistency and recovery support it.

Workout-plan and workout-log contexts include compact volume-progression guidance. The coach should use logged reps, sets, load, RIR/RPE, pain, missed sessions, and recovery to choose one progression at a time: add clean reps, then small load jumps, then sets or frequency only when the user can recover. It should treat 10 weekly sets per muscle as a gradual hypertrophy target, not a default starting demand.

Workout-plan and workout-log contexts include compact advanced strength/hypertrophy guidance. The coach should use failure sparingly, prefer 1-3 RIR for most work sets, use specialization blocks only temporarily, troubleshoot plateaus by checking consistency/sleep/nutrition/rest first, and rotate exercises only when it preserves the goal.

For hypertrophy questions, the coach should talk in practical gym language: hard sets per muscle per week, broad rep ranges that work when close enough to failure, and log-driven increases rather than fixed “magic” volume.

Workout-plan and workout-log contexts include compact load-prescription guidance. The coach should choose starting loads from target reps and RIR, adjust set-to-set from RPE and technique, decide next-session load from clean logged performance, and treat e1RM as a rough estimate rather than a reason to push max testing.

Workout-plan and workout-log contexts include compact concurrent-training guidance. The coach should combine strength and aerobic work by the user’s main goal, put the priority work first when sessions are combined, and manage high-impact running or hard cardio without telling users to avoid cardio categorically.

Workout-plan and workout-log contexts include compact equipment-substitution guidance. The coach should preserve the movement pattern and training intent when equipment is missing: use bodyweight, bands, dumbbells, machines/cables, tempo, pauses, unilateral work, range of motion, or rep targets before declaring that a workout cannot be done.

Workout-plan and workout-log contexts include compact session-structure guidance. The coach should order power/technical and compound work before assistance work, choose rest intervals by goal, use tempo when useful, apply supersets/circuits only when they do not break technique, and keep necessary warmup/ramp sets.

Workout-plan and workout-log contexts include more precise warmup and cooldown guidance. The coach should use dynamic warmup and ramp sets before demanding work, use static stretching mainly for flexibility or comfort when appropriate, and avoid promising that stretching or cooldown prevents DOMS.

Workout-plan and workout-log contexts include compact readiness/recovery guidance. The coach should use RPE, sleep, stress, DOMS, performance trends, and red-flag boundaries to decide whether today is a small-progress day, maintain day, reduced-load day, or safety-led response.

Workout-plan and workout-log contexts also include compact advanced recovery/readiness guidance. The coach should handle sleep debt, high-stress days, DOMS, return after illness, travel weeks, and overreaching signs with practical load adjustments, minimum-action options, and non-punitive Hebrew wording. This expands coaching knowledge; it does not add a new runtime blocker.

Workout-plan and workout-log contexts include program lifecycle guidance. The coach should distinguish normal weeks, deload, maintenance, test week, taper, plateau handling, reassessment cadence, and exercise changes using logs and goals instead of changing the plan randomly.

Workout-plan and workout-log contexts include compact field-assessment guidance. The coach may suggest one to three simple baseline checks such as 6MWT/2MST, chair stand, TUG, balance, or movement snapshots when they change the plan; results are for personal comparison and programming decisions, not diagnosis or medical screening.

Workout-plan and workout-log contexts include compact progress-measurement guidance. The coach should choose metrics by goal, read strength/cardio/body-composition trends from logs, avoid reacting to one noisy data point, and turn weekly review into one practical next action.

Workout-plan and workout-log contexts include compact exercise-science foundation guidance. The coach may use energy systems, planes of motion, joint actions, force vectors, stability, fatigue, and motor-learning basics to choose exercises or adjustments, but should expose only the practical explanation needed for the next action.

Workout-plan and workout-log contexts include compact speed/agility/plyometric guidance. The coach should treat jumps, sprints, deceleration, and reactive agility as short high-quality work: landing mechanics before more height or contacts, sprint/change-of-direction work before fatigue, adequate rest, and conservative regressions when impact quality drops. This is programming knowledge, not a new medical blocker.

Workout contexts include compact goal-specific programming guidance for beginner foundation, strength, hypertrophy, muscular endurance, power, and fat-loss support. The full structured table stays in `CoachingKnowledgeService`; provider context gets only the short `goal_programming_summary`.

Workout contexts include compact profile-based programming guidance. The coach should choose the planning path from the stored profile and request: beginner or returning user, intermediate/advanced user, older adult, limited time, limited equipment, strength, hypertrophy, fat-loss support, or endurance. The full structured table stays in `CoachingKnowledgeService`; provider context gets only `profile_programming_summary`.

Workout contexts include compact cardio programming guidance for base aerobic work, run-walk starts, talk-test/RPE intensity, Zone 2 progression, running-volume progression, Zone 3/HIIT/hill boundaries, fat-loss support, and endurance-event distribution. The coach should treat most beginner runs as easy, avoid making every run a pace test, and adapt missed runs without stacking all missed volume into one day. The full structured cardio and walking/running tables stay in `CoachingKnowledgeService`; provider context gets only `cardio_programming_summary`.

Workout contexts also include a compact `exercise_library_summary` for major movement patterns: squat, hinge, push, pull, lunge, carry, and core. The richer structured exercise library stays in the service layer for tests and future modules instead of being sent wholesale to the model.

Workout contexts also include compact anatomy/muscle mapping. The coach may mention practical groups such as quads, glutes, hamstrings, chest, shoulders, triceps, back, scapula and biceps, but should still reason through movement patterns and avoid pretending to diagnose weak muscles remotely.

For workout-log and planning contexts, the app also sends `training_status`: a compact interpretation of recent completions, skipped workouts, pain flags, RPE/recovery signals, and one suggested adjustment. This is coaching context for better decisions, not a new refusal mechanism.

For meal-log and meal-image contexts, provider context includes compact sports-nutrition guidance: protein ranges for active users, carbohydrate fueling around training, hydration awareness, body-composition signals beyond scale weight, and meal timing. This expands coaching knowledge without adding a new blocking path.

For body-composition questions, the coach should use trend-based progress: weekly-average weight, optional waist/measurements/photos only if the user wants them, strength/performance, energy, sleep, and adherence. Maintenance phases and diet breaks are allowed as adherence tools, not as magic metabolism resets.

For meal-log and meal-image contexts, provider context also includes practical non-clinical nutrition guidance. The coach should prefer simple plate-building, protein anchors, produce/fiber additions, water habits, fallback meals, and clear image-estimate uncertainty over rigid menus or exact calorie claims.

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk. Obvious stimulant safety questions about high-caffeine pre-workout, yohimbine, or fat burners are handled locally before generic nutrition timing so the user does not receive meal-timing advice for a supplement-risk question.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

The Markdown cleanup also removes common list markers, numbered-list prefixes, blockquotes, and simple table pipes when a provider ignores the plain-text instruction. This is cleanup only; it is not a post-model translator and should not rewrite coaching or safety meaning.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, stimulant supplement safety, weekly action-plan guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state. A single-session plan becomes current only when there is no active plan or when the current plan is already a single-session plan; it does not replace an active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. Prompt inference can override profile defaults for explicit requests such as a 30-minute gym workout. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout-plan UI copy should use natural Hebrew singular/plural wording, such as "יום אחד בשבוע" and "סט אחד" instead of "1 ימים בשבוע" or "1 סטים".

The workout-plan UI should expose persisted plan metadata that affects interpretation, including `single_session` as "אימון יחיד" and the saved session duration such as "30 דקות".

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

The workout execution loop is plan-backed. `GET /api/workouts/next` returns the next workout from the active saved plan with row-level `workout_id` and `exercise_id` values. If the latest plan log was completed without pain, the next workout advances by plan order and wraps to the start. If the latest log was skipped, partial, modified, or pain-flagged, the same workout is returned with a conservative adjustment.

`GET /api/workouts/next` also returns a non-persisted `execution_plan` derived from the base workout and recent logs. The base `exercises` remain unchanged. `execution_plan.adjusted_exercises` is the version to perform today: missed/partial sessions become a shorter minimum version, pain logs reduce or swap conservatively, high-RPE logs reduce or hold, and progress candidates get only one small progression cue.

Structured workout logs can be saved through `POST /api/workout-logs` with `workout_id`, `status`, `logged_on`, exercise results, set-level reps/weight/duration/completion, RPE/RIR, pain flag, and notes. `workout_id` must belong to the local user, and any `exercise_id` must belong to that workout; unknown or mismatched row IDs are rejected instead of being persisted. These details are persisted in `WorkoutLog.exercise_results` JSON while `WorkoutLog.workout_id`, `status`, `rpe`, `pain_flag`, and `notes` remain the primary queryable fields. Text-only `{ "text": "..." }` logging remains supported for backwards compatibility.

The Workouts UI shows the executable version when `execution_plan` exists and logs against the base workout/exercise IDs through `source_exercise_id`. It validates structured log inputs before POST: RPE/RIR must be whole numbers in their supported ranges, set reps must be whole numbers separated by commas, and pain-marked logs require a short note describing what was felt. Untouched exercise rows are omitted from partial/modified payloads so a partial workout does not overstate every planned exercise.

The Workouts UI also shows recent persisted workout logs after refresh and immediately after saving a free-text or structured log. Recent logs should show date, natural Hebrew status/confidence labels, RPE when present, pain flags, notes, and a short exercise summary without exposing internal status identifiers.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

The dashboard uses a read-only current weekly summary preview so opening the dashboard does not create a `WeeklySummary` row or increment summary usage. Explicit weekly-summary requests through chat or `/api/summaries/weekly` still update the persisted weekly row and usage tracking.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

The Meals UI should show recent persisted meals, not only the just-submitted result. Recent meals display date/type, confidence, calorie/protein ranges, and detected/manual items as approximate tracking data. It should not expose raw local file paths or imply exact nutrition accuracy.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

Generic English nutrition phrasing such as `protein timing` is treated as avoidable English in user-facing image-analysis copy and should be replaced by the Hebrew fallback unless the provider returns natural Hebrew wording.

## Memory

The app stores durable coaching facts, not every casual detail. Examples worth storing:

- Preferred workout length
- Available equipment
- Disliked activities
- Usual training time
- Coaching style preference
- Safety limitations

Hebrew-first durable facts are extracted from chat into structured memory, including short-workout preference, evening/after-work schedule, Tuesday/Thursday evening availability, dumbbells, resistance bands, dislike of running, no-jump preference, and common nutrition preferences such as plant-based or lactose sensitivity. Lactose sensitivity extraction supports common masculine/feminine Hebrew wording such as "רגיש ללקטוז" and "רגישה ללקטוז".

Safety-relevant chat memories, such as knee pain or sensitivity, are stored as sensitive `safety_limitation` memories. They are available to the context builder through `caution_notes` but are not shown as ordinary dashboard coach notes.

## Safety

The app gives general wellness guidance only. It does not diagnose injury, illness, eating disorders, or medical conditions.

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories in a daily diet or restriction context, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`. Ordinary meal descriptions such as a 900-calorie dinner should not be treated as extreme dieting by themselves.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

Workout-log safety classification runs on the full log source text, including exercise-level notes, not only on top-level pain flags. Dangerous symptoms such as dizziness, fainting, chest pain, unusual shortness of breath, or palpitations should create a `SafetyEvent` even when `pain_flag=false`.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

If no profile exists but an active workout plan exists, the dashboard `current_goal` falls back to the saved workout-plan goal instead of showing an empty-goal state.

When an active workout plan exists, the dashboard next action should be backed by `WorkoutService.next_workout()`: show the next workout name, hide internal `load_signal` identifiers behind natural Hebrew labels, and include the same conservative/progression adjustment used by the workout execution loop.

The dashboard may show a secondary "תזונה היום" action based on today's meals and workouts. It should stay simple: if no meal is logged today, ask for one approximate meal log; if a workout was completed, prefer a protein-anchored meal log; if meals exist, encourage simple continued tracking rather than calorie precision.

The dashboard may also show a compact weekly review: summary sentence, consistency signal, completed/skipped workout counts, meals logged, and one action for the rest of the week. It must come from stored logs/meals and natural Hebrew labels, not internal metric keys.

Dashboard `current_streak` is a consecutive active-day count, not a workout-log count. Completed, partial, or modified workout logs and meal logs count as active dates; skipped workouts alone do not extend the streak.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

Nutrition estimate ranges and missed-workout counts should appear as separate dashboard metrics so a nutrition card does not describe workout adherence.

Dashboard counts should use natural Hebrew singular/plural wording, such as "יום אחד" and "אימון אחד שפוספס" instead of "1 ימים" or "1 אימונים".

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.

