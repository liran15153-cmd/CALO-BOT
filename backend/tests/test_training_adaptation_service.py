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
    assert "שאלה אחת" in summary["next_adjustment"]
    assert summary["plan_adjustment"]["type"] == "reduce_plan_before_rebuild"
    assert summary["plan_adjustment"]["reduce_days_per_week_by"] == 1
    assert "זמן" in summary["plan_adjustment"]["critical_question"]


def test_training_adaptation_allows_small_progression_when_logs_are_stable():
    logs = [
        workout_log(status="completed", rpe=7),
        workout_log(status="completed", rpe=7),
        workout_log(status="completed", rpe=8),
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["completed_recent"] == 3
    assert summary["progress_evidence"] == "completed_streak"
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
    assert summary["progress_evidence"] == "exercise_log"
    assert summary["exercise_adjustments"][0]["exercise_name"] == "Goblet squat"
    assert summary["exercise_adjustments"][0]["adjustment"] == "small_progression"


def test_training_adaptation_uses_exercise_rir_without_session_rpe_for_progression():
    logs = [
        workout_log(
            status="completed",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "completed",
                    "sets": [
                        {"set_index": 1, "reps": 10, "completed": True},
                        {"set_index": 2, "reps": 10, "completed": True},
                        {"set_index": 3, "reps": 10, "completed": True},
                    ],
                    "rir": 2,
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["progress_evidence"] == "exercise_log"
    assert summary["exercise_adjustments"][0]["exercise_name"] == "Bench press"
    assert summary["exercise_adjustments"][0]["adjustment"] == "small_progression"


def test_training_adaptation_treats_zero_rir_as_recovery_need():
    logs = [
        workout_log(
            status="completed",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rir": 0,
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "recovery_needed"
    assert "RPE/RIR" in summary["signals"][0]
    assert summary["exercise_adjustments"][0]["adjustment"] == "reduce_or_hold"
    assert summary["exercise_adjustments"][0]["reason"] == "near_failure_rir"


def test_training_adaptation_uses_high_rir_as_underload_progression():
    logs = [
        workout_log(
            status="completed",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rir": 5,
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["progress_evidence"] == "exercise_log"
    assert summary["exercise_adjustments"][0]["adjustment"] == "small_progression"
    assert summary["exercise_adjustments"][0]["reason"] == "high_rir_underload"
    assert "RIR 1-3" in summary["exercise_adjustments"][0]["next_action"]


def test_training_adaptation_uses_qualitative_underload_without_fake_rir():
    logs = [
        workout_log(
            status="completed",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "effort_signal": "underloaded",
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["progress_evidence"] == "exercise_log"
    assert summary["exercise_adjustments"][0]["reason"] == "qualitative_underload"
    assert "קל מדי" in summary["exercise_adjustments"][0]["next_action"]
    assert "RIR" not in summary["exercise_adjustments"][0]["next_action"]


def test_training_adaptation_uses_qualitative_controlled_effort_without_fake_metrics():
    logs = [
        workout_log(
            status="completed",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "effort_signal": "controlled",
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "maintain"
    assert "progress_evidence" not in summary
    assert summary["exercise_adjustments"][0]["reason"] == "qualitative_controlled_effort"
    assert summary["exercise_adjustments"][0]["adjustment"] == "maintain"
    assert "בשליטה" in summary["next_adjustment"]
    assert "RPE 1-10" in summary["exercise_adjustments"][0]["next_action"]
    assert "מעלים עומס" in summary["exercise_adjustments"][0]["next_action"]


def test_training_adaptation_treats_qualitative_too_hard_as_recovery_need():
    logs = [
        workout_log(
            status="completed",
            exercise_results=[
                {
                    "exercise_name": "Bench press",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "effort_signal": "too_hard",
                }
            ],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "recovery_needed"
    assert "מאמץ מילולי" in summary["signals"][0]
    assert summary["exercise_adjustments"][0]["reason"] == "qualitative_high_effort"


def test_training_adaptation_accepts_session_rpe_with_explicit_no_pain_as_progression_evidence():
    logs = [workout_log(status="completed", rpe=8, notes="סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב")]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "progress_candidate"
    assert summary["progress_evidence"] == "session_rpe_no_pain"
    assert summary["exercise_adjustments"] == []


def test_training_adaptation_does_not_progress_session_rpe_without_pain_status():
    logs = [workout_log(status="completed", rpe=8, notes="סיימתי את האימון, מאמץ 8 מתוך 10")]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "maintain"


def test_training_adaptation_ignores_invalid_exercise_results_for_progression_evidence():
    logs = [
        workout_log(
            status="completed",
            rpe=8,
            notes="סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב",
            exercise_results=["not-a-result"],
        )
    ]

    summary = TrainingAdaptationService().summarize(logs)

    assert summary["load_signal"] == "maintain"
    assert "progress_evidence" not in summary


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
