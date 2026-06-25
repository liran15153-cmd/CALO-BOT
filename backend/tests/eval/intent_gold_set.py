DETERMINISTIC_CASES = [
    {"text": "תבנה לי תוכנית אימון של 2 ימים עם משקולות", "expected_intent": "workout_plan", "category": "plan_build"},
    {"text": "תני לי תוכנית אימון של 4 שבועות, 4 ימים בשבוע", "expected_intent": "workout_plan", "category": "plan_build"},
    {"text": "אימון להיום 20 דקות בלי ציוד", "expected_intent": "workout_plan", "category": "single_workout"},
    {"text": "תוכנית לשבועיים שמתחילה היום", "expected_intent": "workout_plan", "category": "two_week_plan"},
    {"text": "תוכנית חודשית לבית בבקשה", "expected_intent": "workout_plan", "category": "monthly_plan"},
    {"text": "תיעדתי אימון: 3 סטים של סקוואט", "expected_intent": "workout_log", "category": "workout_log"},
    {"text": "עשיתי 3 סטים של 10 חזרות בסקוואט", "expected_intent": "workout_log", "category": "workout_log"},
    {"text": "התאמנתי היום גב ובייספס", "expected_intent": "workout_log", "category": "workout_log"},
    {"text": "עשיתי chest day", "expected_intent": "workout_log", "category": "workout_log"},
    {"text": "אכלתי ארוחת ערב: אורז, עוף וסלט", "expected_intent": "meal_log", "category": "meal_log"},
    {"text": "זללתי פיצה שלמה אתמול", "expected_intent": "meal_log", "category": "meal_log"},
    {"text": "חיסלתי צלחת אורז עם עוף", "expected_intent": "meal_log", "category": "meal_log"},
    {"text": "אין לי ספסל בתוכנית, תחליף רק את מה שצריך", "expected_intent": "workout_plan_edit", "category": "plan_edit"},
    {"text": "תוריד נפח מהתוכנית השבוע, אני עייף", "expected_intent": "workout_plan_edit", "category": "plan_edit"},
    {"text": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר", "expected_intent": "workout_plan_edit", "category": "plan_edit"},
    {"text": "מה השתנה לי בתוכנית?", "expected_intent": "workout_plan_change_summary", "category": "summary"},
    {"text": "תראה לי את התוכנית שלי", "expected_intent": "current_workout_plan_summary", "category": "summary"},
    {"text": "מה האימון הבא שלי?", "expected_intent": "next_workout_summary", "category": "summary"},
    {"text": "פספסתי שני אימונים השבוע. תן לי דרך לחזור בלי להרגיש שאני מתחיל מאפס.", "expected_intent": "missed_workout_guidance", "category": "guidance"},
    {"text": "פרי-וורקאאוט עם הרבה קפאין ו-yohimbine לפני אימון ערב - בטוח או לוותר?", "expected_intent": "supplement_safety_guidance", "category": "guidance"},
    {"text": "תן לי action plan קצר לשבוע עם שני אימוני כוח והליכות.", "expected_intent": "weekly_action_plan_guidance", "category": "guidance"},
    {"text": "אין לי כוח היום, תן לי פעולה אחת קטנה", "expected_intent": "low_energy_action_guidance", "category": "guidance"},
    {"text": "מה לאכול לפני אימון ערב?", "expected_intent": "nutrition_guidance", "category": "nutrition"},
    {"text": "אם אעלה תמונה של קערת אורז, עוף וטחינה, כמה מדויק אפשר להעריך קלוריות?", "expected_intent": "meal_image_guidance", "category": "nutrition"},
    {"text": "לא התאמנתי חודש, איך לחזור לחדר כושר?", "expected_intent": "return_after_break_guidance", "category": "guidance"},
    {"text": "סקוואט כואב לי בברך, איזה תרגיל לעשות במקום?", "expected_intent": "knee_squat_substitution", "category": "guidance"},
    {"text": "קריאטין בטוח?", "expected_intent": "creatine_guidance", "category": "guidance"},
    {"text": "אין לי מכונה לחתירה, מה לעשות במקום?", "expected_intent": "equipment_substitution_guidance", "category": "guidance"},
    {"text": "המשקל תקוע שבועיים מה לעשות?", "expected_intent": "progress_metric", "category": "progress"},
    {"text": "אין לי מוטיבציה היום", "expected_intent": "motivation_recovery", "category": "recovery"},
    {"text": "תסביר לי היפרטרופיה, סטים קשים ו-RIR", "expected_intent": "fitness_term_guidance", "category": "knowledge"},
    {"text": "כתוב לי מייל למנהל", "expected_intent": "non_fitness", "category": "non_fitness"},
]

FALLBACK_CASES = [
    {
        "text": "בא לי מסגרת מסודרת לחודש הקרוב כדי לחזור לכושר",
        "expected_intent": "workout_plan",
        "fallback_intent": "workout_plan",
        "category": "plan_build",
    },
    {
        "text": "צריך מסלול אימונים מסודר לשבועיים הקרובים",
        "expected_intent": "workout_plan",
        "fallback_intent": "workout_plan",
        "category": "two_week_plan",
    },
    {
        "text": "בא לי סדר באימונים, שלושה ימים בשבוע, לא משהו מסובך",
        "expected_intent": "workout_plan",
        "fallback_intent": "workout_plan",
        "category": "weekly_plan",
    },
    {
        "text": "דפקתי היום אימון גב במכון",
        "expected_intent": "workout_log",
        "fallback_intent": "workout_log",
        "category": "workout_log",
    },
]

GOLD_CASES = [*DETERMINISTIC_CASES, *FALLBACK_CASES]

assert len(DETERMINISTIC_CASES) >= 30
assert len(FALLBACK_CASES) >= 3
