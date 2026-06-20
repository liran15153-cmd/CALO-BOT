from backend.app.services.language_guard import (
    has_disallowed_latin_text,
    polish_hebrew_coach_response,
    strip_markdown_markers,
    violates_requested_neutral_address,
)


def test_language_guard_allows_common_fitness_terms_inside_hebrew_response():
    text = "היום תעשה 2 סטים של goblet squat בקצב נשלט, full-body קצר, RPE 7."

    assert has_disallowed_latin_text(text) is False


def test_language_guard_allows_short_english_terms_inside_hebrew_response():
    text = "היום תעשה mobility קצרה לירך, HIIT פעם אחת בשבוע, ו-Zone 2 קל אחרי אימון כוח."

    assert has_disallowed_latin_text(text) is False


def test_language_guard_blocks_generic_english_headings_and_echoed_phrases():
    heading_text = "Weekly summary\n\nסיכום: עשית אימון אחד."
    action_text = "Action plan: שני אימוני כוח והליכות קלות השבוע."
    echoed_text = "כן. recover tomorrow עם הליכה קלה וחלבון מספיק."

    assert has_disallowed_latin_text(heading_text) is True
    assert has_disallowed_latin_text(action_text) is True
    assert has_disallowed_latin_text(echoed_text) is True


def test_language_guard_still_blocks_english_only_sentences():
    text = "Start with goblet squat and then do a full-body workout today."

    assert has_disallowed_latin_text(text) is True


def test_language_guard_still_blocks_dominant_english_with_little_hebrew():
    text = "כן. do a light workout tomorrow and eat protein."

    assert has_disallowed_latin_text(text) is True


def test_neutral_address_guard_only_runs_when_user_requested_it():
    user_text = "מה זה progressive overload?"
    response_text = "הוסף חזרה אחת כשכל הסטים קלים, ואז תבדוק שוב."

    assert violates_requested_neutral_address(user_text, response_text) is False


def test_neutral_address_guard_flags_direct_address_and_commands_when_requested():
    user_text = "מה זה progressive overload? בלי לפנות אליי בלשון זכר או נקבה."
    response_text = "הוסף חזרה אחת. כמה חזרות אתה מקבל כרגע?"

    assert violates_requested_neutral_address(user_text, response_text) is True


def test_neutral_address_guard_allows_neutral_infinitives_and_common_false_positives():
    user_text = "מה זה RPE? ניסוח ניטרלי בבקשה."
    response_text = (
        "זה יכול להגיע מעייפות כללית, לא רק מהשריר עצמו. "
        "הפעולה הבאה: להוסיף 1-2 חזרות רק כשהטכניקה נשארת יציבה."
    )

    assert violates_requested_neutral_address(user_text, response_text) is False


def test_neutral_address_guard_uses_hebrew_word_boundaries():
    user_text = "מה זה RIR? בלי לשון זכר או נקבה."
    response_text = "אפשר לבחור טווח חזרות ולהישאר עם שתי חזרות ברזרבה."

    assert violates_requested_neutral_address(user_text, response_text) is False


def test_strip_markdown_markers_removes_lists_blockquotes_and_table_syntax():
    text = """
## תוכנית קצרה
- עשה **3 סטים** של 10 חזרות
1. שמור `RPE 7`
• בלי רשימות בולטות
> בלי לדחוף דרך כאב
| מונח | שימוש |
| --- | --- |
| reps | חזרות |
"""

    cleaned = strip_markdown_markers(text)

    assert "##" not in cleaned
    assert "- עשה" not in cleaned
    assert "1. שמור" not in cleaned
    assert "•" not in cleaned
    assert ">" not in cleaned
    assert "|" not in cleaned
    assert "**" not in cleaned
    assert "`" not in cleaned
    assert "3 סטים" in cleaned
    assert "RPE 7" in cleaned
    assert "reps" in cleaned
    assert "חזרות" in cleaned


def test_polish_hebrew_coach_response_repairs_common_provider_translation_artifacts():
    text = (
        "• המטרה היא להישאר תחת 10 שליחות מלאות.\n"
        "זה קורה כשנחת את הגוף בסדר. זה הרמה הטובה ביותר לבנייה שריר.\n"
        "אם עשית 8 חזרות וסוף סוף, זה RIR 0-1."
    )

    cleaned = polish_hebrew_coach_response(text)

    assert "•" not in cleaned
    assert "שליחות מלאות" not in cleaned
    assert "נחת את הגוף" not in cleaned
    assert "לבנייה שריר" not in cleaned
    assert "וסוף סוף" not in cleaned
    assert "חזרות נקיות" in cleaned
    assert "נותן לגוף להתאושש" in cleaned
    assert "בניית שריר" in cleaned


def test_polish_hebrew_coach_response_repairs_provider_hebrew_and_generic_english_artifacts():
    text = (
        "למחר התמקד בשלוש דברים. אפשר יום שני וחמישי או שלישי וישישי, עם יום מנוחה בניהם. "
        "אם כאב בברך מופיע, דלג על השקיעה הזה וקשר אותה למישהו מוסמך. "
        "לא צריך להגיע ל-target של צעדים. "
        "הנה תוכנית שבוע קצרה: דחיפת אדמה ואז משיכת גוף."
    )

    cleaned = polish_hebrew_coach_response(text)

    assert "שלוש דברים" not in cleaned
    assert "וישישי" not in cleaned
    assert "בניהם" not in cleaned
    assert "השקיעה הזה" not in cleaned
    assert "קשר אותה למישהו מוסמך" not in cleaned
    assert "target" not in cleaned
    assert "תוכנית שבוע קצרה" not in cleaned
    assert "דחיפת אדמה" not in cleaned
    assert "משיכת גוף" not in cleaned
    assert "שלושה דברים" in cleaned
    assert "ושישי" in cleaned
    assert "ביניהם" in cleaned
    assert "התרגיל הזה" in cleaned
    assert "איש מקצוע מוסמך" in cleaned
    assert "יעד צעדים" in cleaned
    assert "תוכנית שבועית קצרה" in cleaned
    assert "שכיבות סמיכה" in cleaned
    assert "תרגיל משיכה" in cleaned
