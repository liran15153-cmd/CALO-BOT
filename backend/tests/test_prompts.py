from backend.app.prompts import (
    coach_chat_prompt,
    meal_image_prompt,
    meal_text_prompt,
    memory_extraction_prompt,
    safety_classification_prompt,
    weekly_summary_prompt,
    workout_generation_prompt,
)


def test_coach_prompt_is_short_and_safety_aware():
    prompt = coach_chat_prompt()

    assert len(prompt.split()) < 180
    assert "עברית בלבד" in prompt
    assert "אבחון רפואי" in prompt
    assert "coaching_knowledge" in prompt
    assert "אל תטען שאתה מאמן מוסמך" in prompt
    assert "קצרים" in prompt


def test_all_prompt_builders_return_task_specific_text():
    prompts = {
        "workout": workout_generation_prompt(),
        "meal_image": meal_image_prompt(),
        "meal_text": meal_text_prompt(),
        "memory": memory_extraction_prompt(),
        "weekly": weekly_summary_prompt(),
        "safety": safety_classification_prompt(),
    }

    assert "תוכנית אימון מובנית" in prompts["workout"]
    assert "טווחי קלוריות" in prompts["meal_image"]
    assert "פריטי מזון" in prompts["meal_text"]
    assert "עובדות אימון מתמשכות" in prompts["memory"]
    assert "עובדות שמורות" in prompts["weekly"]
    assert "סיכון בטיחותי" in prompts["safety"]


def test_user_facing_prompts_explicitly_forbid_english_output():
    prompts = [
        coach_chat_prompt(),
        workout_generation_prompt(),
        meal_image_prompt(),
        meal_text_prompt(),
        memory_extraction_prompt(),
        weekly_summary_prompt(),
        safety_classification_prompt(),
    ]

    for prompt in prompts:
        assert "עברית בלבד" in prompt
        assert "אל תשתמש באנגלית" in prompt
