import re


_LATIN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*")
_HEBREW_TOKEN_RE = re.compile(r"[\u0590-\u05ff]+")
_VISIBLE_WORD_RE = re.compile(r"[\u0590-\u05ff]+|[A-Za-z][A-Za-z0-9_+-]*")
_ALLOWED_LATIN_TERM_PATTERNS = (
    r"\bRPE\b",
    r"\bRIR\b",
    r"\bDOMS\b",
    r"\bHIIT\b",
    r"\bTRX\b",
    r"\bEMOM\b",
    r"\bAMRAP\b",
    r"\bZone\s*[245]\b",
    r"\bfull[- ]body\b",
    r"\bgoblet\s+squat\b",
    r"\bpush\s*/\s*pull\s*/\s*legs\b",
    r"\bPPL\b",
    r"\bmobility\b",
    r"\bsplit\b",
    r"\bdeload\b",
    r"\bprogressive\s+overload\b",
)
_DISALLOWED_GENERIC_LATIN_TOKENS = {
    "action",
    "calorie",
    "calories",
    "exercise",
    "plan",
    "protein",
    "recover",
    "recovery",
    "reps",
    "sets",
    "summary",
    "target",
    "tomorrow",
    "walk",
    "weekly",
    "workout",
}
_NEUTRAL_ADDRESS_REQUEST_MARKERS = (
    "בלי לפנות אליי בלשון זכר או נקבה",
    "בלי לפנות אלי בלשון זכר או נקבה",
    "בלי לשון זכר או נקבה",
    "לא לפנות אליי בלשון זכר",
    "לא לפנות אלי בלשון זכר",
    "ניסוח ניטרלי",
    "פנייה ניטרלית",
    "פניה ניטרלית",
    "לשון ניטרלית",
    "gender neutral",
)
_DIRECT_HEBREW_ADDRESS_OR_COMMAND_TERMS = (
    "אתה",
    "אתם",
    "אתן",
    "מתאמן",
    "מתאמנת",
    "תוכל",
    "תוכלי",
    "הוסף",
    "הוסיפי",
    "הוסיפו",
    "תוסיף",
    "תוסיפי",
    "תוסיפו",
    "תתקדם",
    "תתקדמי",
    "תתקדמו",
    "התקדם",
    "התקדמי",
    "הגעת",
    "הגעתם",
    "הגעתן",
    "העלה",
    "העלי",
    "העלו",
    "הורד",
    "הורידי",
    "הורידו",
    "בחר",
    "בחרי",
    "בחרו",
    "בצע",
    "בצעי",
    "בצעו",
    "עשה",
    "עשי",
    "עשו",
    "תעשה",
    "תעשי",
    "תעשו",
    "שמור",
    "שמרי",
    "שמרו",
    "עצור",
    "עצרי",
    "עצרו",
    "פנה",
    "פני",
    "פנו",
    "כתוב",
    "כתבי",
    "כתבו",
    "תכתוב",
    "תכתבי",
    "תכתבו",
    "נסה",
    "נסי",
    "נסו",
    "שאל",
    "שאלי",
    "שאלו",
    "תעד",
    "תעדי",
    "תעדו",
    "קבע",
    "קבעי",
    "קבעו",
)


def contains_hebrew(text: str) -> bool:
    return any("\u0590" <= character <= "\u05ff" for character in text)


def has_disallowed_latin_text(text: str, *, allowed_source_text: str = "") -> bool:
    """Return True when Latin text dominates a Hebrew-first user-visible response."""

    del allowed_source_text
    latin_count = len(_latin_tokens(text))
    if latin_count == 0:
        return False

    hebrew_count = len(_hebrew_tokens(text))
    if hebrew_count == 0:
        return True

    if hebrew_count <= 1 and latin_count >= 3:
        return True
    if hebrew_count <= 2 and latin_count >= 5:
        return True
    if _has_unapproved_latin_terms(text):
        return True
    if _max_latin_token_run(text) >= 8:
        return True

    visible_word_count = hebrew_count + latin_count
    return latin_count >= 5 and (latin_count / visible_word_count) >= 0.75


def violates_requested_neutral_address(user_text: str, response_text: str) -> bool:
    if not user_requested_neutral_address(user_text):
        return False
    return has_direct_hebrew_address_or_command(response_text)


def user_requested_neutral_address(text: str) -> bool:
    normalized = text.lower()
    return any(marker in normalized for marker in _NEUTRAL_ADDRESS_REQUEST_MARKERS)


def has_direct_hebrew_address_or_command(text: str) -> bool:
    return any(_contains_hebrew_word(text, term) for term in _DIRECT_HEBREW_ADDRESS_OR_COMMAND_TERMS)


def strip_markdown_markers(text: str) -> str:
    cleaned = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s{0,3}(?:[-*+]\s+|[•◦▪]\s*|\d+[.)]\s+|>\s*)", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\|(.+)\|\s*$", _strip_markdown_table_row, cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s{0,3}[-*_]{3,}\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def polish_hebrew_coach_response(text: str) -> str:
    """Clean provider responses without turning the guard into a translator."""

    cleaned = strip_markdown_markers(text)
    replacements = {
        "שליחות מלאות": "חזרות נקיות",
        "נחת את הגוף": "נותן לגוף להתאושש",
        "לבנייה שריר": "לבניית שריר",
        "לבנייה של שריר": "לבניית שריר",
        "זה הרמה": "זו הרמה",
        "וסוף סוף": "והגעת קרוב לכשל",
        "סוף כוחך": "כשל טכני",
        "השמור ": "שמור ",
        "נפת חזרות": "טווח חזרות",
        "התקדמות טיפשית": "התקדמות הדרגתית",
        "מחרוק קלוריות": "שורף קלוריות",
        "התמקד בשלוש דברים": "התמקד בשלושה דברים",
        "שלוש דברים": "שלושה דברים",
        "וישישי": "ושישי",
        "בניהם": "ביניהם",
        "טווח של תנועה": "טווח התנועה",
        "השקיעה הזה": "התרגיל הזה",
        "קשר אותה למישהו מוסמך": "פנה לאיש מקצוע מוסמך",
        "target של צעדים": "יעד צעדים",
        "ל-target": "ליעד",
        "אם החום או DOMS": "אם הכאב או DOMS",
        "תרגיל עליון קל": "אימון פלג גוף עליון קל",
        "שתרגישי בה טוב": "שמרגישה נוחה",
        "איפה אתה חש כרגע את הברך שלך? עדיין כואבת או זה עבר?": "איך הברך מרגישה עכשיו? עדיין כואב או שזה עבר?",
        "תוכנית שבוע קצרה": "תוכנית שבועית קצרה",
        "דחיפת אדמה": "שכיבות סמיכה",
        "משיכת גוף": "תרגיל משיכה",
    }
    for broken, natural in replacements.items():
        cleaned = cleaned.replace(broken, natural)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip()


def _latin_tokens(text: str) -> list[str]:
    return _LATIN_TOKEN_RE.findall(text)


def _hebrew_tokens(text: str) -> list[str]:
    return _HEBREW_TOKEN_RE.findall(text)


def _max_latin_token_run(text: str) -> int:
    current = 0
    longest = 0
    for token in _VISIBLE_WORD_RE.findall(text):
        if _LATIN_TOKEN_RE.fullmatch(token):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _has_unapproved_latin_terms(text: str) -> bool:
    remaining = text
    for pattern in _ALLOWED_LATIN_TERM_PATTERNS:
        remaining = re.sub(pattern, " ", remaining, flags=re.IGNORECASE)

    remaining_latin_tokens = [token.lower() for token in _latin_tokens(remaining)]
    if not remaining_latin_tokens:
        return False
    if any(token in _DISALLOWED_GENERIC_LATIN_TOKENS for token in remaining_latin_tokens):
        return True
    return _max_latin_token_run(remaining) >= 2


def _contains_hebrew_word(text: str, word: str) -> bool:
    return bool(re.search(rf"(?<![\u0590-\u05ff]){re.escape(word)}(?![\u0590-\u05ff])", text))


def _strip_markdown_table_row(match: re.Match[str]) -> str:
    return " ".join(part.strip() for part in match.group(1).split("|") if part.strip())
