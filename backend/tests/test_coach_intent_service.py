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
