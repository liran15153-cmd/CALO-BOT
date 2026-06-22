import re

from backend.app.services.text_normalization import normalize_user_text


PAIN_OR_INJURY_TERMS = ["hurts", "pain", "injury", "injured", "sharp pain", "כאב", "פציעה", "נפצעתי", "כואב"]

NEGATED_PAIN_PATTERNS = [
    r"\bno\s+(?:sharp\s+)?pain\b",
    r"\bwithout\s+(?:sharp\s+)?pain\b",
    r"\bpain[-\s]?free\b",
    r"בלי\s+כאב(?:ים)?",
    r"ללא\s+כאב(?:ים)?",
    r"אין\s+כאב(?:ים)?",
    r"לא\s+היה\s+כאב(?:ים)?",
    r"לא\s+היו\s+כאב(?:ים)?",
]


_PAIN_AREAS_HE = {
    "ברך": ["ברך", "ברכיים", "knee", "knees"],
    "כתף": ["כתף", "כתפיים", "shoulder", "shoulders"],
    "גב תחתון": ["גב תחתון", "מותן", "מותניים", "low back", "lower back"],
    "גב עליון": ["גב עליון", "upper back"],
    "מרפק": ["מרפק", "elbow"],
    "קרסול": ["קרסול", "ankle"],
    "ירך": ["ירך", "hip"],
    "צוואר": ["צוואר", "neck"],
    "פרק יד": ["פרק יד", "wrist"],
}


def _scrub_negated_pain(text: str) -> str:
    scrubbed = normalize_user_text(text)
    for pattern in NEGATED_PAIN_PATTERNS:
        scrubbed = re.sub(pattern, " ", scrubbed)
    return scrubbed


def has_pain_or_injury_signal(text: str) -> bool:
    return any(term in _scrub_negated_pain(text.lower()) for term in PAIN_OR_INJURY_TERMS)


def extract_pain_area(text: str) -> str | None:
    """Return a short Hebrew label for the body area the user mentioned pain in,
    or None if no area was detected. Side ("שמאל"/"ימין") is appended best-effort
    when present in the same message."""
    scrubbed = _scrub_negated_pain(text.lower())
    matched_label: str | None = None
    for label, aliases in _PAIN_AREAS_HE.items():
        if any(alias in scrubbed for alias in aliases):
            matched_label = label
            break
    if matched_label is None:
        return None
    if "שמאל" in scrubbed or " left" in scrubbed or "left " in scrubbed:
        return f"{matched_label} שמאל"
    if "ימין" in scrubbed or " right" in scrubbed or "right " in scrubbed:
        return f"{matched_label} ימין"
    return matched_label
