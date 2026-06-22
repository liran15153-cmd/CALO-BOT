import re


# ponytail: tiny routing typo table; replace with a measured classifier only if this grows.
_WORD_REPLACEMENTS = {
    "aet": "ate",
    "analize": "analyze",
    "begginer": "beginner",
    "buld": "build",
    "cal": "calorie",
    "callories": "calories",
    "chiken": "chicken",
    "equipmant": "equipment",
    "foto": "photo",
    "lanch": "lunch",
    "minuts": "minutes",
    "mnth": "month",
    "neee": "knee",
    "sald": "salad",
    "squating": "squatting",
    "thini": "tahini",
    "tody": "today",
    "wrkout": "workout",
    "workot": "workout",
}

_TEXT_REPLACEMENTS = {
    "אכלטי": "אכלתי",
    "אימן": "אימון",
    "בחזא": "בחזה",
    "בצהרים": "בצהריים",
    "כועב": "כואב",
    "כועבת": "כואבת",
    "סלת": "סלט",
}


def normalize_user_text(text: str) -> str:
    normalized = text.lower().strip()
    for typo, replacement in _TEXT_REPLACEMENTS.items():
        normalized = re.sub(rf"(?<!\w){re.escape(typo)}(?!\w)", replacement, normalized)
    for typo, replacement in _WORD_REPLACEMENTS.items():
        normalized = re.sub(rf"\b{re.escape(typo)}\b", replacement, normalized)
    return normalized
