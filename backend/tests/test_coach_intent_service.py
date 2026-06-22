from backend.app.services.coach_intent_service import CoachIntentService


def test_intent_service_detects_hebrew_workout_plan_requests():
    intent = CoachIntentService().classify("תבנה לי תוכנית אימון של 2 ימים עם משקולות")

    assert intent.name == "workout_plan"


def test_intent_service_detects_feminine_hebrew_workout_plan_requests():
    intent = CoachIntentService().classify("תבני לי תוכנית אימון של 4 שבועות, 4 ימים בשבוע")

    assert intent.name == "workout_plan"


def test_intent_service_detects_hebrew_summary_requests():
    service = CoachIntentService()

    assert service.classify("תני לי סיכום שבועי לפי מה שתיעדתי").name == "weekly_summary"
    assert service.classify("תני לי סיכום יומי קצר").name == "daily_summary"


def test_intent_service_detects_hebrew_workout_and_meal_logs():
    service = CoachIntentService()

    assert service.classify("תיעדתי אימון: 3 סטים של סקוואט").name == "workout_log"
    assert service.classify("אכלתי ארוחת ערב: אורז, עוף וסלט").name == "meal_log"


def test_intent_service_detects_fitness_term_guidance_requests():
    service = CoachIntentService()

    assert service.classify("מה עדיף באימון כוח: RPE 8 או להשאיר 2 חזרות ברזרבה?").name == "fitness_term_guidance"
    assert service.classify("תסביר לי היפרטרופיה, סטים קשים ו-RIR").name == "fitness_term_guidance"
    assert service.classify("אני עייף כבר שבוע והביצועים יורדים. צריך דילואד?").name == "fitness_term_guidance"
    assert service.classify("מה זה DOMS ומה לעשות אם השרירים תפוסים?").name == "fitness_term_guidance"
    assert service.classify("מה זה Zone 2 ואיך אדע שאני שם בלי שעון דופק?").name == "fitness_term_guidance"
    assert service.classify("מה עדיף לשריר: full-body או push/pull/legs?").name == "fitness_term_guidance"
    assert service.classify("איך לעשות חימום טוב לפני אימון כוח?").name == "fitness_term_guidance"
    assert service.classify("צריך קירור ומתיחות אחרי אימון כדי למנוע DOMS?").name == "fitness_term_guidance"


def test_intent_service_detects_common_hebrew_equipment_and_missed_workout_guidance():
    service = CoachIntentService()

    assert service.classify("אני מתחיל ויש לי רק גומייה. איזה תרגיל גב לעשות במקום חתירה במכונה?").name == "equipment_substitution_guidance"
    assert service.classify("פספסתי שני אימונים השבוע. תן לי דרך לחזור בלי להרגיש שאני מתחיל מאפס.").name == "missed_workout_guidance"


def test_intent_service_detects_nutrition_guidance_without_logging_meal():
    service = CoachIntentService()

    assert service.classify("אני מנסה לרדת קצת באחוזי שומן אבל לא רוצה לספור קלוריות. מה לאכול היום סביב אימון ערב?").name == "nutrition_guidance"
    assert service.classify("אם אעלה תמונה של קערת אורז, עוף וטחינה, כמה מדויק אפשר להעריך קלוריות?").name == "nutrition_guidance"


def test_intent_service_prioritizes_supplement_stimulant_safety_over_nutrition_timing():
    service = CoachIntentService()

    assert (
        service.classify("פרה-וורקאאוט עם הרבה קפאין ו-yohimbine לפני אימון ערב - בטוח או לוותר?").name
        == "supplement_safety_guidance"
    )
    assert service.classify("fat burner לפני אימון ערב זה רעיון טוב?").name == "supplement_safety_guidance"


def test_intent_service_detects_weekly_action_plan_guidance():
    service = CoachIntentService()

    assert (
        service.classify("תן לי action plan קצר לשבוע עם שני אימוני כוח והליכות. בלי אנגלית מיותרת.").name
        == "weekly_action_plan_guidance"
    )
    assert service.classify("תוכנית שבוע קצרה עם שני אימוני כוח ושלוש הליכות").name == "weekly_action_plan_guidance"


def test_intent_service_detects_low_energy_action_guidance():
    service = CoachIntentService()

    assert service.classify("אין לי כוח היום, תן לי פעולה אחת קטנה").name == "low_energy_action_guidance"
    assert service.classify("I have low energy today, give me one minimum action").name == "low_energy_action_guidance"


def test_intent_service_does_not_log_set_explanation_questions():
    service = CoachIntentService()

    assert service.classify("תסביר לי על סטים של 5 חזרות").name == "general_chat"
    assert service.classify("מה ההבדל בין סטים של 8 לסטים של 12?").name == "general_chat"


def test_intent_service_logs_explicit_set_descriptions():
    service = CoachIntentService()

    assert service.classify("עשיתי 3 סטים של 10 חזרות בסקוואט").name == "workout_log"
    assert service.classify("תעד אימון: 3 סטים של 8 חזרות בלחיצת חזה").name == "workout_log"


def test_intent_service_prefers_meal_log_over_summary_when_food_is_mentioned():
    service = CoachIntentService()

    assert service.classify("סיכום היום: אכלתי ביצים").name == "meal_log"
    assert service.classify("סיכום שבועי בבקשה").name == "weekly_summary"


def test_intent_service_routes_missed_workout_questions_about_logging_to_workout_log():
    service = CoachIntentService()

    assert service.classify("פספסתי אימון אתמול, איך לתעד?").name == "workout_log"
    assert service.classify("פספסתי אימון אתמול, איך להמשיך?").name == "missed_workout_guidance"


def test_intent_service_prefers_meal_log_over_nutrition_guidance_when_food_is_eaten():
    service = CoachIntentService()

    assert service.classify("אכלתי חלבון לפני אימון").name == "meal_log"
    assert service.classify("מה לאכול לפני אימון ערב?").name == "nutrition_guidance"


def test_intent_service_keeps_bare_creatine_mentions_in_general_chat():
    service = CoachIntentService()

    assert service.classify("אני שונא קריאטין").name == "general_chat"
    assert service.classify("קריאטין בטוח?").name == "creatine_guidance"
    assert service.classify("תוסף קריאטין לפני אימון ערב, בטוח?").name == "supplement_safety_guidance"


def test_intent_service_routes_food_judgment_questions_to_nutrition_not_meal_log():
    service = CoachIntentService()

    # "I ate X, is it ruining my cut?" is a nutrition question, not a meal to log.
    assert service.classify("אכלתי המבורגר, זה דופק לי את החיטוב?").name == "nutrition_guidance"
    assert service.classify("אכלתי פיצה, זה משמין?").name == "nutrition_guidance"
    # A plain eaten-food statement is still a log.
    assert service.classify("אכלתי חלבון לפני אימון").name == "meal_log"


def test_intent_service_detects_eating_slang_only_with_food_context():
    service = CoachIntentService()

    assert service.classify("זללתי פיצה שלמה אתמול").name == "meal_log"
    assert service.classify("חיסלתי צלחת אורז עם עוף").name == "meal_log"
    # Slang verbs used about training must NOT become a meal log.
    assert service.classify("טרפתי אימון רגליים").name != "meal_log"
    assert service.classify("חיסלתי את כל הסטים").name != "meal_log"


def test_intent_service_detects_gym_slang_workout_logs():
    service = CoachIntentService()

    assert service.classify("התאמנתי היום גב וביצפס").name == "workout_log"
    assert service.classify("עשיתי רגליים").name == "workout_log"
    assert service.classify("עשיתי chest day").name == "workout_log"
    assert service.classify("אין לי כוח להתאמן, עשיתי רק 2 סטים חזה").name == "workout_log"
    # A past-tense mention framed as a question is not a log.
    assert service.classify("עשיתי chest day, כמה סטים הייתי צריך לעשות?").name != "workout_log"


def test_intent_service_detects_motivation_and_recovery():
    service = CoachIntentService()

    assert service.classify("אין לי מוטיבציה היום").name == "motivation_recovery"
    assert service.classify("נמאס לי, בא לי לוותר").name == "motivation_recovery"
    assert service.classify("כמה ימי מנוחה צריך בין אימונים?").name == "motivation_recovery"
    # Low-energy + explicit small-action request stays its own dedicated intent.
    assert service.classify("אין לי כוח היום, תן לי פעולה אחת קטנה").name == "low_energy_action_guidance"


def test_intent_service_detects_progress_and_body_metric_questions():
    service = CoachIntentService()

    assert service.classify("המשקל תקוע שבועיים מה לעשות?").name == "progress_metric"
    assert service.classify("עליתי 2 קילו, זה שריר או שומן?").name == "progress_metric"
    assert service.classify("ירדתי באחוזי שומן?").name == "progress_metric"
    assert service.classify("המשקל תקוע אבל אני אוכל טוב ומתאמן").name == "progress_metric"


def test_intent_service_detects_hebrew_strength_plan_request():
    service = CoachIntentService()

    # "תוכנית כוח" (strength plan) must be recognized as a plan request, not general chat.
    assert service.classify("תבנה לי תוכנית כוח של 2 ימים בלי ציוד").name == "workout_plan"
