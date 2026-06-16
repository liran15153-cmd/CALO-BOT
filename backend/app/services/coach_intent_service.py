from dataclasses import dataclass


@dataclass(frozen=True)
class CoachIntent:
    name: str
    payload_text: str


class CoachIntentService:
    def classify(self, text: str) -> CoachIntent:
        normalized = text.lower().strip()
        payload_text = self._strip_command_prefix(text)

        if self._is_meal_log(normalized):
            return CoachIntent(name="meal_log", payload_text=payload_text)
        if self._is_workout_plan(normalized):
            return CoachIntent(name="workout_plan", payload_text=payload_text)
        if self._is_workout_log(normalized):
            return CoachIntent(name="workout_log", payload_text=payload_text)
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
            ]
        )

    @staticmethod
    def _is_workout_plan(text: str) -> bool:
        has_plan_language = "plan" in text or "program" in text or "routine" in text
        has_workout_language = "workout" in text or "training" in text or "gym" in text or "dumbbell" in text
        has_creation_language = any(phrase in text for phrase in ["create", "build", "make", "generate"])
        return has_plan_language and has_workout_language and has_creation_language

    @staticmethod
    def _is_workout_log(text: str) -> bool:
        return (
            "log workout" in text
            or "skipped workout" in text
            or text.startswith("i did ")
            or ("sets of" in text and any(token.isdigit() for token in text.split()))
        )

    @staticmethod
    def _strip_command_prefix(text: str) -> str:
        stripped = text.strip()
        prefixes = ["log meal:", "log my meal:", "log workout:", "workout log:"]
        lowered = stripped.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return stripped[len(prefix) :].strip()
        return stripped
