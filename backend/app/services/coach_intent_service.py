from dataclasses import dataclass


@dataclass(frozen=True)
class CoachIntent:
    name: str
    payload_text: str


class CoachIntentService:
    def classify(self, text: str) -> CoachIntent:
        normalized = text.lower().strip()
        payload_text = self._strip_command_prefix(text)

        if self._is_weekly_summary(normalized):
            return CoachIntent(name="weekly_summary", payload_text=payload_text)
        if self._is_daily_summary(normalized):
            return CoachIntent(name="daily_summary", payload_text=payload_text)
        if self._is_meal_log(normalized):
            return CoachIntent(name="meal_log", payload_text=payload_text)
        if self._is_workout_plan(normalized):
            return CoachIntent(name="workout_plan", payload_text=payload_text)
        if self._is_workout_log(normalized):
            return CoachIntent(name="workout_log", payload_text=payload_text)
        if self._is_knee_squat_substitution(normalized):
            return CoachIntent(name="knee_squat_substitution", payload_text=payload_text)
        if self._is_creatine_guidance(normalized):
            return CoachIntent(name="creatine_guidance", payload_text=payload_text)
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
            term in text for term in ["workout", "training", "gym", "dumbbell", "אימון", "אימונים", "כושר", "משקולות"]
        )
        has_creation_language = any(
            phrase in text
            for phrase in [
                "create",
                "build",
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
                "20 minute",
                "20-minute",
                "אימון אחד",
                "היום",
            ]
        )
        return has_workout_language and has_creation_language and (has_plan_language or has_single_session_language)

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
    def _is_workout_log(text: str) -> bool:
        return (
            "log workout" in text
            or "skipped workout" in text
            or text.startswith("i did ")
            or ("sets of" in text and any(token.isdigit() for token in text.split()))
            or "תיעדתי אימון" in text
            or "תעד אימון" in text
            or "לוג אימון" in text
            or "עשיתי אימון" in text
            or "פספסתי אימון" in text
            or ("סטים" in text and "של" in text)
        )

    @staticmethod
    def _is_creatine_guidance(text: str) -> bool:
        return "creatine" in text or "קריאטין" in text or "קראטין" in text

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
    def _strip_command_prefix(text: str) -> str:
        stripped = text.strip()
        prefixes = ["log meal:", "log my meal:", "log workout:", "workout log:", "תעד ארוחה:", "תעד אימון:"]
        lowered = stripped.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return stripped[len(prefix) :].strip()
        return stripped
