import re


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


def has_pain_or_injury_signal(text: str) -> bool:
    normalized = text.lower()
    scrubbed = normalized
    for pattern in NEGATED_PAIN_PATTERNS:
        scrubbed = re.sub(pattern, " ", scrubbed)
    return any(term in scrubbed for term in PAIN_OR_INJURY_TERMS)
