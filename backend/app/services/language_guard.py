import re


_LATIN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*")
_HEBREW_TOKEN_RE = re.compile(r"[\u0590-\u05ff]+")
_VISIBLE_WORD_RE = re.compile(r"[\u0590-\u05ff]+|[A-Za-z][A-Za-z0-9_+-]*")


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
    if _max_latin_token_run(text) >= 8:
        return True

    visible_word_count = hebrew_count + latin_count
    return latin_count >= 5 and (latin_count / visible_word_count) >= 0.75


def strip_markdown_markers(text: str) -> str:
    cleaned = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s{0,3}[-*_]{3,}\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("`", "")
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
