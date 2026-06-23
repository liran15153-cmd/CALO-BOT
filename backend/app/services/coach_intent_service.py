from dataclasses import dataclass

from backend.app.services.text_normalization import normalize_user_text


@dataclass(frozen=True)
class CoachIntent:
    name: str
    payload_text: str


class CoachIntentService:
    def classify(self, text: str) -> CoachIntent:
        normalized = normalize_user_text(text)
        payload_text = self._strip_command_prefix(normalized)

        # Logging actions outrank guidance/summary: a message that records something
        # the user did should always be treated as a log, not as a question about it.
        if self._is_workout_log(normalized):
            return CoachIntent(name="workout_log", payload_text=payload_text)
        if self._is_meal_log(normalized):
            return CoachIntent(name="meal_log", payload_text=payload_text)
        if self._is_missed_workout_guidance(normalized):
            return CoachIntent(name="missed_workout_guidance", payload_text=payload_text)
        if self._is_supplement_safety_guidance(normalized):
            return CoachIntent(name="supplement_safety_guidance", payload_text=payload_text)
        if self._is_weekly_action_plan_guidance(normalized):
            return CoachIntent(name="weekly_action_plan_guidance", payload_text=payload_text)
        if self._is_low_energy_action_guidance(normalized):
            return CoachIntent(name="low_energy_action_guidance", payload_text=payload_text)
        if self._is_meal_image_guidance(normalized):
            return CoachIntent(name="meal_image_guidance", payload_text=payload_text)
        if self._is_nutrition_guidance(normalized):
            return CoachIntent(name="nutrition_guidance", payload_text=payload_text)
        if self._is_workout_plan(normalized):
            return CoachIntent(name="workout_plan", payload_text=payload_text)
        if self._is_knee_squat_substitution(normalized):
            return CoachIntent(name="knee_squat_substitution", payload_text=payload_text)
        if self._is_creatine_guidance(normalized):
            return CoachIntent(name="creatine_guidance", payload_text=payload_text)
        if self._is_equipment_substitution_guidance(normalized):
            return CoachIntent(name="equipment_substitution_guidance", payload_text=payload_text)
        if self._is_progress_metric(normalized):
            return CoachIntent(name="progress_metric", payload_text=payload_text)
        if self._is_motivation_recovery(normalized):
            return CoachIntent(name="motivation_recovery", payload_text=payload_text)
        if self._is_fitness_term_guidance(normalized):
            return CoachIntent(name="fitness_term_guidance", payload_text=payload_text)
        if self._is_non_fitness_request(normalized):
            return CoachIntent(name="non_fitness", payload_text=payload_text)
        return CoachIntent(name="general_chat", payload_text=text)

    # Common Israeli foods used to gate eating-slang and food-judgment questions, so a
    # bare slang verb ("טרפתי אימון", "חיסלתי סטים") is never mistaken for a meal log.
    _FOOD_CONTEXT_TERMS = (
        "ארוחה",
        "ארוחת",
        "אוכל",
        "פיצה",
        "המבורגר",
        "בורגר",
        "סושי",
        "שניצל",
        "אורז",
        "פסטה",
        "עוף",
        "בשר",
        "סלט",
        "חטיף",
        "שוקולד",
        "גלידה",
        "לחם",
        "כריך",
        "טוסט",
        "בורקס",
        "פלאפל",
        "שווארמה",
        "חומוס",
        "יוגורט",
        "ביצים",
        "ביצה",
        "פחמימות",
        "קלוריות",
        "חלבון",
    )

    def secondary_state_intent(self, text: str, primary_name: str) -> str | None:
        normalized = normalize_user_text(text)
        if primary_name != "workout_plan" and self._is_workout_plan(normalized):
            return "workout_plan"
        if primary_name != "meal_log" and self._is_meal_log(normalized):
            return "meal_log"
        if primary_name != "workout_log" and self._is_workout_log(normalized):
            return "workout_log"
        return None

    @staticmethod
    def _is_meal_log(text: str) -> bool:
        # A message that names food but is framed as a question ("אכלתי המבורגר, זה משמין?")
        # is a nutrition question, not a log. Let it fall through to nutrition_guidance.
        if CoachIntentService._is_food_judgment_question(text):
            return False
        if any(
            phrase in text
            for phrase in [
                "log meal",
                "log my meal",
                "i ate",
                "i had",
                "for breakfast",
                "for lunch",
                "for dinner",
                "אכלתי",
                "אכלתי ארוחת",
                "תיעדתי ארוחה",
                "תעד ארוחה",
                "לוג ארוחה",
                "ארוחת בוקר",
                "ארוחת צהריים",
                "ארוחת ערב",
            ]
        ):
            return True
        # Eating slang only counts as a log when there is real food context next to it.
        if any(verb in text for verb in ["זללתי", "טרפתי", "חיסלתי"]) and any(
            food in text for food in CoachIntentService._FOOD_CONTEXT_TERMS
        ):
            return True
        return False

    @staticmethod
    def _is_food_judgment_question(text: str) -> bool:
        ate_food = any(
            verb in text for verb in ["אכלתי", "i ate", "i had", "זללתי", "טרפתי", "חיסלתי"]
        )
        asks_judgment = "?" in text and any(
            marker in text
            for marker in [
                "דופק",
                "משמין",
                "ישמין",
                "מעלה",
                "יעלה",
                "בריא",
                "הורס",
                "מקלקל",
                "עושה לי",
                "זה בסדר",
                "חיטוב",
            ]
        )
        return ate_food and asks_judgment

    @staticmethod
    def _is_workout_plan(text: str) -> bool:
        has_plan_language = any(term in text for term in ["plan", "program", "routine", "תוכנית", "תכנית"])
        has_workout_language = any(
            term in text
            for term in [
                "workout",
                "training",
                "gym",
                "dumbbell",
                "leg",
                "legs",
                "pushup",
                "pushups",
                "run",
                "running",
                "squat",
                "אימון",
                "אימונים",
                "כושר",
                "כוח",
                "משקולות",
                "ריצה",
                "רגליים",
            ]
        )
        has_creation_language = any(
            phrase in text
            for phrase in [
                "create",
                "build",
                "give",
                "give me",
                "make",
                "generate",
                "תבנה",
                "תבני",
                "בנה",
                "בני",
                "תכין",
                "תכיני",
                "תכנן",
                "תכנני",
                "צור",
                "צרי",
                "תייצר",
                "תייצרי",
                "תן לי",
                "תני לי",
                "תעשה לי",
                "תעשי לי",
            ]
        )
        has_single_session_language = any(
            phrase in text
            for phrase in [
                "one workout",
                "one session",
                "single workout",
                "single session",
                "for today",
                "today",
                "right now",
                "short workout",
                "quick workout",
                "beginner workout",
                "starter workout",
                "20 minute",
                "20-minute",
                "אימון אחד",
                "אימון קצר",
                "היום",
            ]
        )
        has_training_week_language = any(
            phrase in text
            for phrase in [
                "workout week",
                "training week",
                "week of workouts",
                "שבוע אימונים",
                "שבוע של אימונים",
                "שבוע כוח",
                "שבוע כושר",
            ]
        )
        has_timeboxed_week_plan_language = (
            has_plan_language
            and any(phrase in text for phrase in ["שבוע הקרוב", "השבוע", "לשבוע"])
            and any(term in text for term in ["דקות", "דקה", "ביום"])
            and not any(term in text for term in ["תזונה", "ארוחה", "ארוחות", "אוכל", "תפריט"])
        )
        return has_creation_language and (
            (
                has_workout_language
                and (has_plan_language or has_single_session_language or has_training_week_language)
            )
            or has_timeboxed_week_plan_language
        )

    @staticmethod
    def _is_nutrition_guidance(text: str) -> bool:
        if CoachIntentService._is_food_judgment_question(text):
            return True
        asks_food_choice = any(phrase in text for phrase in ["מה לאכול", "מה כדאי לאכול", "סביב אימון", "לפני אימון", "אחרי אימון"])
        has_nutrition_goal = any(
            phrase in text
            for phrase in ["קלוריות", "אחוזי שומן", "ירידה בשומן", "חלבון", "תזונה", "אימון ערב", "לספור קלוריות"]
        )
        asks_image_accuracy = "תמונה" in text and any(phrase in text for phrase in ["מדויק", "להעריך", "קלוריות"])
        return (asks_food_choice and has_nutrition_goal) or asks_image_accuracy

    @staticmethod
    def _is_meal_image_guidance(text: str) -> bool:
        has_image = any(phrase in text for phrase in ["תמונה", "image", "photo"])
        asks_estimate = any(
            phrase in text
            for phrase in ["קלוריות", "calories", "מדויק", "exact", "להעריך", "estimate", "ניתוח", "analyze"]
        )
        return has_image and asks_estimate

    @staticmethod
    def _is_workout_log(text: str) -> bool:
        # Unambiguous logging statements: past tense or explicit command prefixes.
        explicit_phrases = (
            "log workout",
            "skipped workout",
            "תיעדתי אימון",
            "תעד אימון",
            "לוג אימון",
            "עשיתי אימון",
            "סיימתי אימון",
        )
        if any(phrase in text for phrase in explicit_phrases):
            return True
        if text.startswith("i did "):
            return True
        # Question framing pushes "סטים של" mentions to general chat / guidance routes:
        # "תסביר לי על סטים של 5 חזרות" must NOT be persisted as a workout log.
        has_question_framing = "?" in text or any(
            marker in text
            for marker in [
                "תסביר",
                "הסבר",
                "מה זה",
                "מה ה",
                "מה ההבדל",
                "כמה",
                "what is",
                "how do",
                "explain",
            ]
        )
        has_digit = any(token.isdigit() for token in text.split())
        if has_digit and not has_question_framing and ("sets of" in text or "סטים של" in text):
            return True
        # Gym slang for a completed session: a past-tense training verb plus a muscle group
        # or a "סטים" mention, but only when the message is not framed as a question.
        # Catches "עשיתי רגליים", "עשיתי רק 2 סטים חזה", "עשיתי chest day", "התאמנתי גב".
        if not has_question_framing:
            if "התאמנתי" in text or "סיימתי אימון" in text or "עשיתי אימון" in text:
                return True
            has_training_verb = any(verb in text for verb in ["עשיתי", "התאמנתי", "סיימתי", "i did ", "did "])
            has_gym_noun = any(
                noun in text
                for noun in [
                    "רגליים",
                    "חזה",
                    "גב",
                    "כתפיים",
                    "כתף",
                    "ידיים",
                    "בטן",
                    "ביצפס",
                    "טריצפס",
                    "סטים",
                    "chest",
                    "legs",
                    "back",
                    "shoulders",
                    "biceps",
                    "triceps",
                    "leg day",
                ]
            )
            if has_training_verb and has_gym_noun:
                return True
        # "פספסתי אימון" alone is ambiguous. Treat it as a log only when the user
        # explicitly asks to record it (e.g. "פספסתי אימון אתמול, איך לתעד?").
        # Otherwise it falls through to missed_workout_guidance.
        if "פספסתי אימון" in text and any(
            verb in text for verb in ["לתעד", "תעד אותו", "תעד את", "לוג", "log it"]
        ):
            return True
        return False

    @staticmethod
    def _is_creatine_guidance(text: str) -> bool:
        if not ("creatine" in text or "קריאטין" in text or "קראטין" in text):
            return False
        # Bare mentions ("אני שונא קריאטין") fall through to general chat.
        # The intent fires only when the user asks a question about creatine.
        return any(
            marker in text
            for marker in [
                "?",
                "בטוח",
                "מסוכן",
                "כמה",
                "מינון",
                "לוותר",
                "כדאי",
                "מתי",
                "איך",
                "מה זה",
                "צריך",
                "תסביר",
                "safe",
                "dangerous",
                "should",
                "dose",
                "dosage",
                "when",
                "how much",
                "necessary",
            ]
        )

    @staticmethod
    def _is_supplement_safety_guidance(text: str) -> bool:
        has_stimulant_or_supplement = any(
            term in text
            for term in [
                "pre-workout",
                "pre workout",
                "פרה-וורקאאוט",
                "פרי וורקאאוט",
                "קפאין",
                "caffeine",
                "yohimbine",
                "יוהימבין",
                "fat burner",
                "fat burners",
                "שורף שומן",
                "שורפי שומן",
                "ממריץ",
                "ממריצים",
                "תוסף",
                "תוספים",
            ]
        )
        asks_safety_or_timing = any(
            phrase in text
            for phrase in [
                "בטוח",
                "מסוכן",
                "לוותר",
                "כדאי",
                "רעיון טוב",
                "לפני אימון",
                "אימון ערב",
                "safe",
                "dangerous",
                "skip",
                "should",
            ]
        )
        return has_stimulant_or_supplement and asks_safety_or_timing

    @staticmethod
    def _is_weekly_action_plan_guidance(text: str) -> bool:
        asks_action_plan = any(
            phrase in text
            for phrase in [
                "action plan",
                "תוכנית שבוע",
                "תכנית שבוע",
                "תוכנית קצרה לשבוע",
                "תכנית קצרה לשבוע",
            ]
        )
        has_strength_and_walking = any(phrase in text for phrase in ["אימוני כוח", "אימון כוח"]) and any(
            phrase in text for phrase in ["הליכה", "הליכות", "צעדים"]
        )
        return asks_action_plan and has_strength_and_walking

    @staticmethod
    def _is_low_energy_action_guidance(text: str) -> bool:
        has_low_energy = any(
            phrase in text
            for phrase in [
                "אין לי כוח",
                "אין אנרגיה",
                "עייף",
                "עייפה",
                "יום עמוס",
                "low energy",
                "tired",
                "exhausted",
            ]
        )
        asks_small_action = any(
            phrase in text
            for phrase in [
                "פעולה אחת",
                "פעולה קטנה",
                "משהו קטן",
                "מינימום",
                "מה לעשות",
                "תן לי",
                "תני לי",
                "one action",
                "minimum action",
                "small action",
            ]
        )
        has_consistency_framing = any(phrase in text for phrase in ["רצף", "לשבור רצף", "consistency", "streak"])
        return asks_small_action and (has_low_energy or has_consistency_framing)

    @staticmethod
    def _is_knee_squat_substitution(text: str) -> bool:
        has_squat = "squat" in text or "סקוואט" in text
        has_knee = "knee" in text or "ברך" in text
        asks_for_substitution = any(
            phrase in text
            for phrase in ["replace", "alternative", "substitute", "להחליף", "תחליף", "חלופה", "במקום"]
        )
        return has_squat and has_knee and asks_for_substitution

    @staticmethod
    def _is_equipment_substitution_guidance(text: str) -> bool:
        has_substitution = any(
            phrase in text
            for phrase in ["replace", "alternative", "substitute", "instead of", "במקום", "להחליף", "תחליף", "חלופה", "אין לי"]
        )
        has_equipment_or_exercise = any(
            term in text
            for term in [
                "גומייה",
                "גומיות",
                "משקולת",
                "משקולות",
                "מכונה",
                "ספסל",
                "חתירה",
                "לחיצה",
                "תרגיל גב",
                "band",
                "dumbbell",
                "machine",
                "bench",
                "row",
            ]
        )
        return has_substitution and has_equipment_or_exercise

    @staticmethod
    def _is_missed_workout_guidance(text: str) -> bool:
        has_missed = any(phrase in text for phrase in ["פספסתי", "החמצתי", "missed workout", "skipped workout"])
        # Explicit guidance verbs only. A bare "?" used to qualify here, which let
        # logging questions like "פספסתי אימון אתמול, איך לתעד?" leak into guidance.
        asks_for_guidance = any(
            phrase in text
            for phrase in ["לחזור", "מה לעשות", "איך", "דרך", "תן לי", "תני לי", "להמשיך", "בלי להרגיש"]
        )
        return has_missed and asks_for_guidance

    @staticmethod
    def _is_fitness_term_guidance(text: str) -> bool:
        term_markers = [
            "rpe",
            "rir",
            "doms",
            "zone 2",
            "זון 2",
            "deload",
            "progression",
            "progressive overload",
            "full-body",
            "full body",
            "push/pull/legs",
            "ppl",
            "warmup",
            "warm-up",
            "cooldown",
            "cool-down",
            "mobility",
            "חימום",
            "קירור",
            "מתיחות",
            "מוביליטי",
            "היפרטרופיה",
            "חזרות ברזרבה",
            "סטים קשים",
            "דילואד",
            "פרוגרסיה",
            "התקדמות",
            "להתקדם",
            "שרירים תפוסים",
            "כאבי שרירים",
        ]
        if not any(marker in text for marker in term_markers):
            return False

        guidance_markers = ["מה", "איך", "תסביר", "הסבר", "עדיף", "צריך", "?", "what", "how", "explain", "should"]
        return any(marker in text for marker in guidance_markers)

    @staticmethod
    def _is_motivation_recovery(text: str) -> bool:
        has_demotivation = any(
            phrase in text
            for phrase in [
                "אין מוטיבציה",
                "אין לי מוטיבציה",
                "אין חשק",
                "אין לי חשק",
                "בא לי לוותר",
                "מתחשק לי לוותר",
                "מאסתי",
                "נמאס לי",
                "אני מתוסכל",
                "אני מתוסכלת",
                "לא בא לי",
                "no motivation",
                "want to quit",
                "feel like giving up",
            ]
        )
        asks_rest = any(
            phrase in text
            for phrase in [
                "כמה מנוחה",
                "כמה ימי מנוחה",
                "כמה זמן מנוחה",
                "ימי מנוחה",
                "יום מנוחה",
                "מנוחה בין אימונים",
                "rest days",
                "rest between",
            ]
        )
        return has_demotivation or asks_rest

    @staticmethod
    def _is_progress_metric(text: str) -> bool:
        mentions_metric = any(
            phrase in text
            for phrase in [
                "המשקל תקוע",
                "תקוע במשקל",
                "תקועה במשקל",
                "המשקל לא זז",
                "המשקל עומד",
                "עליתי במשקל",
                "ירדתי במשקל",
                "עליתי קילו",
                "אחוזי שומן",
                "אחוז שומן",
                "שריר או שומן",
                "מסת שריר",
                "לא רואה תוצאות",
                "אין תוצאות",
                "stuck at weight",
                "weight plateau",
                "body fat",
            ]
        )
        weight_with_number = ("קילו" in text or "ק\"ג" in text or "kg" in text) and any(
            token.isdigit() for token in text.split()
        ) and any(verb in text for verb in ["עליתי", "ירדתי", "עלתה", "ירד", "תקוע", "gained", "lost"])
        return mentions_metric or weight_with_number

    @staticmethod
    def _is_non_fitness_request(text: str) -> bool:
        return any(
            phrase in text
            for phrase in [
                "resignation email",
                "write an email",
                "email to my manager",
                "cover letter",
                "קורות חיים",
                "מייל למנהל",
                "לכתוב מייל",
                "מכתב התפטרות",
            ]
        )

    @staticmethod
    def _strip_command_prefix(text: str) -> str:
        stripped = text.strip()
        prefixes = ["log meal:", "log my meal:", "log workout:", "workout log:", "תעד ארוחה:", "תעד אימון:"]
        lowered = stripped.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return stripped[len(prefix) :].strip()
        return stripped
