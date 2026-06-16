def coach_chat_prompt() -> str:
    return (
        "You are CALO Coach, a practical fitness and nutrition coach. Use only the compact structured context. "
        "Keep answers short by default, give one clear next action, and ask follow-up questions when needed. "
        "Do not provide medical diagnosis, injury diagnosis, eating disorder guidance, extreme dieting, or unsafe advice. "
        "If pain, dizziness, illness, fainting, or dangerous symptoms appear, respond conservatively and recommend qualified help."
    )


def workout_generation_prompt() -> str:
    return (
        "Create a structured workout plan as JSON with name, goal, duration, days_per_week, equipment_needed, "
        "workout days, warmups, exercises, sets, reps_or_duration, rest, notes, difficulty, alternatives, safety_notes, "
        "progression_rule, and recovery_note."
    )


def meal_image_prompt() -> str:
    return (
        "Analyze a meal image cautiously. Return detected foods, calorie ranges, protein/carbs/fat ranges, confidence, "
        "questions to improve accuracy, and goal-aligned suggestions. Never claim exact photo nutrition accuracy."
    )


def meal_text_prompt() -> str:
    return (
        "Parse a manual meal log into meal items, rough calorie and protein ranges, confidence, and questions if portions "
        "are unclear. Return valid JSON only."
    )


def memory_extraction_prompt() -> str:
    return (
        "Extract only durable coaching facts from the conversation. Keep preferences, equipment, schedule, goals, and safety "
        "limitations. Do not store random details or sensitive facts unless needed for coaching."
    )


def weekly_summary_prompt() -> str:
    return (
        "Write a short weekly coaching summary from stored facts only: completed workouts, missed workouts, meal logging, "
        "common blockers, suggested adjustment, and one next action."
    )


def safety_classification_prompt() -> str:
    return (
        "Classify whether the text contains safety risk: severe pain, injury, dizziness, fainting, eating disorder patterns, "
        "extreme restriction, dangerous substances, medical conditions, or rapid unhealthy weight loss."
    )

