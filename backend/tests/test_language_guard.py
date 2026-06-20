from backend.app.services.language_guard import has_disallowed_latin_text


def test_language_guard_allows_common_fitness_terms_inside_hebrew_response():
    text = "היום תעשה 2 סטים של goblet squat בקצב נשלט, full-body קצר, RPE 7."

    assert has_disallowed_latin_text(text) is False


def test_language_guard_allows_short_english_terms_inside_hebrew_response():
    text = "היום תעשה recovery walk קצר, mobility לירך, ואז protein בארוחה."

    assert has_disallowed_latin_text(text) is False


def test_language_guard_allows_short_english_heading_before_hebrew_body():
    text = "Weekly summary\n\nסיכום: עשית workout אחד."

    assert has_disallowed_latin_text(text) is False


def test_language_guard_still_blocks_english_only_sentences():
    text = "Start with goblet squat and then do a full-body workout today."

    assert has_disallowed_latin_text(text) is True


def test_language_guard_still_blocks_dominant_english_with_little_hebrew():
    text = "כן. do a light workout tomorrow and eat protein."

    assert has_disallowed_latin_text(text) is True
