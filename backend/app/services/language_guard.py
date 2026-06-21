import re
from dataclasses import dataclass

from backend.app.config import get_settings


_LATIN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*")
_HEBREW_TOKEN_RE = re.compile(r"[\u0590-\u05ff]+")
_VISIBLE_WORD_RE = re.compile(r"[\u0590-\u05ff]+|[A-Za-z][A-Za-z0-9_+-]*")
_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?")
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
    "השתמש",
    "השתמשי",
    "השתמשו",
    "תשתמש",
    "תשתמשי",
    "תשתמשו",
    "הרם",
    "הרימי",
    "הרימו",
    "תרים",
    "תרימי",
    "תרימו",
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
_NEUTRAL_COMMAND_REPLACEMENTS = {
    "אתה": "",
    "אתם": "",
    "אתן": "",
    "תוכל": "אפשר",
    "תוכלי": "אפשר",
    "השתמש": "להשתמש",
    "השתמשי": "להשתמש",
    "השתמשו": "להשתמש",
    "תשתמש": "להשתמש",
    "תשתמשי": "להשתמש",
    "תשתמשו": "להשתמש",
    "הרם": "להרים",
    "הרימי": "להרים",
    "הרימו": "להרים",
    "תרים": "להרים",
    "תרימי": "להרים",
    "תרימו": "להרים",
    "הוסף": "להוסיף",
    "הוסיפי": "להוסיף",
    "הוסיפו": "להוסיף",
    "תוסיף": "להוסיף",
    "תוסיפי": "להוסיף",
    "תוסיפו": "להוסיף",
    "התקדם": "להתקדם",
    "התקדמי": "להתקדם",
    "העלה": "להעלות",
    "העלי": "להעלות",
    "העלו": "להעלות",
    "הורד": "להוריד",
    "הורידי": "להוריד",
    "הורידו": "להוריד",
    "בחר": "לבחור",
    "בחרי": "לבחור",
    "בחרו": "לבחור",
    "בצע": "לבצע",
    "בצעי": "לבצע",
    "בצעו": "לבצע",
    "עשה": "לבצע",
    "עשי": "לבצע",
    "עשו": "לבצע",
    "תעשה": "לבצע",
    "תעשי": "לבצע",
    "תעשו": "לבצע",
    "שמור": "לשמור",
    "שמרי": "לשמור",
    "שמרו": "לשמור",
    "עצור": "לעצור",
    "עצרי": "לעצור",
    "עצרו": "לעצור",
    "פנה": "לפנות",
    "פני": "לפנות",
    "פנו": "לפנות",
    "כתוב": "לכתוב",
    "כתבי": "לכתוב",
    "כתבו": "לכתוב",
    "תכתוב": "לכתוב",
    "תכתבי": "לכתוב",
    "תכתבו": "לכתוב",
    "נסה": "לנסות",
    "נסי": "לנסות",
    "נסו": "לנסות",
    "שאל": "לשאול",
    "שאלי": "לשאול",
    "שאלו": "לשאול",
    "תעד": "לתעד",
    "תעדי": "לתעד",
    "תעדו": "לתעד",
    "קבע": "לקבוע",
    "קבעי": "לקבוע",
    "קבעו": "לקבוע",
}
_BROKEN_HEBREW_REPLACEMENTS = {
    "אנחנו נשים את זה בחשבון": "ניקח את זה בחשבון",
    "נשים את זה בחשבון": "ניקח את זה בחשבון",
    "אימנים": "מתאמנים",
    "מתכננן": "מתכנן",
    "בואו נדברנו": "נדבר",
    "חומקות": "התחכמויות",
    "השבוע הבא אתה אמרת": "אמרת שבשבוע הבא",
    "או זה יותר משאלה": "או שזו יותר שאלה",
    "אשנה קצר וברור": "אענה קצר וברור",
    "לתחילה בטוח": "כדי להתחיל בצורה בטוחה",
    "בתוכניה": "בתוכנית",
    "תוכניה": "תוכנית",
    "תוכניית": "תוכנית",
    "דחיפת קרקע": "שכיבות סמיכה",
    "להשאר": "להישאר",
    "סקוואט גוף ממושקל": "סקוואט במשקל גוף",
    "אינץ׳ דחיפה": "שכיבות סמיכה",
    "הינג׳ גג": "הינג׳ ירך",
    "2 סטים כל תרגיל": "2 סטים לכל תרגיל",
    "חזרות בעודן נשארות ברזרבה": "חזרות ברזרבה",
    "לא תופסים כשל": "לא להגיע לכשל",
    "מה החוששות שלך הכי גדולות": "מה החשש הכי גדול",
    "גוף בעיקר משקלך": "משקל גוף",
    "אני דאוג": "אני דואג",
    "דאוג": "דואג",
    "או זה": "או שזה",
    "חומרא": "עומס גבוה",
    "פעמים שתרגול האט": "לפעמים תרגול איטי",
    "בעזה": "ברזרבה",
    "לקצה המדף": "לקצה",
    "קצה המדף": "הקצה",
    "כוח בברך": "כאב בברך",
    "בטוב": "בסדר",
    "קשיבות לגופך": "הקשבה לגוף",
    "אל תתחרות": "לא להתחרות",
    "תתחרות": "להתחרות",
    "גופך לא מתוקן": "הגוף לא מתאושש",
    "חדות או נקיטה": "כאב חד",
    "נקיטה": "כאב חד",
    "לשלוש סטים": "לשלושה סטים",
    "חזקק": "חזק",
    "30 שנייה": "30 שניות",
    "הקצה החד": "הקצה",
    "האם אתה רוצה אני אגיד": "רוצה שאגיד",
}
_BROKEN_HEBREW_ARTIFACTS = tuple(_BROKEN_HEBREW_REPLACEMENTS)


@dataclass(frozen=True)
class ResponseQuality:
    ok: bool
    issues: tuple[str, ...] = ()


def contains_hebrew(text: str) -> bool:
    if not _language_guard_enabled():
        return True
    return any("\u0590" <= character <= "\u05ff" for character in text)


def has_disallowed_latin_text(text: str, *, allowed_source_text: str = "") -> bool:
    """Return True when Latin text dominates a Hebrew-first user-visible response."""

    if not _language_guard_enabled():
        return False

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


def has_suspicious_non_hebrew_script(text: str) -> bool:
    """Return True for alphabetic scripts that should never appear in Hebrew coach output."""

    if not _language_guard_enabled():
        return False

    for character in text:
        if not character.isalpha():
            continue
        if "\u0590" <= character <= "\u05ff":
            continue
        if ("a" <= character.lower() <= "z"):
            continue
        return True
    return False


def has_broken_hebrew_artifacts(text: str) -> bool:
    """Return True for known translated-sounding Hebrew artifacts in provider output."""

    if not _language_guard_enabled():
        return False
    return any(artifact in text for artifact in _BROKEN_HEBREW_ARTIFACTS)


def assess_hebrew_response_quality(user_text: str, response_text: str) -> ResponseQuality:
    if not _language_guard_enabled():
        return ResponseQuality(ok=True)

    issues: list[str] = []
    if not contains_hebrew(response_text):
        issues.append("missing_hebrew")
    if has_disallowed_latin_text(response_text):
        issues.append("latin_text")
    if has_suspicious_non_hebrew_script(response_text):
        issues.append("suspicious_script")
    if has_broken_hebrew_artifacts(response_text):
        issues.append("broken_hebrew")
    if violates_requested_neutral_address(user_text, response_text):
        issues.append("neutral_address")
    return ResponseQuality(ok=not issues, issues=tuple(issues))


def violates_requested_neutral_address(user_text: str, response_text: str) -> bool:
    if not _language_guard_enabled():
        return False
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

    if not _language_guard_enabled():
        return text

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
        "\u05dc\u05dc\u05d0\uc11c\u05d1\u05e8": "בלי",
        "reserve in reserve": "חזרות ברזרבה",
        **_BROKEN_HEBREW_REPLACEMENTS,
    }
    for broken, natural in replacements.items():
        cleaned = cleaned.replace(broken, natural)
    cleaned = re.sub(r"(?<![A-Za-z])even(?![A-Za-z])", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip()


def repair_hebrew_coach_response(user_text: str, response_text: str) -> str:
    if not _language_guard_enabled():
        return response_text

    repaired = polish_hebrew_coach_response(response_text)
    if user_requested_neutral_address(user_text):
        repaired = _neutralize_direct_address(repaired)
    repaired = _trim_hebrew_coach_response(repaired)
    repaired = re.sub(r"\s{2,}", " ", repaired)
    repaired = re.sub(r" *\n *", "\n", repaired)
    return repaired.strip()


def _latin_tokens(text: str) -> list[str]:
    return _LATIN_TOKEN_RE.findall(text)


def _language_guard_enabled() -> bool:
    settings = get_settings()
    return settings.language_guard_enabled and settings.language_guard_mode != "off"


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


def _neutralize_direct_address(text: str) -> str:
    neutralized = text
    for direct, neutral in _NEUTRAL_COMMAND_REPLACEMENTS.items():
        neutralized = re.sub(
            rf"(?<![\u0590-\u05ff]){re.escape(direct)}(?![\u0590-\u05ff])",
            neutral,
            neutralized,
        )
    neutralized = re.sub(r"\s+([?.!,;:])", r"\1", neutralized)
    return neutralized


def _trim_hebrew_coach_response(text: str) -> str:
    sentence_parts = [match.group(0).strip() for match in _SENTENCE_RE.finditer(text) if match.group(0).strip()]
    if len(sentence_parts) > 4:
        text = " ".join(sentence_parts[:4])

    words = text.split()
    if len(words) > 90:
        text = " ".join(words[:90]).rstrip(" ,;:")
        if not re.search(r"[.!?]$", text):
            text += "."
    return text.strip()


def _strip_markdown_table_row(match: re.Match[str]) -> str:
    return " ".join(part.strip() for part in match.group(1).split("|") if part.strip())
