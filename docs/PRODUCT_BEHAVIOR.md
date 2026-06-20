# Product Behavior

## Coach Style

The coach is practical, short by default, and action-oriented. It should ask follow-up questions when data is missing and avoid long essays unless the user requests detail.

All user-visible product copy and coach responses are Hebrew-first. They should be mostly natural Hebrew, while short English fitness/nutrition terms, exercise names, headings, product names, model names, URLs, and technical identifiers may remain in English when that is clearer or more natural.

If a configured chat provider returns a response with no Hebrew text, the coach does not display that response and returns a Hebrew retry message instead.

If a configured chat provider returns text that is effectively an English sentence or paragraph with only a little Hebrew, the coach does not display that response. Hebrew responses with short English terms such as recovery, mobility, workout, protein timing, RPE, RIR, DOMS, HIIT, or Zone 2 are allowed.

Frontend surfaces map technical provider statuses such as `not_configured`, `provider_error`, `budget_exceeded`, `local_tool`, and `safety_override` to Hebrew labels. The API values stay stable English identifiers.

Provider-backed chat receives a compact `coaching_knowledge` context with source-backed general fitness rules and trainer decision domains: assessment, FITT programming, movement patterns, progressions/regressions, recovery, adherence, nutrition uncertainty, and referral boundaries. It must not claim to be certified or replace a qualified professional.

All chat intents receive compact adherence coaching context: ask one open question when needed, identify the concrete barrier, collaborate on one small action, use logs as feedback, and offer a fallback plan after missed workouts. The full behavior-change protocol table stays internal so prompts do not become long manuals.

General-chat contexts also include a compact adherence micro-protocol. The coach should use short OARS-style support, identify one barrier, build an if-then or minimum viable action, and offer two safe choices when useful instead of issuing commands.

General-chat contexts include compact daily activity and NEAT guidance. The coach should start from the user's step baseline, increase steps gradually, suggest short movement breaks for long sitting, use natural Hebrew such as "הפסקות תנועה קצרות", and treat calorie burn from steps or wearables as a rough range rather than a precise number.

General-chat contexts include compact environmental training guidance. The coach should adapt outdoor training for heat, AQI/air quality, cold, wind chill, smoke, and humidity by shortening, lowering intensity, moving the session indoors, or rescheduling. Workout contexts carry a shorter cue inside cardio programming so plan/log prompts stay under budget. This is coaching knowledge only; dangerous symptoms still use the existing safety/referral boundaries and no new runtime blocker is added.

General-chat contexts include compact common-fitness-myth guidance. The coach should answer questions about spot reduction, DOMS, sweat, fasted cardio, and fear of strength training causing unwanted bulk in natural Hebrew, correct the misconception without mocking the user, and redirect to one practical action. This is coaching knowledge only; it does not create a new blocker or certification claim.

General-chat and meal contexts include compact body-composition strategy guidance. The coach should explain מאזן קלורי, גירעון, תחזוקה, ריקומפ, חיטוב, מסה, מגמת משקל, and plateau review in natural Hebrew, while avoiding exact calorie certainty, medical diet claims, or treating one weigh-in as proof.

All provider contexts include compact Hebrew coaching-language guidance. The coach should write natural Hebrew, keep useful fitness terms such as RPE, RIR, DOMS, HIIT and Zone 2 when direct translation would sound worse, explain those terms briefly when needed, and avoid shame, punishment, or mandatory language after missed actions.

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

General-chat and meal contexts include compact supplement education. The coach may explain creatine monohydrate, caffeine/pre-workout, protein powder, beta-alanine and electrolytes as optional tools, while pushing back on fat burners, testosterone boosters, hidden stimulants and product claims with weak evidence or higher risk.

Provider-backed coach replies should be plain text, not raw Markdown. The prompt asks for no headings, bold markers, tables, or horizontal rules, because the current chat UI renders message text directly. The backend also strips common Markdown markers before storing/displaying provider chat text.

## AI Honesty

If no AI provider is configured, the product must not pretend to generate AI answers. It should explain that provider configuration is missing while keeping deterministic screens usable.

Configured AI calls use the Anthropic Claude provider adapter with `claude-haiku-4-5` by default. No API key is ever returned from backend settings responses or expected in the frontend.

The coach engine handles obvious action requests locally before generic chat: creating workout plans, logging workouts, logging meals, returning daily/weekly summaries, answering common creatine guidance, and giving knee/squat substitution guidance save or return deterministic product behavior with `provider_status: local_tool`.

Opening the chat screen should not create empty chat sessions. The backend creates a session when the first real message is sent, while the explicit "new chat" action can still create a fresh session.

The local workout-plan tool creates saved structured plan objects, not chat-only text. Multi-week plans are capped at 1-4 weeks and can become the current plan. Single-session plans create one saved workout for the user's current state, use `is_current=false`, and do not replace the active multi-week plan.

The deterministic workout builder uses profile, request fields, prompt inference, equipment, limitations, preferred days, session length, and recent workout-log status. It chooses full-body for most 1-3 day plans, upper/lower for many 4-day intermediate plans, trims exercise count by available time, and includes movement patterns, sets, reps/time, rest, alternatives, progression, regression, safety notes, `decision_inputs`, and URL-bearing `source_refs`.

Workout logging parses common exercise-first phrasing such as "I did goblet squat 3 sets 8,8,7 with 20kg" and Hebrew equivalents, stores parsed exercise results, and extracts RPE when present so adaptation logic can use it. Negated pain phrases such as "בלי כאב", "ללא כאב", and "no pain" should not trigger safety override or set `pain_flag`.

Weekly summaries are one structured row per user/week. Re-reading the weekly summary updates the current week record instead of appending duplicate rows.

One-off workouts use readiness and recent logs. Green days may keep the planned structure and one small progression. Yellow days, such as high recent RPE, low sleep, soreness, or adherence risk, reduce volume or intensity and avoid failure. Red-flag pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath stay in safety/referral behavior rather than normal progression.

Configured provider-backed chat and image analysis check `DAILY_AI_TOKEN_LIMIT` before making an external call. When the daily budget is spent, the app saves the request context where appropriate, returns `provider_status: budget_exceeded`, and does not call the AI provider.

## Nutrition Accuracy

Photo-based and text-based nutrition estimates are approximate. The app must use calorie and macro ranges, confidence levels, and uncertainty notes.

Manual meal parsing is deliberately rough in v1. It should produce editable ranges, not authoritative nutrition database claims.

Manual meal parsing should aggregate recognized simple items instead of stopping at the first match. For example, yogurt plus banana plus protein shake is saved as separate estimated items and a summed calorie/protein range.

Nutrition coaching should stay practical: use ranges, confidence, one next habit, and stored context. Protein, carbohydrate, hydration, and body-composition guidance should be framed as general coaching support, not clinical nutrition treatment.

Configured image analysis normalizes provider JSON into persisted meal ranges and detected meal items. If the provider is not configured, image analysis must stay unavailable and must not fake detected foods.

If configured image analysis returns user-facing text with no Hebrew or dominant-English copy, the app replaces that visible text with conservative Hebrew placeholders instead of displaying English copy. Hebrew analysis text may keep short English food, fitness, or nutrition terms when the sentence remains mostly Hebrew.

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

Extreme dieting safety is checked before provider calls. Numeric targets such as very low daily calories at or below 1,000 calories, or rapid monthly weight-loss targets such as 6 kg or more in a month, should return a conservative safety response and record a `SafetyEvent`.

Common non-diagnostic movement substitutions can be handled locally when the user asks how to replace a squat because of knee sensitivity. The response should avoid diagnosis, avoid pushing through pain, offer conservative alternatives such as box squat, Romanian deadlift, or hip bridge, and recommend professional help when pain is sharp, worsening, or persistent.

## Dashboard

The dashboard is a product surface, not a landing page. It should show persisted facts: profile goal, current workout plan, completed workouts, meals logged, nutrition estimate ranges, coach memories, streak, missed workouts, and one practical next action.

When no nutrition estimate exists, the dashboard should show an empty estimate state instead of rendering `null-null` or implying precision.

## Data Controls

Settings exposes provider status, usage totals, remaining daily token budget, JSON export, and local reset. It must not expose secrets.
