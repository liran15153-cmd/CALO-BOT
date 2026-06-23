from backend.app.prompts import (
    coach_chat_prompt,
    meal_image_prompt,
    meal_text_prompt,
    safety_classification_prompt,
    workout_generation_prompt,
)


def test_coach_prompt_is_short_and_safety_aware():
    prompt = coach_chat_prompt()

    assert len(prompt.split()) < 180
    assert "עברית בלבד" in prompt
    assert "אבחון רפואי" in prompt
    assert "coaching_knowledge" in prompt
    assert "אל תטען שהמאמן מוסמך" in prompt
    assert "קצרים" in prompt


def test_coach_prompt_requires_natural_israeli_fitness_hebrew():
    prompt = coach_chat_prompt()

    assert "עברית ישראלית טבעית" in prompt
    assert "לא תרגום אוטומטי" in prompt
    assert "אל תתרגם מילולית מונחי כושר" in prompt
    assert "RPE 8" in prompt
    assert "bullet" in prompt
    assert "אם המשתמש מבקש לא לפנות בלשון זכר או נקבה" in prompt
    assert "ניסוח ניטרלי" in prompt
    for term in ["RPE", "RIR", "DOMS", "full-body", "דילואד", "progressive overload"]:
        assert term in prompt


def test_coach_prompt_contains_canonical_hebrew_style_examples():
    prompt = coach_chat_prompt()

    assert "ניקח את זה בחשבון" in prompt
    assert "מתאמנים" in prompt
    assert "שכיבות סמיכה" in prompt
    assert "אל תמציא צירופים" in prompt


def test_all_prompt_builders_return_task_specific_text():
    prompts = {
        "workout": workout_generation_prompt(),
        "meal_image": meal_image_prompt(),
        "meal_text": meal_text_prompt(),
        "safety": safety_classification_prompt(),
    }

    assert "תוכנית אימון מובנית" in prompts["workout"]
    assert "טווחי קלוריות" in prompts["meal_image"]
    assert "פריטי מזון" in prompts["meal_text"]
    assert "סיכון בטיחותי" in prompts["safety"]


def test_user_facing_prompts_explicitly_forbid_english_output():
    prompts = [
        coach_chat_prompt(),
        workout_generation_prompt(),
        meal_image_prompt(),
        meal_text_prompt(),
        safety_classification_prompt(),
    ]

    for prompt in prompts:
        assert "עברית בלבד" in prompt
        assert "אל תשתמש באנגלית" in prompt
