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


def test_structured_workout_plan_rejects_more_than_four_weeks():
    payload = valid_plan()
    payload["duration_weeks"] = 5

    with pytest.raises(ValidationError):
        StructuredWorkoutPlan(**payload)


def test_structured_workout_plan_keeps_planning_decision_metadata():
    payload = valid_plan()
    payload.update(
        {
            "plan_type": "multi_week",
            "training_split": "full_body",
            "experience_level": "beginner",
            "session_length_minutes": 45,
            "safety_notes": ["Stop for sharp pain or unusual dizziness."],
            "decision_inputs": {
                "goal": "improve_strength",
                "equipment": ["dumbbells"],
                "limitations": "none provided",
            },
            "source_refs": [
                "ACSM 2026 resistance training guidelines",
                "CDC adult physical activity guidelines",
            ],
        }
    )
    payload["days"][0].update({"focus": "full_body", "estimated_duration_minutes": 45})
    payload["days"][0]["exercises"][0].update(
        {
            "movement_pattern": "squat",
            "target_muscles": ["quads", "glutes"],
            "progression": "Add reps before load.",
            "regression": "Use a box squat.",
        }
    )

    plan = StructuredWorkoutPlan(**payload)

    assert plan.plan_type == "multi_week"
    assert plan.training_split == "full_body"
    assert plan.days[0].focus == "full_body"
    assert plan.days[0].exercises[0].movement_pattern == "squat"
    assert "ACSM 2026 resistance training guidelines" in plan.source_refs


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
