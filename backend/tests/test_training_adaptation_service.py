from datetime import date, timedelta

from backend.app.models import WorkoutLog
from backend.app.services.training_adaptation_service import TrainingAdaptationService


def test_training_adaptation_flags_pain_before_progression():
    logs = [
        workout_log(status="completed", pain_flag=True, notes="כאב חד בברך"),
        workout_log(status="completed", pain_flag=False),
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "pain_caution"
    assert summary["pain_flags_recent"] == 1
    assert "כאב" in summary["next_adjustment"]
    assert "וריאציה" in summary["next_adjustment"]


def test_training_adaptation_detects_adherence_risk_from_skips():
    logs = [
        workout_log(status="skipped"),
        workout_log(status="completed"),
        workout_log(status="skipped"),
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "adherence_risk"
    assert summary["skipped_recent"] == 2
    assert "גרסה קצרה" in summary["next_adjustment"]


def test_training_adaptation_allows_small_progression_when_logs_are_stable():
    logs = [
        workout_log(status="completed", rpe=7),
        workout_log(status="completed", rpe=7),
        workout_log(status="completed", rpe=8),
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["completed_recent"] == 3
    assert "משתנה אחד" in summary["next_adjustment"]


def test_training_adaptation_flags_high_effort_recovery_need():
    logs = [
        workout_log(status="completed", rpe=9),
        workout_log(status="completed", rpe=10),
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "recovery_needed"
    assert "RPE" in summary["signals"][0]
    assert "התאוששות" in summary["next_adjustment"]


def test_training_adaptation_uses_structured_completed_sets_for_exercise_progression():
    logs = [
        workout_log(
            status="completed",
            rpe=8,
            exercise_results=[
                {
                    "exercise_name": "Goblet squat",
                    "status": "completed",
                    "sets": [
                        {"set_index": 1, "reps": 12, "completed": True},
                        {"set_index": 2, "reps": 12, "completed": True},
                        {"set_index": 3, "reps": 12, "completed": True},
                    ],
                    "rpe": 8,
                    "rir": 2,
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["exercise_adjustments"][0]["exercise_name"] == "Goblet squat"
    assert summary["exercise_adjustments"][0]["adjustment"] == "small_progression"


def test_training_adaptation_uses_minimum_version_for_partial_structured_log():
    logs = [
        workout_log(
            status="partial",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "partial",
                    "sets": [{"set_index": 1, "reps": 6, "completed": True}],
                    "rpe": 7,
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "adherence_risk"
    assert summary["exercise_adjustments"][0]["adjustment"] == "minimum_version"


def workout_log(
    status: str,
    pain_flag: bool = False,
    notes: str = "",
    rpe: int | None = None,
    exercise_results: list[dict] | None = None,
) -> WorkoutLog:
    return WorkoutLog(
        user_id=1,
        workout_id=None,
        logged_on=date.today() - timedelta(days=1),
        status=status,
        exercise_results=exercise_results or [],
        rpe=rpe,
        notes=notes,
        pain_flag=pain_flag,
        parse_confidence="medium",
    )
