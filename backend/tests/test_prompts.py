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
    assert "medical diagnosis" in prompt
    assert "short" in prompt.lower()


def test_all_prompt_builders_return_task_specific_text():
    prompts = {
        "workout": workout_generation_prompt(),
        "meal_image": meal_image_prompt(),
        "meal_text": meal_text_prompt(),
        "memory": memory_extraction_prompt(),
        "weekly": weekly_summary_prompt(),
        "safety": safety_classification_prompt(),
    }

    assert "structured workout plan" in prompts["workout"]
    assert "calorie ranges" in prompts["meal_image"]
    assert "meal items" in prompts["meal_text"]
    assert "durable coaching facts" in prompts["memory"]
    assert "stored facts" in prompts["weekly"]
    assert "safety risk" in prompts["safety"]

