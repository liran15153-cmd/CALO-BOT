from dataclasses import dataclass


@dataclass(frozen=True)
class CoachIntent:
    name: str
    payload_text: str


class CoachIntentService:
    def classify(self, text: str) -> CoachIntent:
        normalized = text.lower().strip()
        payload_text = self._strip_command_prefix(text)

        # Logging actions outrank guidance/summary: a message that records something
        # the user did should always be treated as a log, not as a question about it.
        if self._is_workout_log(normalized):
            return CoachIntent(name="workout_log", payload_text=payload_text)
        if self._is_meal_log(normalized):
            return CoachIntent(name="meal_log", payload_text=payload_text)
        if self._is_missed_workout_guidance(normalized):
            return CoachIntent(name="missed_workout_guidance", payload_text=payload_text)
        if self._is_weekly_summary(normalized):
            return CoachIntent(name="weekly_summary", payload_text=payload_text)
        if self._is_daily_summary(normalized):
            return CoachIntent(name="daily_summary", payload_text=payload_text)
        if self._is_memory_update_ack(normalized):
            return CoachIntent(name="memory_ack", payload_text=payload_text)
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
        if self._is_fitness_term_guidance(normalized):
            return CoachIntent(name="fitness_term_guidance", payload_text=payload_text)
        return CoachIntent(name="general_chat", payload_text=text)

    @staticmethod
    def _is_meal_log(text: str) -> bool:
        return any(
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
        )

    @staticmethod
    def _is_workout_plan(text: str) -> bool:
        has_plan_language = any(term in text for term in ["plan", "program", "routine", "תוכנית", "תכנית"])
        has_workout_language = any(
            term in text
            for term in ["workout", "training", "gym", "dumbbell", "אימון", "אימונים", "כושר", "כוח", "משקולות"]
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
    def _is_weekly_summary(text: str) -> bool:
        return any(
            phrase in text
            for phrase in ["weekly summary", "summarize my week", "סיכום שבועי", "סיכום השבוע", "סכמי לי את השבוע"]
        )

    @staticmethod
    def _is_daily_summary(text: str) -> bool:
        return any(phrase in text for phrase in ["daily summary", "today's summary", "סיכום יומי", "סיכום היום"])

    @staticmethod
    def _is_memory_update_ack(text: str) -> bool:
        starts_like_memory_update = any(
            text.startswith(prefix)
            for prefix in ["זכור", "תזכור", "תזכרי", "תזכרו", "remember", "keep in mind"]
        )
        has_preference_or_limitation = any(
            phrase in text
            for phrase in [
                "שונא",
                "אוהב",
                "מעדיף",
                "לא אוהב",
                "רגיש",
                "כאב",
                "ציוד",
                "preference",
                "prefer",
                "hate",
                "avoid",
            ]
        )
        return starts_like_memory_update and has_preference_or_limitation

    @staticmethod
    def _is_nutrition_guidance(text: str) -> bool:
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
    def _strip_command_prefix(text: str) -> str:
        stripped = text.strip()
        prefixes = ["log meal:", "log my meal:", "log workout:", "workout log:", "תעד ארוחה:", "תעד אימון:"]
        lowered = stripped.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return stripped[len(prefix) :].strip()
        return stripped
