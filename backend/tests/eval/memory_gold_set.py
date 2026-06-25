ALLERGY = "allergy"
MEDICAL = "medical"
INJURY = "injury"
RESTRICTION = "restriction_nutrition"


_SAFETY_CASES = [
    *[(text, ALLERGY) for text in [
        "אני אלרגי לבוטנים",
        "יש לי אלרגיה לאגוזים",
        "אלרגית לחלב",
        "אלרגי לגלוטן, אל תציע לי לחם",
        "I am allergic to milk",
        "I have a gluten allergy",
        "יש לי allergy to fish",
        "אל תתן לי טחינה, אני אלרגי לשומשום",
    ]],
    *[(text, MEDICAL) for text in [
        "יש לי סוכרת",
        "אני עם לחץ דם גבוה",
        "יש לי אסתמה",
        "אני לוקחת תרופות קבועות",
        "אני בהריון",
        "I have diabetes",
        "blood pressure is an issue for me",
    ]],
    *[(text, INJURY) for text in [
        "יש לי כאב בברך",
        "כואב לי הגב התחתון",
        "נפצעתי בכתף",
        "יש לי פציעה בקרסול",
        "כאב חד במרפק באימון",
        "my shoulder hurts",
        "I have a knee injury",
        "sharp pain in my back",
    ]],
    *[(text, RESTRICTION) for text in [
        "אני טבעוני",
        "אני טבעונית",
        "אני צמחוני",
        "אני אוכלת רק כשר",
        "לא אוכל חזיר",
        "לא אוכלת בשר",
        "I am vegan",
        "kosher food only",
    ]],
]

_TRAP_CASES = [
    "בוקר טוב",
    "תודה רבה",
    "אם הייתי אלרגי לבוטנים מה הייתי עושה?",
    "אין לי אלרגיה",
    "I am not allergic to peanuts",
    "מה זה RPE?",
    "אפשר אימון קצר?",
    "מה כדאי לאכול לפני אימון?",
    "אני לא בטוח מה המטרה שלי",
    "תסביר לי DOMS",
    "איך לשפר עקביות?",
    "מה זה דילואד?",
]

GOLD_CASES = [{"text": text, "expected_types": [fact_type]} for text, fact_type in _SAFETY_CASES]
GOLD_CASES += [{"text": text, "expected_types": []} for text in _TRAP_CASES]

assert len(GOLD_CASES) >= 30
