import pytest
from pydantic import ValidationError

from backend.app.schemas import StructuredWorkoutPlan


def test_structured_workout_plan_validates_required_shape():
    plan = StructuredWorkoutPlan(**valid_plan())

    assert plan.name == "3 Day Strength"
    assert plan.days[0].exercises[0].name == "Goblet squat"
    assert plan.progression_rule


def test_structured_workout_plan_rejects_day_without_exercises():
    payload = valid_plan()
    payload["days"][0]["exercises"] = []

    with pytest.raises(ValidationError):
        StructuredWorkoutPlan(**payload)


def valid_plan():
    return {
        "name": "3 Day Strength",
        "goal": "improve_strength",
        "duration_weeks": 4,
        "days_per_week": 3,
        "equipment_needed": ["dumbbells"],
        "days": [
            {
                "name": "Day 1 Full Body",
                "warmup": ["5 min brisk walk"],
                "exercises": [
                    {
                        "name": "Goblet squat",
                        "sets": "3",
                        "reps_or_duration": "8-10 reps",
                        "rest": "90 sec",
                        "notes": "Stop if knee pain appears",
                        "difficulty": "moderate",
                        "alternatives": ["Box squat"],
                        "safety_notes": ["Pain-free range only"],
                    }
                ],
                "difficulty": "moderate",
                "notes": "Keep two reps in reserve",
            }
        ],
        "progression_rule": "Increase reps first, then load.",
        "recovery_note": "Add rest if soreness is high.",
    }

