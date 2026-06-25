from dataclasses import dataclass
from enum import IntEnum

from backend.app.services.text_normalization import normalize_user_text


@dataclass(frozen=True)
class CoachIntent:
    name: str
    payload_text: str


class IntentPriority(IntEnum):
    WORKOUT_LOG = 100
    MEAL_LOG = 99
    MISSED_WORKOUT_GUIDANCE = 98
    SUPPLEMENT_SAFETY_GUIDANCE = 97
    WEEKLY_ACTION_PLAN_GUIDANCE = 96
    LOW_ENERGY_ACTION_GUIDANCE = 95
    MEAL_IMAGE_GUIDANCE = 94
    NUTRITION_GUIDANCE = 93
    FULL_WORKOUT_PLAN_REPLACEMENT = 92
    WORKOUT_PLAN_CHANGE_SUMMARY = 91
    NEXT_WORKOUT_SUMMARY = 90
    CURRENT_WORKOUT_PLAN_SUMMARY = 89
    WORKOUT_PLAN_EDIT = 88
    WORKOUT_PLAN = 87
    RETURN_AFTER_BREAK_GUIDANCE = 86
    KNEE_SQUAT_SUBSTITUTION = 85
    CREATINE_GUIDANCE = 84
    EQUIPMENT_SUBSTITUTION_GUIDANCE = 83
    PROGRESS_METRIC = 82
    MOTIVATION_RECOVERY = 81
    FITNESS_TERM_GUIDANCE = 80
    NON_FITNESS = 79
    GENERAL_CHAT = 0


@dataclass(frozen=True)
class IntentRule:
    name: str
    predicate_name: str
    priority: IntentPriority
    intent_name: str | None = None


def _has_workout_plan_question_framing(text: str) -> bool:
    return "?" in text or any(
        marker in text
        for marker in [
            "מה ההבדל",
            "מה זה",
            "מה אומר",
            "איך",
            "כמה",
            "למה",
            "האם",
            "תסביר",
            "הסבר",
            "what is",
            "how many",
            "how long",
            "how to",
            "difference between",
            "explain",
        ]
    )


class CoachIntentService:
    _INTENT_RULES = (
        IntentRule("workout_log", "_is_workout_log", IntentPriority.WORKOUT_LOG),
        IntentRule("meal_log", "_is_meal_log", IntentPriority.MEAL_LOG),
        IntentRule("missed_workout_guidance", "_is_missed_workout_guidance", IntentPriority.MISSED_WORKOUT_GUIDANCE),
        IntentRule(
            "supplement_safety_guidance",
            "_is_supplement_safety_guidance",
            IntentPriority.SUPPLEMENT_SAFETY_GUIDANCE,
        ),
        IntentRule(
            "weekly_action_plan_guidance",
            "_is_weekly_action_plan_guidance",
            IntentPriority.WEEKLY_ACTION_PLAN_GUIDANCE,
        ),
        IntentRule("low_energy_action_guidance", "_is_low_energy_action_guidance", IntentPriority.LOW_ENERGY_ACTION_GUIDANCE),
        IntentRule("meal_image_guidance", "_is_meal_image_guidance", IntentPriority.MEAL_IMAGE_GUIDANCE),
        IntentRule("nutrition_guidance", "_is_nutrition_guidance", IntentPriority.NUTRITION_GUIDANCE),
        IntentRule(
            "full_workout_plan_replacement",
            "_is_full_workout_plan_replacement",
            IntentPriority.FULL_WORKOUT_PLAN_REPLACEMENT,
            intent_name="workout_plan",
        ),
        IntentRule(
            "workout_plan_change_summary",
            "_is_workout_plan_change_summary",
            IntentPriority.WORKOUT_PLAN_CHANGE_SUMMARY,
        ),
        IntentRule("next_workout_summary", "_is_next_workout_summary", IntentPriority.NEXT_WORKOUT_SUMMARY),
        IntentRule(
            "current_workout_plan_summary",
            "_is_current_workout_plan_summary",
            IntentPriority.CURRENT_WORKOUT_PLAN_SUMMARY,
        ),
        IntentRule("workout_plan_edit", "_is_workout_plan_edit", IntentPriority.WORKOUT_PLAN_EDIT),
        IntentRule("workout_plan", "_is_workout_plan", IntentPriority.WORKOUT_PLAN),
        IntentRule("return_after_break_guidance", "_is_return_after_break_guidance", IntentPriority.RETURN_AFTER_BREAK_GUIDANCE),
        IntentRule("knee_squat_substitution", "_is_knee_squat_substitution", IntentPriority.KNEE_SQUAT_SUBSTITUTION),
        IntentRule("creatine_guidance", "_is_creatine_guidance", IntentPriority.CREATINE_GUIDANCE),
        IntentRule(
            "equipment_substitution_guidance",
            "_is_equipment_substitution_guidance",
            IntentPriority.EQUIPMENT_SUBSTITUTION_GUIDANCE,
        ),
        IntentRule("progress_metric", "_is_progress_metric", IntentPriority.PROGRESS_METRIC),
        IntentRule("motivation_recovery", "_is_motivation_recovery", IntentPriority.MOTIVATION_RECOVERY),
        IntentRule("fitness_term_guidance", "_is_fitness_term_guidance", IntentPriority.FITNESS_TERM_GUIDANCE),
        IntentRule("non_fitness", "_is_non_fitness_request", IntentPriority.NON_FITNESS),
    )

    def classify(self, text: str) -> CoachIntent:
        intent, _, _ = self.classify_with_trace(text)
        return intent

    def classify_with_trace(self, text: str) -> tuple[CoachIntent, str, str]:
        normalized = normalize_user_text(text)
        payload_text = self._strip_command_prefix(normalized)

        for rule in self._INTENT_RULES:
            if getattr(self, rule.predicate_name)(normalized):
                intent_name = rule.intent_name or rule.name
                return CoachIntent(name=intent_name, payload_text=payload_text), rule.name, "high"
        return CoachIntent(name="general_chat", payload_text=text), "general_chat", "low"

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
        "food",
        "meal",
        "breakfast",
        "lunch",
        "dinner",
        "rice",
        "chicken",
        "salad",
        "tahini",
        "pizza",
        "burger",
        "protein",
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
        if any(verb in text for verb in ["i ate", "i had"]) and any(
            food in text for food in CoachIntentService._FOOD_CONTEXT_TERMS
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
                "סשן",
                "חזרה אחרי",
                "אחרי הפסקה",
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
                "צור לי",
                "צרי לי",
                "תייצר",
                "תייצרי",
                "תן לי",
                "תני לי",
                "תעשה לי",
                "תעשי לי",
                "אני רוצה תוכנית",
                "אני רוצה תכנית",
                "אני צריך תוכנית",
                "אני צריכה תוכנית",
                "בא לי תוכנית",
                "בא לי תכנית",
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
                "אימון יחיד",
                "אימון בודד",
                "אימון חד פעמי",
                "אימון חד-פעמי",
                "אימון קצר",
                "אימון זריז",
                "מיני אימון",
                "סשן אחד",
                "סשן קצר",
                "עכשיו",
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
        has_training_horizon_language = any(
            phrase in text
            for phrase in [
                "weekly plan",
                "two week plan",
                "2 week plan",
                "monthly plan",
                "four week plan",
                "4 week plan",
                "שבועית",
                "שבוע הבא",
                "שבועיים",
                "לשבועיים",
                "שבועיים הקרובים",
                "השבועיים הקרובים",
                "חודשית",
                "לחודש",
                "חודש הקרוב",
                "לחודש הקרוב",
                "4 שבועות",
                "ארבעה שבועות",
            ]
        )
        has_body_composition_plan_language = any(
            phrase in text for phrase in ["fat loss", "cutting", "חיטוב", "להתחטב", "ירידה בשומן"]
        )
        has_nutrition_language = any(term in text for term in ["תזונה", "ארוחה", "ארוחות", "אוכל", "תפריט", "nutrition", "meal"])
        has_question_framing = "?" in text or any(
            marker in text
            for marker in [
                "מה ההבדל",
                "מה עדיף",
                "איך",
                "כמה",
                "למה",
                "האם",
                "תסביר",
                "הסבר",
                "what is",
                "how many",
                "how long",
                "difference between",
            ]
        )
        has_explanatory_question_framing = any(
            marker in text
            for marker in [
                "מה ההבדל",
                "תסביר",
                "הסבר",
                "איך לבנות",
                "איך בונים",
                "what is",
                "how to",
                "how do i",
                "difference between",
            ]
        )
        has_timeboxed_week_plan_language = (
            has_plan_language
            and any(phrase in text for phrase in ["שבוע הקרוב", "השבוע", "לשבוע"])
            and any(term in text for term in ["דקות", "דקה", "ביום"])
            and not has_nutrition_language
        )
        has_past_session_language = any(
            phrase in text
            for phrase in [
                "היה קשה",
                "היה קל",
                "היה לי",
                "הייתה",
                "עשיתי",
                "סיימתי",
                "תיעדתי",
                "בוצע",
                "completed",
                "was hard",
                "was easy",
            ]
        )
        has_bare_single_session_request = (
            has_workout_language
            and has_single_session_language
            and not has_nutrition_language
            and not has_question_framing
            and not has_past_session_language
            and any(
                phrase in text
                for phrase in [
                    "אימון להיום",
                    "אימון עכשיו",
                    "אימון קצר",
                    "אימון זריז",
                    "אימון יחיד",
                    "אימון אחד",
                    "סשן להיום",
                    "סשן עכשיו",
                    "workout for today",
                    "today workout",
                    "today's workout",
                    "short workout",
                ]
            )
        )
        has_horizon_plan_language = (
            has_plan_language
            and has_training_horizon_language
            and not has_nutrition_language
        )
        explicit_plan_request = has_creation_language and (
            (
                has_workout_language
                and (has_plan_language or has_single_session_language or has_training_week_language)
            )
            or has_timeboxed_week_plan_language
            or has_horizon_plan_language
            or (has_plan_language and has_body_composition_plan_language and not has_nutrition_language)
        ) and not has_explanatory_question_framing
        minimal_plan_request = (
            has_creation_language
            and has_plan_language
            and not has_nutrition_language
            and not has_question_framing
        )
        bare_horizon_plan_request = has_horizon_plan_language and not has_question_framing
        return explicit_plan_request or minimal_plan_request or bare_horizon_plan_request or has_bare_single_session_request

    @staticmethod
    def _is_full_workout_plan_replacement(text: str) -> bool:
        if _has_workout_plan_question_framing(text):
            return False
        has_plan_reference = any(
            phrase in text
            for phrase in [
                "my plan",
                "current plan",
                "the plan",
                "בתוכנית",
                "בתכנית",
                "התוכנית",
                "התכנית",
                "תוכנית שלי",
                "תכנית שלי",
            ]
        )
        if not has_plan_reference:
            return False
        if any(phrase in text for phrase in ["רק את זה", "רק מה שצריך", "רק את מה שצריך"]):
            return False

        direct_replacement = any(
            phrase in text
            for phrase in [
                "כל התוכנית",
                "כל התכנית",
                "התוכנית כולה",
                "התכנית כולה",
                "תוכנית חדשה",
                "תכנית חדשה",
                "במקום התוכנית",
                "במקום התכנית",
                "להחליף את התוכנית",
                "להחליף את התכנית",
                "תחליף לי את התוכנית",
                "תחליפי לי את התוכנית",
                "תחליף לי את התכנית",
                "תחליפי לי את התכנית",
                "replace my plan",
                "replace the plan",
                "new plan instead",
                "new program instead",
            ]
        )
        structural_rewrite = any(
            phrase in text
            for phrase in [
                "תעדכן לי את התוכנית לתוכנית",
                "תעדכני לי את התוכנית לתוכנית",
                "תעדכן לי את התכנית לתכנית",
                "תשנה לי את התוכנית לתוכנית",
                "תשני לי את התוכנית לתוכנית",
                "update my plan to",
                "change my plan to",
            ]
        ) and any(
            marker in text
            for marker in [
                "יום",
                "ימים",
                "שבוע",
                "שבועיים",
                "חודש",
                "מכון",
                "בית",
                "משקולות",
                "חיטוב",
                "כוח",
                "שריר",
                "gym",
                "home",
                "days",
                "week",
                "month",
                "strength",
                "muscle",
            ]
        )
        return direct_replacement or structural_rewrite

    @staticmethod
    def _is_workout_plan_edit(text: str) -> bool:
        has_plan_reference = any(
            phrase in text
            for phrase in [
                "my plan",
                "current plan",
                "the plan",
                "בתוכנית",
                "בתכנית",
                "התוכנית",
                "התכנית",
                "תוכנית שלי",
                "תכנית שלי",
            ]
        )
        has_edit_language = any(
            phrase in text
            for phrase in [
                "update",
                "change",
                "replace",
                "swap",
                "reduce volume",
                "less volume",
                "no bench",
                "without bench",
                "תעדכן",
                "תעדכני",
                "תשנה",
                "תשני",
                "שנה",
                "שני",
                "תחליף",
                "תחליפי",
                "להחליף",
                "תוריד",
                "תורידי",
                "להוריד נפח",
                "פחות נפח",
                "פחות סטים",
                "אין לי",
                "בלי ספסל",
                "ללא ספסל",
                "קשה מדי",
                "קשים מדי",
                "קשות מדי",
                "too hard",
                "too difficult",
            ]
        )
        return has_plan_reference and has_edit_language

    @staticmethod
    def _is_workout_plan_change_summary(text: str) -> bool:
        has_plan_reference = any(
            phrase in text
            for phrase in [
                "my plan",
                "the plan",
                "current plan",
                "בתוכנית",
                "בתכנית",
                "התוכנית",
                "התכנית",
                "תוכנית שלי",
                "תכנית שלי",
            ]
        )
        asks_change_summary = any(
            phrase in text
            for phrase in [
                "what changed",
                "what did you change",
                "what did you update",
                "what was changed",
                "what changed in my plan",
                "מה השתנה",
                "מה שינית",
                "מה עדכנת",
                "מה החלפת",
                "איזה שינוי",
                "איזה עדכון",
            ]
        )
        return has_plan_reference and asks_change_summary

    @staticmethod
    def _is_current_workout_plan_summary(text: str) -> bool:
        has_plan_reference = any(
            phrase in text
            for phrase in [
                "my plan",
                "current plan",
                "active plan",
                "the plan",
                "התוכנית שלי",
                "התכנית שלי",
                "התוכנית הפעילה",
                "התכנית הפעילה",
                "התוכנית",
                "התכנית",
            ]
        )
        asks_to_view = any(
            phrase in text
            for phrase in [
                "show me",
                "show my",
                "show the",
                "open my",
                "view my",
                "what is my plan",
                "what's my plan",
                "what is the plan",
                "מה התוכנית",
                "מה התכנית",
                "תראה לי",
                "תציג לי",
                "הצג לי",
                "פתח לי",
            ]
        )
        return has_plan_reference and asks_to_view

    @staticmethod
    def _is_next_workout_summary(text: str) -> bool:
        has_next_workout_reference = any(
            phrase in text
            for phrase in [
                "next workout",
                "current workout",
                "upcoming workout",
                "workout next",
                "האימון הבא",
                "אימון הבא",
                "האימון הקרוב",
                "אימון קרוב",
                "האימון של היום",
                "אימון של היום",
            ]
        )
        asks_to_open_or_start = any(
            phrase in text
            for phrase in [
                "show me",
                "show the",
                "open",
                "start",
                "view",
                "what is",
                "what's",
                "which workout",
                "פתח",
                "תפתח",
                "תפתחי",
                "תראה לי",
                "תראי לי",
                "הצג",
                "תציג",
                "תציגי",
                "מה",
                "איזה",
                "להתחיל",
                "התחל",
                "מתחילים",
            ]
        )
        return has_next_workout_reference and asks_to_open_or_start

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
            "תיעדתי אימון",
            "תעד אימון",
            "לוג אימון",
            "עשיתי אימון",
            "עשיתי את האימון",
            "סיימתי אימון",
            "סיימתי את האימון",
        )
        if any(phrase in text for phrase in explicit_phrases):
            return True
        if text.startswith(("i did not ", "i didn't ", "i didnt ", "i didn’t ")):
            return False
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
        if "skipped workout" in text and any(verb in text for verb in ["log", "record", "track"]):
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
        negated_recent_workout = any(
            phrase in text
            for phrase in [
                "\u05dc\u05d0 \u05d4\u05ea\u05d0\u05de\u05e0\u05ea\u05d9",
                "did not workout",
                "did not work out",
                "didn't workout",
                "didn't work out",
                "didnt workout",
                "didnt work out",
            ]
        )
        long_break = any(
            phrase in text
            for phrase in [
                "\u05d7\u05d5\u05d3\u05e9",
                "\u05e9\u05d1\u05d5\u05e2\u05d9\u05d9\u05dd",
                "\u05e9\u05dc\u05d5\u05e9\u05d4 \u05e9\u05d1\u05d5\u05e2\u05d5\u05ea",
                "\u05db\u05de\u05d4 \u05e9\u05d1\u05d5\u05e2\u05d5\u05ea",
                "\u05ea\u05e7\u05d5\u05e4\u05d4",
                "for a month",
                "for weeks",
                "for months",
                "after a break",
                "layoff",
            ]
        )
        asks_recent_guidance = any(
            phrase in text
            for phrase in [
                "\u05d0\u05d9\u05da",
                "\u05dc\u05d4\u05de\u05e9\u05d9\u05da",
                "\u05de\u05d4 \u05dc\u05e2\u05e9\u05d5\u05ea",
                "how should",
                "how do i continue",
                "what should i do",
                "continue",
            ]
        )
        if negated_recent_workout and asks_recent_guidance and not long_break:
            return True
        has_missed = any(phrase in text for phrase in ["פספסתי", "החמצתי", "missed workout", "skipped workout"])
        # Explicit guidance verbs only. A bare "?" used to qualify here, which let
        # logging questions like "פספסתי אימון אתמול, איך לתעד?" leak into guidance.
        asks_for_guidance = any(
            phrase in text
            for phrase in [
                "לחזור",
                "מה לעשות",
                "איך",
                "דרך",
                "תן לי",
                "תני לי",
                "להמשיך",
                "בלי להרגיש",
                "how should",
                "how do i continue",
                "what should i do",
                "continue",
            ]
        )
        return has_missed and asks_for_guidance

    @staticmethod
    def _is_return_after_break_guidance(text: str) -> bool:
        break_marker = any(
            phrase in text
            for phrase in [
                "לא התאמנתי",
                "לא התאמן",
                "לא התאמנה",
                "הפסקה",
                "אחרי חודש",
                "אחרי כמה שבועות",
                "אחרי כמה חודשים",
                "שבועיים בלי",
                "חודש בלי",
                "תקופה בלי",
                "after a break",
                "layoff",
            ]
        )
        training_marker = any(
            phrase in text
            for phrase in ["אימון", "אימונים", "להתאמן", "כושר", "חדר כושר", "training", "workout", "gym"]
        )
        asks_for_guidance = any(
            phrase in text
            for phrase in ["איך", "מה לעשות", "לחזור", "חזרה", "להמשיך", "תן לי", "תני לי", "אימון ראשון"]
        )
        return break_marker and training_marker and asks_for_guidance

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
