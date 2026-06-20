from sqlalchemy.orm import sessionmaker

from backend.app.db import init_db, make_engine
from backend.app.models import ChatMessage, ChatSession, UserMemory, WorkoutLog
from backend.app.schemas import OnboardingPayload
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.profile_service import ProfileService


def test_context_builder_uses_compact_context_not_full_chat_history(tmp_path):
    db = make_session(tmp_path)
    profile_service = ProfileService(db)
    profile = profile_service.upsert_onboarding(valid_payload())
    session = ChatSession(user_id=profile.user_id, title="test")
    db.add(session)
    db.commit()
    db.refresh(session)

    for index in range(8):
      db.add(ChatMessage(session_id=session.id, user_id=profile.user_id, role="user", content=f"turn {index}"))
    db.add(UserMemory(user_id=profile.user_id, memory_type="preference", content="User prefers short workouts"))
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, session_id=session.id)

    assert context["profile"]["main_goal"] == "build_muscle"
    assert context["memories"] == ["User prefers short workouts"]
    assert len(context["recent_chat"]) == 4
    assert "turn 0" not in str(context)
    assert "turn 7" in str(context)


def test_context_builder_filters_memories_for_intent(tmp_path):
    db = make_session(tmp_path)
    profile_service = ProfileService(db)
    profile = profile_service.upsert_onboarding(valid_payload())
    db.add_all(
        [
            UserMemory(user_id=profile.user_id, memory_type="equipment", content="User has access to dumbbells"),
            UserMemory(user_id=profile.user_id, memory_type="nutrition", content="User avoids dairy"),
            UserMemory(user_id=profile.user_id, memory_type="schedule", content="User trains after work"),
        ]
    )
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="meal_log")

    assert "User avoids dairy" in context["memories"]
    assert "User has access to dumbbells" not in context["memories"]


def test_context_builder_exposes_sensitive_limitations_as_caution_notes(tmp_path):
    db = make_session(tmp_path)
    profile_service = ProfileService(db)
    profile = profile_service.upsert_onboarding(valid_payload())
    db.add_all(
        [
            UserMemory(
                user_id=profile.user_id,
                memory_type="preference",
                content="המשתמש מעדיף אימונים קצרים",
            ),
            UserMemory(
                user_id=profile.user_id,
                memory_type="safety_limitation",
                content="המשתמש דיווח על רגישות ברך בסקוואט",
                is_sensitive=True,
            ),
        ]
    )
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="general_chat")

    assert "המשתמש מעדיף אימונים קצרים" in context["memories"]
    assert "המשתמש דיווח על רגישות ברך בסקוואט" not in context["memories"]
    assert context["caution_notes"] == ["המשתמש דיווח על רגישות ברך בסקוואט"]


def test_context_builder_includes_compact_coaching_knowledge(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")

    assert context["coaching_knowledge"]["scope"] == "general_wellness_coaching"
    assert any("עקביות" in rule for rule in context["coaching_knowledge"]["rules"])
    assert any("עומס הדרגתי" in item for item in context["coaching_knowledge"]["intent_focus"])
    assert "150-300" in str(context["coaching_knowledge"])
    assert "תכנות אימונים" in context["coaching_knowledge"]["trainer_skill_domains"]
    assert any("FITT" in rule for rule in context["coaching_knowledge"]["programming_model"])
    assert "program_design_summary" in context["coaching_knowledge"]
    assert "technique_cues_summary" in context["coaching_knowledge"]
    assert len(str(context["coaching_knowledge"])) < 8500


def test_context_builder_includes_training_status_from_recent_logs(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())
    db.add_all(
        [
            WorkoutLog(
                user_id=profile.user_id,
                workout_id=None,
                logged_on=__import__("datetime").date.today(),
                status="skipped",
                exercise_results=[],
                rpe=None,
                notes="לא הספקתי",
                pain_flag=False,
                parse_confidence="medium",
            ),
            WorkoutLog(
                user_id=profile.user_id,
                workout_id=None,
                logged_on=__import__("datetime").date.today(),
                status="completed",
                exercise_results=[],
                rpe=9,
                notes="היה קשה מאוד",
                pain_flag=False,
                parse_confidence="medium",
            ),
        ]
    )
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_log")

    assert context["training_status"]["completed_recent"] == 1
    assert context["training_status"]["skipped_recent"] == 1
    assert context["training_status"]["load_signal"] in {"recovery_needed", "adherence_risk"}
    assert context["training_status"]["next_adjustment"]


def test_context_builder_includes_current_workout_plan_metadata(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())
    from backend.app.models import WorkoutPlan

    db.add(
        WorkoutPlan(
            user_id=profile.user_id,
            name="4 Week Strength",
            goal="improve_strength",
            duration_weeks=4,
            days_per_week=4,
            equipment_needed=["dumbbells"],
            plan_json={
                "plan_type": "multi_week",
                "training_split": "upper_lower",
                "experience_level": "intermediate",
                "session_length_minutes": 50,
                "source_refs": ["ACSM 2026 resistance training guidelines: https://acsm.org/resistance-training-guidelines-update-2026/"],
                "decision_inputs": {"duration_weeks": 4},
            },
            progression_rule="Add reps before load.",
            recovery_note="Recover between similar sessions.",
            is_current=True,
        )
    )
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")

    plan = context["current_workout_plan"]
    assert plan["plan_type"] == "multi_week"
    assert plan["duration_weeks"] == 4
    assert plan["training_split"] == "upper_lower"
    assert plan["session_length_minutes"] == 50
    assert plan["source_refs"]


def test_context_builder_includes_program_adaptation_summary_for_workout_log(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_log")
    knowledge = context["coaching_knowledge"]

    assert "program_adaptation_summary" in knowledge
    assert any("משתנה אחד" in item for item in knowledge["program_adaptation_summary"])
    assert any("RPE" in item or "עייפות" in item for item in knowledge["program_adaptation_summary"])
    assert "program_adaptation_protocols" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_sports_nutrition_knowledge_for_meal_intent(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="meal_log")

    nutrition_summary = context["coaching_knowledge"]["sports_nutrition_summary"]
    assert any("1.4-2.0" in item for item in nutrition_summary)
    assert any("פחמימות" in item for item in nutrition_summary)
    assert any("מים" in item or "הידרציה" in item for item in nutrition_summary)
    assert "body_composition_summary" in context["coaching_knowledge"]


def test_context_builder_includes_full_coach_knowledge_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "exercise_prescription_summary" in knowledge
    assert "periodization_summary" in knowledge
    assert "cardiorespiratory_summary" in knowledge
    assert "warmup_mobility_summary" in knowledge
    assert "adherence_coaching_summary" in knowledge
    assert any("FITT-VP" in item for item in knowledge["exercise_prescription_summary"])
    assert any("חסמים" in item for item in knowledge["adherence_coaching_summary"])


def test_context_builder_includes_adherence_summary_for_general_chat(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="general_chat")
    summary = context["coaching_knowledge"]["adherence_coaching_summary"]

    assert any("חסם" in item for item in summary)
    assert any("מעקב" in item or "לוג" in item for item in summary)
    assert "behavior_change_protocols" not in context["coaching_knowledge"]
    assert len(str(context["coaching_knowledge"])) < 7000


def test_context_builder_passes_user_message_to_relevant_knowledge_retrieval(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(
        user_id=profile.user_id,
        intent="general_chat",
        user_message="האם כפיפות בטן באמת מורידות שומן בבטן?",
    )

    knowledge = context["coaching_knowledge"]
    assert "retrieved_knowledge" in knowledge
    assert knowledge["retrieved_knowledge"][0]["topic"] == "common_fitness_myth_protocols.spot_reduction"
    assert "common_fitness_myth_protocols" not in knowledge
    assert len(str(knowledge)) < 7000


def test_context_builder_includes_goal_programming_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "goal_programming_summary" in knowledge
    assert any("כוח" in item and "1-5" in item for item in knowledge["goal_programming_summary"])
    assert any("היפרטרופיה" in item and "6-12" in item for item in knowledge["goal_programming_summary"])
    assert "goal_specific_programming" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_profile_programming_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "profile_programming_summary" in knowledge
    assert any("מתחיל" in item and ("יציבה" in item or "טכניקה" in item) for item in knowledge["profile_programming_summary"])
    assert any("מבוגר" in item and "שיווי" in item for item in knowledge["profile_programming_summary"])
    assert "client_profile_programming" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_limitation_adaptation_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "limitation_adaptation_summary" in knowledge
    assert any("ברך" in item for item in knowledge["limitation_adaptation_summary"])
    assert any("גב" in item for item in knowledge["limitation_adaptation_summary"])
    assert any("כתף" in item for item in knowledge["limitation_adaptation_summary"])
    assert "movement_limitation_adaptations" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_special_population_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "special_population_summary" in knowledge
    assert any("נוער" in item for item in knowledge["special_population_summary"])
    assert any("הריון" in item for item in knowledge["special_population_summary"])
    assert any("כרוני" in item or "מוגבלות" in item for item in knowledge["special_population_summary"])
    assert "special_population_programming" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_instruction_coaching_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "instruction_coaching_summary" in knowledge
    assert any("cue" in item or "קיו" in item for item in knowledge["instruction_coaching_summary"])
    assert any("feedback" in item for item in knowledge["instruction_coaching_summary"])
    assert "coaching_instruction_protocols" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_weekly_structure_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "weekly_structure_summary" in knowledge
    assert any("2-3" in item and ("גוף מלא" in item or "full-body" in item) for item in knowledge["weekly_structure_summary"])
    assert any("upper/lower" in item or "עליון/תחתון" in item for item in knowledge["weekly_structure_summary"])
    assert "weekly_structure_protocols" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_volume_progression_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "volume_progression_summary" in knowledge
    assert any("10" in item and "סטים" in item for item in knowledge["volume_progression_summary"])
    assert any("2-for-2" in item or "2-10%" in item or "2–10%" in item for item in knowledge["volume_progression_summary"])
    assert any("RIR" in item and "RPE" in item for item in knowledge["volume_progression_summary"])
    assert "volume_progression_protocols" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_equipment_substitution_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "equipment_substitution_summary" in knowledge
    summary = knowledge["equipment_substitution_summary"]
    assert any("דפוס" in item and "ציוד" in item for item in summary)
    assert any("משקל גוף" in item and "גומיות" in item for item in summary)
    assert any("קצב" in item and "חד-צדדי" in item for item in summary)
    assert "equipment_substitution_protocols" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_cardio_programming_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "cardio_programming_summary" in knowledge
    assert any("150-300" in item for item in knowledge["cardio_programming_summary"])
    assert any("talk test" in item for item in knowledge["cardio_programming_summary"])
    assert "cardio_programming" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_mobility_balance_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "mobility_balance_summary" in knowledge
    assert any("חימום" in item and "5-10" in item for item in knowledge["mobility_balance_summary"])
    assert any("שיווי" in item for item in knowledge["mobility_balance_summary"])
    assert "mobility_balance_programming" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_assessment_tracking_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    knowledge = context["coaching_knowledge"]

    assert "assessment_tracking_summary" in knowledge
    assert any("baseline" in item for item in knowledge["assessment_tracking_summary"])
    assert any("לוגים" in item for item in knowledge["assessment_tracking_summary"])
    assert "assessment_tracking_protocols" not in knowledge
    assert len(str(knowledge)) < 8500


def test_context_builder_includes_exercise_library_summary_for_workout_plan(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    summary = context["coaching_knowledge"]["exercise_library_summary"]

    assert any("סקוואט" in item for item in summary)
    assert any("דחיפה" in item for item in summary)
    assert any("משיכה" in item for item in summary)
    assert "exercise_library" not in context["coaching_knowledge"]


def test_context_builder_exercise_library_summary_mentions_expanded_patterns(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="workout_plan")
    summary = context["coaching_knowledge"]["exercise_library_summary"]

    assert any("אנכית" in item and "דחיפה" in item for item in summary)
    assert any("אנכית" in item and "משיכה" in item for item in summary)
    assert any("זרועות" in item or "בייספס" in item for item in summary)
    assert "exercise_library" not in context["coaching_knowledge"]
    assert len(str(context["coaching_knowledge"])) < 8500


def make_session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'context.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def valid_payload():
    return OnboardingPayload(
        name="Lior",
        main_goal="build_muscle",
        experience_level="beginner",
        training_location="gym",
        available_equipment=["dumbbells"],
        weekly_availability=3,
        session_length_minutes=45,
        preferred_workout_days=["Monday"],
        coaching_style="direct",
        consent_disclaimer=True,
    )
