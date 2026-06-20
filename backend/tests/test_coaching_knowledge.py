from backend.app.services.coaching_knowledge import (
    CoachingKnowledgeService,
    _BASE_CONTEXT,
    _RETRIEVAL_SKIP_KEYS,
    _iter_knowledge_entries,
    _tokenize,
)


def test_coaching_knowledge_contains_evidence_based_training_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert context["version"] == "2026-06-19"
    assert context["scope"] == "general_wellness_coaching"
    assert any("150-300" in rule for rule in context["rules"])
    assert any("2 ימים" in rule and "קבוצות השרירים" in rule for rule in context["rules"])
    assert any("עקביות" in rule for rule in context["rules"])
    assert any("כאב בחזה" in rule for rule in context["safety_boundaries"])
    assert any(source["organization"] == "ACSM" for source in context["sources"])


def test_coaching_knowledge_returns_intent_specific_focus():
    workout_context = CoachingKnowledgeService().for_intent("workout_plan")
    meal_context = CoachingKnowledgeService().for_intent("meal_log")

    assert any("עומס הדרגתי" in item for item in workout_context["intent_focus"])
    assert any("טווחים" in item for item in meal_context["intent_focus"])
    assert len(workout_context["rules"]) <= 14


def test_coaching_knowledge_contains_trainer_skill_domains_without_claiming_certification():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "הערכה ותשאול" in context["trainer_skill_domains"]
    assert "תכנות אימונים" in context["trainer_skill_domains"]
    assert "שינוי התנהגות והתמדה" in context["trainer_skill_domains"]
    assert any("FITT" in rule for rule in context["programming_model"])
    assert any("רגרסיה" in rule and "פרוגרסיה" in rule for rule in context["progression_regression"])
    assert any("סקוואט" in pattern and "hinge" in pattern for pattern in context["movement_patterns"])
    assert any("שינה" in rule for rule in context["recovery_rules"])
    assert "אינה תחליף להסמכה" in context["professional_scope"][0]


def test_coaching_knowledge_stays_compact_for_provider_context():
    context = CoachingKnowledgeService().for_provider_context("general_chat")

    assert len(str(context)) < 7000
    assert "preparticipation_screening" in context
    assert "goal_playbook_summary" in context
    assert len(context["sources"]) >= 10


def test_workout_provider_context_keeps_prompt_budget_headroom():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    workout_log_context = CoachingKnowledgeService().for_provider_context("workout_log")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "nutrition_coaching_rules" not in workout_context
    assert "nutrition_coaching_rules" not in workout_log_context
    assert "nutrition_coaching_rules" in general_context
    assert "nutrition_coaching_rules" in meal_context
    assert len(str(workout_context)) < 8350
    assert len(str(workout_log_context)) < 8350


def test_coaching_knowledge_contains_goal_and_scenario_playbooks():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "build_muscle" in context["goal_playbooks"]
    assert "improve_strength" in context["goal_playbooks"]
    assert "lose_fat" in context["goal_playbooks"]
    assert "improve_endurance" in context["goal_playbooks"]
    assert any("נפח" in rule for rule in context["goal_playbooks"]["build_muscle"])
    assert any("כבד" in rule or "4-6" in rule for rule in context["goal_playbooks"]["improve_strength"])
    assert any("דיאטת קיצון" in rule for rule in context["goal_playbooks"]["lose_fat"])
    assert "missed_workout" in context["scenario_adjustments"]
    assert "short_time" in context["scenario_adjustments"]
    assert "low_sleep" in context["scenario_adjustments"]
    assert "no_equipment" in context["scenario_adjustments"]
    assert "pain_flag" in context["scenario_adjustments"]


def test_coaching_knowledge_contains_goal_specific_programming_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "goal_specific_programming" in context
    programming = context["goal_specific_programming"]
    for key in [
        "beginner_foundation",
        "strength",
        "hypertrophy",
        "muscular_endurance",
        "power",
        "fat_loss_support",
    ]:
        assert key in programming
        entry = programming[key]
        assert entry["goal"]
        assert entry["set_range"]
        assert entry["rep_range"]
        assert entry["rest_guidance"]
        assert entry["intensity_guidance"]
        assert entry["programming_notes"]

    assert any("12-20" in item for item in programming["beginner_foundation"]["rep_range"])
    assert any("1-5" in item for item in programming["strength"]["rep_range"])
    assert any("6-12" in item for item in programming["hypertrophy"]["rep_range"])
    assert any("12-20" in item for item in programming["muscular_endurance"]["rep_range"])
    assert any("8-10" in item for item in programming["power"]["rep_range"])
    assert any("צעדים" in item or "אירובי" in item for item in programming["fat_loss_support"]["programming_notes"])
    assert any(source["organization"] == "ACSM 2026 Resistance Training Position Stand" for source in context["sources"])
    assert any(source["organization"] == "NASM OPT Model" for source in context["sources"])


def test_coaching_knowledge_contains_client_profile_programming_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "client_profile_programming" in context
    protocols = context["client_profile_programming"]
    for key in [
        "beginner_foundation",
        "intermediate_advanced",
        "older_adult",
        "limited_time",
        "limited_equipment",
        "strength_goal",
        "hypertrophy_goal",
        "fat_loss_goal",
        "endurance_goal",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["entry_point"]
        assert entry["primary_focus"]
        assert entry["programming_rules"]
        assert entry["progression_gate"]
        assert entry["avoid"]

    assert any("12-20" in item or "יציבה" in item for item in protocols["beginner_foundation"]["programming_rules"])
    assert any("מאזן" in item or "שיווי" in item for item in protocols["older_adult"]["programming_rules"])
    assert any("150" in item for item in protocols["older_adult"]["programming_rules"])
    assert any("מורכבים" in item or "מינימום" in item for item in protocols["limited_time"]["programming_rules"])
    assert any("גומיות" in item or "משקל גוף" in item for item in protocols["limited_equipment"]["programming_rules"])
    assert any("80%" in item or "1-5" in item for item in protocols["strength_goal"]["programming_rules"])
    assert any("10 סטים" in item or "6-12" in item for item in protocols["hypertrophy_goal"]["programming_rules"])
    assert any("כוח" in item and "אירובי" in item for item in protocols["fat_loss_goal"]["programming_rules"])
    assert any("talk test" in item or "בסיס אירובי" in item for item in protocols["endurance_goal"]["programming_rules"])
    assert any(source["organization"] == "ACE IFT Program Design" for source in context["sources"])
    assert any(source["organization"] == "CDC Older Adults Physical Activity" for source in context["sources"])
    assert any(source["organization"] == "ACSM Physical Activity Guidelines" for source in context["sources"])


def test_coaching_knowledge_contains_movement_limitation_adaptations():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "movement_limitation_adaptations" in context
    adaptations = context["movement_limitation_adaptations"]
    for key in [
        "joint_pain_general",
        "knee_sensitive_lower_body",
        "low_back_sensitive_training",
        "shoulder_sensitive_push_pull",
        "wrist_sensitive_push_support",
        "ankle_hip_mobility_limited",
    ]:
        assert key in adaptations
        entry = adaptations[key]
        assert entry["signal"]
        assert entry["coaching_goal"]
        assert entry["adjustment_rules"]
        assert entry["exercise_options"]
        assert entry["progression_gate"]
        assert entry["avoid"]

    assert any("טווח תנועה" in item or "התנגדות" in item for item in adaptations["joint_pain_general"]["adjustment_rules"])
    assert any("סקוואט לקופסה" in item or "step-up" in item for item in adaptations["knee_sensitive_lower_body"]["exercise_options"])
    assert any("כאב" in item for item in adaptations["knee_sensitive_lower_body"]["avoid"])
    assert any("low-impact" in item or "השפעה נמוכה" in item for item in adaptations["low_back_sensitive_training"]["adjustment_rules"])
    assert any("glute bridge" in item or "dead bug" in item for item in adaptations["low_back_sensitive_training"]["exercise_options"])
    assert any("rotator cuff" in item or "שכמה" in item for item in adaptations["shoulder_sensitive_push_pull"]["adjustment_rules"])
    assert any("אחיזה ניטרלית" in item or "שיפוע" in item for item in adaptations["wrist_sensitive_push_support"]["adjustment_rules"])
    assert any("עומק" in item or "הגבהת עקב" in item for item in adaptations["ankle_hip_mobility_limited"]["adjustment_rules"])
    assert any(source["organization"] == "ACE Joint Pain Exercise Modifications" for source in context["sources"])
    assert any(source["organization"] == "ACSM/EIM Low Back Pain Activity" for source in context["sources"])
    assert any(source["organization"] == "HSS Shoulder Impingement Exercises" for source in context["sources"])
    assert any(source["organization"] == "NASM Rotator Cuff Corrective Exercise" for source in context["sources"])


def test_coaching_knowledge_contains_exercise_science_foundations():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "exercise_science_foundations" in context
    foundations = context["exercise_science_foundations"]
    for key in [
        "energy_systems",
        "planes_and_patterns",
        "joint_actions_and_levers",
        "force_vector_and_stability",
        "fatigue_and_skill_order",
        "motor_learning_basics",
    ]:
        assert key in foundations
        entry = foundations[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["examples"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("ATP-PC" in item or "phosphagen" in item for item in foundations["energy_systems"]["rules"])
    assert any("גליקוליטי" in item or "glycolytic" in item for item in foundations["energy_systems"]["rules"])
    assert any("אירובי" in item or "aerobic" in item for item in foundations["energy_systems"]["rules"])
    assert any("sagittal" in item and "frontal" in item and "transverse" in item for item in foundations["planes_and_patterns"]["rules"])
    assert any("מנוף" in item or "lever" in item for item in foundations["joint_actions_and_levers"]["rules"])
    assert any("וקטור" in item or "כיוון התנגדות" in item for item in foundations["force_vector_and_stability"]["rules"])
    assert any("עייפות" in item and ("טכניקה" in item or "skill" in item) for item in foundations["fatigue_and_skill_order"]["rules"])
    assert any("external cue" in item or "cue חיצוני" in item for item in foundations["motor_learning_basics"]["rules"])
    assert any(source["organization"] == "ACE Energy Pathways" for source in context["sources"])
    assert any(source["organization"] == "NASM Planes of Motion" for source in context["sources"])
    assert any(source["organization"] == "NASM Squat Biomechanics" for source in context["sources"])


def test_provider_context_projects_exercise_science_compactly_without_full_table():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")

    summary = workout_context["exercise_prescription_summary"]
    assert any("ATP-PC" in item or "גליקוליטי" in item or "אירובי" in item for item in summary)
    assert any("מישורי תנועה" in item or "וקטור" in item for item in summary)
    assert "exercise_science_foundations" not in workout_context
    assert "exercise_prescription_summary" not in general_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_speed_agility_plyometric_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "speed_agility_plyometric_protocols" in context
    protocols = context["speed_agility_plyometric_protocols"]
    for key in [
        "landing_mechanics_foundation",
        "low_level_plyometric_entry",
        "jump_training_progression",
        "sprint_acceleration_exposure",
        "deceleration_change_of_direction",
        "agility_reactive_progression",
        "power_session_order_and_rest",
        "impact_volume_and_surface",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["progression_gate"]
        assert entry["regressions"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("נחיתה" in item and ("ברכ" in item or "שקט" in item or "רכה" in item) for item in protocols["landing_mechanics_foundation"]["rules"])
    assert any("pogo" in item or "skip" in item or "קפיצות נמוכות" in item for item in protocols["low_level_plyometric_entry"]["rules"])
    assert any(("נפח" in item or "גובה" in item or "מגעים" in item) and "אחד" in item for item in protocols["jump_training_progression"]["rules"])
    assert any("האצה" in item or "ספרינט" in item or "sprint" in item for item in protocols["sprint_acceleration_exposure"]["rules"])
    assert any("בלימה" in item and ("שינוי כיוון" in item or "change of direction" in item) for item in protocols["deceleration_change_of_direction"]["rules"])
    assert any("תגובה" in item or "cue" in item or "stimulus" in item for item in protocols["agility_reactive_progression"]["rules"])
    assert any(("לפני עייפות" in item or "תחילת האימון" in item) and ("מנוחה" in item or "rest" in item) for item in protocols["power_session_order_and_rest"]["rules"])
    assert any("משטח" in item or "surface" in item for item in protocols["impact_volume_and_surface"]["rules"])
    assert any(source["organization"] == "NASM Plyometric Technique" for source in context["sources"])
    assert any(source["organization"] == "ACE Plyometric Guidelines" for source in context["sources"])
    assert any(source["organization"] == "Current Concepts of Plyometric Exercise" for source in context["sources"])
    assert any(source["organization"] == "NSCA Acceleration and Deceleration Mechanics" for source in context["sources"])
    assert any(source["organization"] == "NSCA Agility Movement Classification" for source in context["sources"])


def test_provider_context_includes_compact_power_agility_language_without_full_table():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")

    summary = workout_context["exercise_prescription_summary"]
    assert any("ATP-PC" in item and ("קפיצה" in item or "ספרינט" in item) for item in summary)
    assert any("נחיתה" in item or "וקטור" in item for item in summary)
    assert "speed_agility_plyometric_protocols" not in workout_context
    assert "exercise_prescription_summary" not in general_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_special_population_programming():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "special_population_programming" in context
    programming = context["special_population_programming"]
    for key in [
        "youth_resistance_training",
        "pregnancy_postpartum_general",
        "chronic_conditions_disabilities",
        "older_adult_multicomponent",
    ]:
        assert key in programming
        entry = programming[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["programming_rules"]
        assert entry["progression_gate"]
        assert entry["avoid"]

    youth = programming["youth_resistance_training"]
    assert any("60 דקות" in item or "60 minutes" in item for item in youth["programming_rules"])
    assert any("טכניקה" in item and "עומס" in item for item in youth["programming_rules"])
    assert any("1RM" in item or "מקסימ" in item for item in youth["avoid"])

    pregnancy = programming["pregnancy_postpartum_general"]
    assert any("150" in item for item in pregnancy["programming_rules"])
    assert any("שכיבה על הגב" in item or "first trimester" in item for item in pregnancy["avoid"])
    assert any("ספק רפואי" in item or "רופא" in item for item in pregnancy["progression_gate"])

    chronic = programming["chronic_conditions_disabilities"]
    assert any("150" in item for item in chronic["programming_rules"])
    assert any("2 ימים" in item or "2 days" in item for item in chronic["programming_rules"])
    assert any("יכולת" in item for item in chronic["programming_rules"])

    older = programming["older_adult_multicomponent"]
    assert any("שיווי" in item for item in older["programming_rules"])
    assert any("כוח" in item and "אירובי" in item for item in older["programming_rules"])
    assert any(source["organization"] == "CDC Pregnant and Postpartum Physical Activity" for source in context["sources"])
    assert any(source["organization"] == "ODPHP Pregnancy Activity Guidance" for source in context["sources"])
    assert any(source["organization"] == "CDC Chronic Conditions and Disabilities Activity" for source in context["sources"])
    assert any(source["organization"] == "Exercise is Medicine Youth and Older Adult Activity" for source in context["sources"])
    assert any(source["organization"] == "ASCA Youth Resistance Training Position Stand" for source in context["sources"])


def test_coaching_knowledge_contains_menstrual_cycle_training_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "menstrual_cycle_training_protocols" in context
    protocols = context["menstrual_cycle_training_protocols"]
    expected = {
        "symptom_based_autoregulation",
        "cycle_phase_evidence_limits",
        "cycle_tracking_for_coaching",
        "cramps_fatigue_adjustment",
        "low_energy_availability_flags",
    }
    assert expected.issubset(protocols)

    for key in expected:
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["avoid"]

    assert any(
        "סימפטומים" in item and ("RPE" in item or "אנרגיה" in item)
        for item in protocols["symptom_based_autoregulation"]["rules"]
    )
    assert any(
        "אין מספיק ראיות" in item or "לא לבנות" in item
        for item in protocols["cycle_phase_evidence_limits"]["rules"]
    )
    assert any("מחזור" in item and "לוג" in item for item in protocols["cycle_tracking_for_coaching"]["rules"])
    assert any("הליכה" in item or "קל" in item for item in protocols["cramps_fatigue_adjustment"]["rules"])
    assert any("וסת" in item or "מחזור" in item for item in protocols["low_energy_availability_flags"]["rules"])


def test_provider_context_includes_compact_menstrual_cycle_summary_for_general_chat_only():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "menstrual_cycle_summary" in general_context
    summary = general_context["menstrual_cycle_summary"]
    assert any("סימפטומים" in item and ("RPE" in item or "אנרגיה" in item) for item in summary)
    assert any("אין מספיק ראיות" in item or "cycle syncing" in item for item in summary)
    assert any("וסת" in item or "מחזור" in item for item in summary)
    assert "menstrual_cycle_training_protocols" not in general_context
    assert "menstrual_cycle_summary" not in workout_context
    assert "menstrual_cycle_summary" not in meal_context


def test_coaching_knowledge_contains_environment_training_risk_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "environment_training_risk_protocols" in context
    protocols = context["environment_training_risk_protocols"]
    expected = {
        "heat_load_adjustment",
        "heat_acclimatization",
        "heat_illness_red_flags",
        "air_quality_aqi_adjustment",
        "cold_wind_chill_adjustment",
        "outdoor_session_decision",
    }
    assert expected.issubset(protocols)

    for key in expected:
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("עומס חום" in item or "חום" in item for item in protocols["heat_load_adjustment"]["rules"])
    assert any("1-2 שבועות" in item or "1-2" in item for item in protocols["heat_acclimatization"]["rules"])
    assert any("בלבול" in item or "עילפון" in item for item in protocols["heat_illness_red_flags"]["rules"])
    assert any("AQI" in item and ("עצימות" in item or "פנימה" in item) for item in protocols["air_quality_aqi_adjustment"]["rules"])
    assert any("wind chill" in item or "קור" in item for item in protocols["cold_wind_chill_adjustment"]["rules"])
    assert any("להזיז" in item or "בפנים" in item for item in protocols["outdoor_session_decision"]["rules"])
    assert any(source["organization"] == "CDC Heat and Athletes" for source in context["sources"])
    assert any(source["organization"] == "AirNow AQI Outdoor Activity Guidance" for source in context["sources"])
    assert any(source["organization"] == "ACSM Cold Weather Exercise" for source in context["sources"])


def test_provider_context_includes_compact_environment_summary_for_general_chat_only():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "environment_training_summary" in general_context
    summary = general_context["environment_training_summary"]
    assert any("חום" in item and ("צל" in item or "מים" in item) for item in summary)
    assert any("AQI" in item and ("עצימות" in item or "בפנים" in item) for item in summary)
    assert any("wind chill" in item or "קור" in item for item in summary)
    assert "environment_training_risk_protocols" not in general_context
    assert "environment_training_summary" not in workout_context
    assert "environment_training_summary" not in meal_context
    assert len(str(general_context)) < 6500


def test_workout_provider_context_keeps_one_compact_environment_cue_without_new_section():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    workout_log_context = CoachingKnowledgeService().for_provider_context("workout_log")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert any(
        ("חום" in item and "AQI" in item and "קור" in item)
        for item in workout_context["cardio_programming_summary"]
    )
    assert any(
        ("חום" in item and "AQI" in item and "קור" in item)
        for item in workout_log_context["cardio_programming_summary"]
    )
    assert "environment_training_summary" not in workout_context
    assert "environment_training_summary" not in workout_log_context
    assert "environment_training_summary" not in meal_context
    assert len(str(workout_context)) < 8350
    assert len(str(workout_log_context)) < 8350


def test_coaching_knowledge_contains_low_energy_availability_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "low_energy_availability_protocols" in context
    protocols = context["low_energy_availability_protocols"]
    expected = {
        "under_fueling_watchlist",
        "training_recovery_decline",
        "menstrual_bone_stress_risk",
        "disordered_eating_boundary",
        "body_composition_guardrails",
    }
    assert expected.issubset(protocols)

    for key in expected:
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("תדלוק" in item or "אכילה" in item for item in protocols["under_fueling_watchlist"]["rules"])
    assert any("RPE" in item or "ביצועים" in item for item in protocols["training_recovery_decline"]["rules"])
    assert any("וסת" in item or "מחזור" in item for item in protocols["menstrual_bone_stress_risk"]["rules"])
    assert any("לא לאבחן" in item or "לא לתת" in item for item in protocols["disordered_eating_boundary"]["avoid"])
    assert any("גירעון מתון" in item or "תחזוקה" in item for item in protocols["body_composition_guardrails"]["rules"])
    assert any(source["organization"] == "IOC REDs Consensus 2023" for source in context["sources"])
    assert any(source["organization"] == "Nutrition and Athletic Performance Position Paper" for source in context["sources"])
    assert any(source["organization"] == "NEDA Eating Disorder Warning Signs" for source in context["sources"])


def test_provider_context_includes_compact_fueling_risk_guidance_without_prompt_bloat():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    workout_log_context = CoachingKnowledgeService().for_provider_context("workout_log")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")

    assert "fueling_risk_summary" in general_context
    assert any("REDs" in item and "לא לאבחן" in item for item in general_context["fueling_risk_summary"])
    assert any("תדלוק" in item or "אכילה" in item for item in general_context["fueling_risk_summary"])
    assert any("תדלוק" in item or "אכילה" in item for item in workout_log_context["readiness_recovery_summary"])
    assert any("תדלוק" in item or "אכילה" in item for item in meal_context["body_recomposition_summary"])
    assert "low_energy_availability_protocols" not in general_context
    assert "fueling_risk_summary" not in workout_context
    assert "fueling_risk_summary" not in workout_log_context
    assert "fueling_risk_summary" not in meal_context
    assert len(str(general_context)) < 6500
    assert len(str(workout_context)) < 8350
    assert len(str(workout_log_context)) < 8350
    assert len(str(meal_context)) < 5600


def test_coaching_knowledge_contains_coaching_instruction_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "coaching_instruction_protocols" in context
    protocols = context["coaching_instruction_protocols"]
    for key in [
        "session_flow",
        "exercise_teaching",
        "cue_selection",
        "feedback_frequency",
        "technique_safety_checklist",
        "client_feedback_loop",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["coaching_moves"]
        assert entry["progression_gate"]
        assert entry["avoid"]

    assert any("5-10" in item and "חימום" in item for item in protocols["session_flow"]["coaching_moves"])
    assert any("cool" in item or "שחרור" in item for item in protocols["session_flow"]["coaching_moves"])
    assert any("show-tell-do" in item or "הדגם" in item for item in protocols["exercise_teaching"]["coaching_moves"])
    assert any("external" in item and "internal" in item for item in protocols["cue_selection"]["coaching_moves"])
    assert any("פחות feedback" in item or "עצמא" in item for item in protocols["feedback_frequency"]["coaching_moves"])
    assert any("אחיזה" in item or "מנח" in item for item in protocols["technique_safety_checklist"]["coaching_moves"])
    assert any("עייפות" in item or "soreness" in item for item in protocols["client_feedback_loop"]["coaching_moves"])
    assert any(source["organization"] == "NASM Correctly Coaching Exercises" for source in context["sources"])
    assert any(source["organization"] == "NASM Cueing Clients" for source in context["sources"])
    assert any(source["organization"] == "AHA Warm Up Cool Down" for source in context["sources"])
    assert any(source["organization"] == "NSCA Exercise Technique Manual" for source in context["sources"])
    assert any(source["organization"] == "Attentional Focus Resistance Training Review" for source in context["sources"])


def test_coaching_knowledge_contains_exercise_setup_safety_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "exercise_setup_safety_protocols" in context
    protocols = context["exercise_setup_safety_protocols"]
    for key in [
        "machine_adjustment",
        "rack_safety_pins",
        "spotting_free_weights",
        "breathing_bracing",
        "stable_variation_defaults",
        "switch_instead_of_cueing",
        "equipment_misuse_checks",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("מושב" in item and "פד" in item for item in protocols["machine_adjustment"]["rules"])
    assert any("safety pins" in item or "safeties" in item for item in protocols["rack_safety_pins"]["rules"])
    assert any("head" in item or "face" in item or "trunk" in item for item in protocols["spotting_free_weights"]["rules"])
    assert any("brace" in item and ("נשיפה" in item or "exhale" in item) for item in protocols["breathing_bracing"]["rules"])
    assert any("supported" in item or "יציבה" in item for item in protocols["stable_variation_defaults"]["rules"])
    assert any("שני cues" in item or "2 cues" in item for item in protocols["switch_instead_of_cueing"]["rules"])
    assert any("OUT OF ORDER" in item or "כבל" in item for item in protocols["equipment_misuse_checks"]["rules"])
    assert any(source["organization"] == "NSCA Professional Standards" for source in context["sources"])
    assert any(source["organization"] == "NSCA Progressive Teaching Strategies" for source in context["sources"])
    assert any(source["organization"] == "TRUE Fitness Equipment Safety" for source in context["sources"])
    assert any(source["organization"] == "ACE Bodyweight Squat" for source in context["sources"])


def test_coaching_knowledge_contains_weekly_structure_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "weekly_structure_protocols" in context
    protocols = context["weekly_structure_protocols"]
    for key in [
        "availability_first",
        "beginner_full_body",
        "intermediate_upper_lower",
        "advanced_split",
        "recovery_spacing",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["structure_rules"]
        assert entry["progression_gate"]
        assert entry["avoid"]

    assert any("2-3" in item and ("גוף מלא" in item or "full-body" in item) for item in protocols["beginner_full_body"]["structure_rules"])
    assert any("upper/lower" in item or "עליון/תחתון" in item for item in protocols["intermediate_upper_lower"]["structure_rules"])
    assert any("push" in item and "pull" in item and "legs" in item for item in protocols["advanced_split"]["structure_rules"])
    assert any("48" in item or "יומיים" in item for item in protocols["recovery_spacing"]["structure_rules"])
    assert any("פעמיים" in item or "twice" in item for item in protocols["availability_first"]["structure_rules"])
    assert any(source["organization"] == "ACSM Resistance Training Guidelines 2026" for source in context["sources"])
    assert any(source["organization"] == "NSCA Resistance Training Frequency" for source in context["sources"])
    assert any(source["organization"] == "NSCA Guide to Program Design" for source in context["sources"])


def test_coaching_knowledge_contains_volume_progression_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "volume_progression_protocols" in context
    protocols = context["volume_progression_protocols"]
    for key in [
        "minimum_effective_volume",
        "hypertrophy_weekly_sets",
        "double_progression",
        "rir_rpe_autoregulation",
        "progression_decision_order",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["progression_rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]

    assert any("4" in item and "סטים" in item and "שריר" in item for item in protocols["minimum_effective_volume"]["progression_rules"])
    assert any("10" in item and "סטים" in item and "שריר" in item for item in protocols["hypertrophy_weekly_sets"]["progression_rules"])
    assert any("2-for-2" in item or ("2" in item and "שבועות" in item) for item in protocols["double_progression"]["progression_rules"])
    assert any("2-10%" in item or "2–10%" in item for item in protocols["double_progression"]["progression_rules"])
    assert any("RIR" in item and "RPE" in item for item in protocols["rir_rpe_autoregulation"]["progression_rules"])
    assert any("חזרות" in item and "עומס" in item for item in protocols["progression_decision_order"]["progression_rules"])
    assert any(source["organization"] == "ACSM Progression Models in Resistance Training" for source in context["sources"])
    assert any(source["organization"] == "Schoenfeld Weekly Volume Meta-analysis" for source in context["sources"])
    assert any(source["organization"] == "NASM Reps in Reserve" for source in context["sources"])


def test_coaching_knowledge_contains_equipment_substitution_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "equipment_substitution_protocols" in context
    protocols = context["equipment_substitution_protocols"]
    for key in [
        "no_equipment",
        "bands",
        "dumbbells",
        "machines_cables",
        "progression_without_load",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["substitution_rules"]
        assert entry["progression_options"]
        assert entry["avoid"]

    assert any("דפוס" in item and "משקל גוף" in item for item in protocols["no_equipment"]["substitution_rules"])
    assert any("גומ" in item and ("חתירה" in item or "row" in item) for item in protocols["bands"]["substitution_rules"])
    assert any("לחיצת רצפה" in item or "floor press" in item for item in protocols["dumbbells"]["substitution_rules"])
    assert any("סקוואט גביע" in item or "goblet squat" in item for item in protocols["dumbbells"]["substitution_rules"])
    assert any("מכונה" in item and "כבל" in item for item in protocols["machines_cables"]["substitution_rules"])
    assert any("קצב" in item and "חד-צדדי" in item for item in protocols["progression_without_load"]["progression_options"])
    assert any(source["organization"] == "NASM Resistance Training Concepts" for source in context["sources"])
    assert any(source["organization"] == "ACSM Resistance Training Guidelines 2026" for source in context["sources"])
    assert any(source["organization"] == "NSCA Exercise Technique Manual" for source in context["sources"])


def test_coaching_knowledge_contains_session_structure_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "session_structure_protocols" in context
    protocols = context["session_structure_protocols"]
    for key in [
        "exercise_order",
        "rest_intervals",
        "tempo_control",
        "supersets_and_circuits",
        "warmup_ramp_sets",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["structure_rules"]
        assert entry["adjustment_rules"]
        assert entry["avoid"]

    assert any("Power" in item or "כוח מתפרץ" in item for item in protocols["exercise_order"]["structure_rules"])
    assert any("מורכבים" in item and ("עזר" in item or "חד-מפרקי" in item) for item in protocols["exercise_order"]["structure_rules"])
    assert any("2-4" in item or "2-5" in item for item in protocols["rest_intervals"]["structure_rules"])
    assert any("0-90" in item or "0-60" in item for item in protocols["rest_intervals"]["structure_rules"])
    assert any("4/2/1" in item or "tempo" in item for item in protocols["tempo_control"]["structure_rules"])
    assert any("superset" in item or "סופרסט" in item for item in protocols["supersets_and_circuits"]["structure_rules"])
    assert any("ramp" in item or "חימום" in item for item in protocols["warmup_ramp_sets"]["structure_rules"])
    assert any(source["organization"] == "NASM Acute Variables" for source in context["sources"])
    assert any(source["organization"] == "HPRC / NSCA Exercise Order" for source in context["sources"])
    assert any(source["organization"] == "Superset Resistance Training Review" for source in context["sources"])


def test_coaching_knowledge_contains_readiness_recovery_protocols():
    context = CoachingKnowledgeService().for_intent("workout_log")

    assert "readiness_recovery_protocols" in context
    protocols = context["readiness_recovery_protocols"]
    for key in [
        "green_day_progress",
        "yellow_day_adjustment",
        "soreness_doms",
        "sleep_stress_low_readiness",
        "red_flag_boundary",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["signals"]
        assert entry["adjustment_rules"]
        assert entry["avoid"]

    assert any("RPE" in item for item in protocols["green_day_progress"]["signals"])
    assert any("20-40" in item or "20%" in item for item in protocols["yellow_day_adjustment"]["adjustment_rules"])
    assert any("DOMS" in item or "כאבי שרירים" in item for item in protocols["soreness_doms"]["signals"])
    assert any("שינה" in item for item in protocols["sleep_stress_low_readiness"]["signals"])
    assert any("כאב בחזה" in item or "סחרחורת" in item for item in protocols["red_flag_boundary"]["signals"])
    assert any(source["organization"] == "CDC Sleep Basics" for source in context["sources"])
    assert any(source["organization"] == "ACSM Training Load Monitoring" for source in context["sources"])
    assert any(source["organization"] == "NSCA Overtraining and Recovery" for source in context["sources"])
    assert any(source["organization"] == "NASM Overtraining Signs" for source in context["sources"])


def test_provider_context_includes_compact_readiness_recovery_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_log")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "readiness_recovery_summary" in workout_context
    summary = workout_context["readiness_recovery_summary"]
    assert any("RPE" in item and ("התקדמות" in item or "התקדם" in item) for item in summary)
    assert any("שינה" in item or "DOMS" in item or "כאבי שרירים" in item for item in summary)
    assert any("20-40" in item or "נפח" in item for item in summary)
    assert "readiness_recovery_protocols" not in workout_context
    assert "readiness_recovery_summary" not in general_context
    assert "readiness_recovery_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_advanced_recovery_readiness_protocols():
    context = CoachingKnowledgeService().for_intent("workout_log")

    assert "advanced_recovery_readiness_protocols" in context
    protocols = context["advanced_recovery_readiness_protocols"]
    for key in [
        "sleep_debt_adjustment",
        "stress_readiness_adjustment",
        "doms_soreness_decision",
        "illness_return_to_training",
        "travel_disruption_maintenance",
        "overreaching_watchlist",
        "recovery_modality_priorities",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("7" in item or "שינה" in item for item in protocols["sleep_debt_adjustment"]["rules"])
    assert any("20-40" in item for item in protocols["sleep_debt_adjustment"]["rules"])
    assert any("צהוב" in item for item in protocols["stress_readiness_adjustment"]["rules"])
    assert any("DOMS" in item and ("לא" in item or "אינו" in item) for item in protocols["doms_soreness_decision"]["rules"])
    assert any("חום" in item or "fever" in item for item in protocols["illness_return_to_training"]["rules"])
    assert any("צוואר" in item or "neck" in item for item in protocols["illness_return_to_training"]["rules"])
    assert any("maintenance" in item or "מינימום" in item for item in protocols["travel_disruption_maintenance"]["rules"])
    assert any("ביצועים" in item and ("RPE" in item or "שינה" in item) for item in protocols["overreaching_watchlist"]["rules"])
    assert any("שינה" in item and "עומס" in item for item in protocols["recovery_modality_priorities"]["rules"])
    assert any(source["organization"] == "Mayo Clinic Exercise and Illness" for source in context["sources"])
    assert any(source["organization"] == "Cleveland Clinic Activity During Acute Illness" for source in context["sources"])


def test_provider_context_readiness_summary_mentions_recovery_details_without_full_protocols():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_log")

    summary = workout_context["readiness_recovery_summary"]
    assert any("שינה" in item and "סטרס" in item for item in summary)
    assert any("DOMS" in item for item in summary)
    assert any("מחלה" in item or "נסיעה" in item or "maintenance" in item for item in summary)
    assert "advanced_recovery_readiness_protocols" not in workout_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_load_prescription_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "load_prescription_protocols" in context
    protocols = context["load_prescription_protocols"]
    for key in [
        "starting_load_selection",
        "rir_rpe_calibration",
        "set_to_set_adjustment",
        "next_session_load_decision",
        "submax_strength_estimation",
        "heavy_load_safety_gate",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]

    assert any("RIR" in item for item in protocols["starting_load_selection"]["rules"])
    assert any("RPE" in item and "RIR" in item for item in protocols["rir_rpe_calibration"]["rules"])
    assert any("סט" in item and ("עומס" in item or "חזרות" in item) for item in protocols["set_to_set_adjustment"]["rules"])
    assert any("2-10%" in item or "2–10%" in item for item in protocols["next_session_load_decision"]["rules"])
    assert any("e1RM" in item or "1RM" in item for item in protocols["submax_strength_estimation"]["rules"])
    assert any("כאב" in item or "ספוטר" in item or "safety" in item for item in protocols["heavy_load_safety_gate"]["rules"])
    assert any(source["organization"] == "Helms RIR-Based RPE" for source in context["sources"])
    assert any(source["organization"] == "NASM Reps in Reserve" for source in context["sources"])
    assert any(source["organization"] == "Load Prescription Systematic Review" for source in context["sources"])


def test_provider_context_includes_compact_load_prescription_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "load_prescription_summary" in workout_context
    summary = workout_context["load_prescription_summary"]
    assert any("RIR" in item and "עומס" in item for item in summary)
    assert any("RPE" in item and ("שמור" in item or "הורד" in item) for item in summary)
    assert any("2-10%" in item or "קפיצה קטנה" in item for item in summary)
    assert any("e1RM" in item or "1RM" in item for item in summary)
    assert "load_prescription_protocols" not in workout_context
    assert "load_prescription_summary" not in general_context
    assert "load_prescription_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_field_assessment_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "field_assessment_protocols" in context
    protocols = context["field_assessment_protocols"]
    assert "eligibility_screen" in protocols
    screen = protocols["eligibility_screen"]
    assert screen["use_when"]
    assert screen["required_profile_inputs"]
    assert screen["do_not_test_if"]
    assert screen["stop_flags"]
    assert screen["referral_action"]

    for key in [
        "six_minute_walk",
        "two_minute_step",
        "thirty_second_chair_stand",
        "four_stage_balance",
        "timed_up_and_go",
        "movement_snapshot",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["test_id"]
        assert entry["goal"]
        assert entry["equipment"]
        assert entry["instructions"]
        assert entry["record_fields"]
        assert entry["interpretation_rules"]
        assert entry["action_rules"]
        assert entry["retest_window"]
        assert entry["safety_limits"]
        assert entry["source_refs"]

    assert any("6MWT" in item or "6 דקות" in item for item in protocols["six_minute_walk"]["instructions"])
    assert any("2MST" in item or "2 דקות" in item for item in protocols["two_minute_step"]["instructions"])
    assert any("30" in item and "כיסא" in item for item in protocols["thirty_second_chair_stand"]["instructions"])
    assert any("TUG" in item or "Timed Up" in item for item in protocols["timed_up_and_go"]["source_refs"])
    assert any("baseline" in item or "אישי" in item for item in protocols["movement_snapshot"]["interpretation_rules"])
    assert any(source["organization"] == "CDC STEADI" for source in context["sources"])
    assert any(source["organization"] == "ATS Six-Minute Walk Test" for source in context["sources"])


def test_provider_context_includes_compact_field_assessment_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "field_assessment_summary" in workout_context
    summary = workout_context["field_assessment_summary"]
    assert any("1-3" in item and "baseline" in item for item in summary)
    assert any("6MWT" in item or "2MST" in item for item in summary)
    assert any("chair stand" in item or "TUG" in item or "שיווי" in item for item in summary)
    assert any("RPE" in item and ("התקדמות" in item or "הורד" in item) for item in summary)
    assert "field_assessment_protocols" not in workout_context
    assert "field_assessment_summary" not in general_context
    assert "field_assessment_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_concurrent_training_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "concurrent_training_protocols" in context
    protocols = context["concurrent_training_protocols"]
    for key in [
        "general_health_blend",
        "strength_priority",
        "endurance_priority",
        "same_day_order",
        "interference_management",
        "recovery_spacing",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["planning_rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]

    assert any("אירובי" in item and "כוח" in item for item in protocols["general_health_blend"]["planning_rules"])
    assert any("כוח" in item and ("לפני" in item or "קודם" in item) for item in protocols["strength_priority"]["planning_rules"])
    assert any("ריצה" in item or "cycling" in item or "אופניים" in item for item in protocols["interference_management"]["planning_rules"])
    assert any("24" in item or "6" in item or "שעות" in item for item in protocols["recovery_spacing"]["planning_rules"])
    assert any(source["organization"] == "Concurrent Training Interference Meta-analysis" for source in context["sources"])
    assert any(source["organization"] == "Concurrent Training Compatibility Meta-analysis" for source in context["sources"])


def test_provider_context_includes_compact_concurrent_training_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "concurrent_training_summary" in workout_context
    summary = workout_context["concurrent_training_summary"]
    assert any("כוח" in item and "אירובי" in item for item in summary)
    assert any("מטרה" in item and ("קודם" in item or "לפני" in item) for item in summary)
    assert any("ריצה" in item or "אופניים" in item or "impact" in item for item in summary)
    assert "concurrent_training_protocols" not in workout_context
    assert "concurrent_training_summary" not in general_context
    assert "concurrent_training_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_cardio_programming_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "cardio_programming" in context
    cardio = context["cardio_programming"]
    for key in ["base", "aerobic_efficiency", "intervals", "fat_loss_support", "endurance_event"]:
        assert key in cardio
        entry = cardio[key]
        assert entry["goal"]
        assert entry["frequency"]
        assert entry["duration"]
        assert entry["intensity"]
        assert entry["progression"]
        assert entry["coach_notes"]

    assert any("150-300" in item for item in cardio["base"]["duration"])
    assert any("talk test" in item for item in cardio["base"]["intensity"])
    assert any("Zone 1" in item for item in cardio["base"]["intensity"])
    assert any("Zone 2" in item for item in cardio["aerobic_efficiency"]["intensity"])
    assert any("Zone 3" in item for item in cardio["intervals"]["intensity"])
    assert any("70-80" in item for item in cardio["endurance_event"]["coach_notes"])
    assert any(source["organization"] == "ACSM Aerobic Intensity Guidance" for source in context["sources"])
    assert any(source["organization"] == "ACE IFT Cardiorespiratory Training" for source in context["sources"])


def test_coaching_knowledge_contains_walking_running_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "walking_running_protocols" in context
    protocols = context["walking_running_protocols"]
    for key in [
        "beginner_walk_run",
        "easy_run_base",
        "weekly_volume_progression",
        "long_run_management",
        "intervals_and_hills",
        "runner_strength_support",
        "form_cadence_surface",
        "missed_run_adjustment",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["progression_gate"]
        assert entry["adjust_if_hard"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("ריצה-הליכה" in item or "walk-run" in item for item in protocols["beginner_walk_run"]["rules"])
    assert any("talk test" in item or "משפטים קצרים" in item for item in protocols["easy_run_base"]["rules"])
    assert any("נפח ריצה" in item or "קילומטר" in item for item in protocols["weekly_volume_progression"]["rules"])
    assert any("ריצה ארוכה" in item and ("קלה" in item or "Zone" in item) for item in protocols["long_run_management"]["rules"])
    assert any("אינטרוולים" in item or "עליות" in item for item in protocols["intervals_and_hills"]["rules"])
    assert any("כוח" in item and ("רצים" in item or "ריצה" in item) for item in protocols["runner_strength_support"]["rules"])
    assert any("cadence" in item or "קצב צעדים" in item for item in protocols["form_cadence_surface"]["rules"])
    assert any("לא משלימים" in item or "פספוס" in item for item in protocols["missed_run_adjustment"]["rules"])
    assert any("כאב חד" in item or "סחרחורת" in item for item in protocols["missed_run_adjustment"]["avoid"])
    assert any(source["organization"] == "ACSM Distance Running Habits" for source in context["sources"])
    assert any(source["organization"] == "Running Injury Training Parameters Review" for source in context["sources"])
    assert any(source["organization"] == "Brigham and Women's Return to Running" for source in context["sources"])


def test_coaching_knowledge_contains_daily_activity_neat_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "daily_activity_neat_protocols" in context
    protocols = context["daily_activity_neat_protocols"]
    for key in [
        "step_baseline",
        "gradual_step_target",
        "movement_breaks_sedentary_reset",
        "movement_snacks",
        "post_meal_walk",
        "active_errands_and_commute",
        "low_impact_recovery_day",
        "fat_loss_activity_support",
        "calorie_burn_uncertainty",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["progression_gate"]
        assert entry["adjust_if_hard"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("בסיס הצעדים" in item or "baseline" in item for item in protocols["step_baseline"]["rules"])
    assert any("500" in item or "1,000" in item or "1000" in item for item in protocols["gradual_step_target"]["rules"])
    assert any("ישיבה" in item and ("קום" in item or "תנועה" in item) for item in protocols["movement_breaks_sedentary_reset"]["rules"])
    assert any("הפסקות תנועה" in item or "2-3 דקות" in item for item in protocols["movement_snacks"]["rules"])
    assert any("אחרי ארוחה" in item or "ארוחה" in item for item in protocols["post_meal_walk"]["rules"])
    assert any("מדרגות" in item or "תחנה" in item or "שיחת הליכה" in item for item in protocols["active_errands_and_commute"]["rules"])
    assert any("עומס נמוך" in item or "low-impact" in item for item in protocols["low_impact_recovery_day"]["rules"])
    assert any("לא עונש" in item or "קלור" in item for item in protocols["fat_loss_activity_support"]["rules"])
    assert any("לא מדויק" in item or "טווח" in item for item in protocols["calorie_burn_uncertainty"]["rules"])
    assert any(source["organization"] == "ODPHP Move Your Way" for source in context["sources"])
    assert any(source["organization"] == "CDC Benefits of Physical Activity" for source in context["sources"])
    assert any(source["organization"] == "WHO Sedentary Behaviour Guidelines" for source in context["sources"])
    assert any(source["organization"] == "ACSM Sedentary Behaviour" for source in context["sources"])


def test_provider_context_includes_daily_activity_summary_for_general_chat_only():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "daily_activity_summary" in general_context
    summary = general_context["daily_activity_summary"]
    assert any("בסיס צעדים" in item or "baseline" in item for item in summary)
    assert any("500" in item or "1,000" in item or "ישיבה" in item for item in summary)
    assert any("קלור" in item and ("טווח" in item or "לא מדויק" in item) for item in summary)
    assert "daily_activity_neat_protocols" not in general_context
    assert "daily_activity_summary" not in workout_context
    assert "daily_activity_summary" not in meal_context
    assert any("צעדים" in item for item in workout_context["goal_playbook_summary"])
    assert len(str(general_context)) < 7000
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_practical_nutrition_protocols():
    context = CoachingKnowledgeService().for_intent("meal_log")

    assert "practical_nutrition_protocols" in context
    protocols = context["practical_nutrition_protocols"]
    for key in [
        "non_clinical_scope",
        "plate_builder",
        "protein_anchor",
        "fiber_produce_habit",
        "hydration_habit",
        "meal_prep_fallback",
        "pre_post_workout_choices",
        "food_image_uncertainty",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]

    assert any("צלחת" in item and ("חלבון" in item or "ירק" in item) for item in protocols["plate_builder"]["rules"])
    assert any("חלבון" in item and "ארוחה" in item for item in protocols["protein_anchor"]["rules"])
    assert any("סיבים" in item or "ירק" in item or "פרי" in item for item in protocols["fiber_produce_habit"]["rules"])
    assert any("מים" in item and ("אימון" in item or "ארוחה" in item) for item in protocols["hydration_habit"]["rules"])
    assert any("טווח" in item and "ביטחון" in item for item in protocols["food_image_uncertainty"]["rules"])
    assert any(source["organization"] == "USDA MyPlate" for source in context["sources"])
    assert any(source["organization"] == "CDC Water and Healthier Drinks" for source in context["sources"])
    assert any(source["organization"] == "NIH Hydrating for Health" for source in context["sources"])


def test_provider_context_includes_compact_practical_nutrition_summary_for_meals_only():
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")
    image_context = CoachingKnowledgeService().for_provider_context("meal_image")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")

    assert "practical_nutrition_summary" in meal_context
    assert "practical_nutrition_summary" in image_context
    summary = meal_context["practical_nutrition_summary"]
    assert any("צלחת" in item and "חלבון" in item for item in summary)
    assert any("ירק" in item or "פרי" in item or "סיבים" in item for item in summary)
    assert any("מים" in item for item in summary)
    assert any("טווח" in item and "ביטחון" in item for item in summary)
    assert "practical_nutrition_protocols" not in meal_context
    assert "practical_nutrition_summary" not in workout_context
    assert "practical_nutrition_summary" not in general_context
    assert len(str(meal_context)) < 5600


def test_coaching_knowledge_contains_mobility_flexibility_balance_programming():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "mobility_balance_programming" in context
    programming = context["mobility_balance_programming"]
    for key in [
        "dynamic_warmup",
        "mobility_work",
        "static_flexibility",
        "neuromotor_balance",
        "desk_sedentary_reset",
        "older_adult_fall_prevention",
    ]:
        assert key in programming
        entry = programming[key]
        assert entry["goal"]
        assert entry["frequency"]
        assert entry["duration"]
        assert entry["methods"]
        assert entry["intensity_or_quality"]
        assert entry["progression"]
        assert entry["coach_notes"]

    assert any("5-10" in item for item in programming["dynamic_warmup"]["duration"])
    assert any("10-30" in item for item in programming["static_flexibility"]["duration"])
    assert any("2-3" in item for item in programming["static_flexibility"]["frequency"])
    assert any("20-30" in item for item in programming["neuromotor_balance"]["duration"])
    assert any("שיווי" in item for item in programming["neuromotor_balance"]["methods"])
    assert any("תמיכה" in item or "כיסא" in item for item in programming["older_adult_fall_prevention"]["methods"])
    assert any(source["organization"] == "ACSM Flexibility and Neuromotor Guidance" for source in context["sources"])
    assert any(source["organization"] == "CDC Older Adults Balance Guidance" for source in context["sources"])
    assert any(source["organization"] == "Community Guide Older Adult Home Exercise" for source in context["sources"])


def test_coaching_knowledge_contains_warmup_cooldown_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "warmup_cooldown_protocols" in context
    protocols = context["warmup_cooldown_protocols"]
    for key in [
        "pulse_raiser",
        "dynamic_specific_prep",
        "ramp_sets",
        "static_stretching",
        "cooldown",
        "doms_truthfulness",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("5-10" in item for item in protocols["pulse_raiser"]["rules"])
    assert any("dynamic warmup" in item or "דינמי" in item for item in protocols["dynamic_specific_prep"]["rules"])
    assert any("ramp" in item or "סטים" in item for item in protocols["ramp_sets"]["rules"])
    assert any("10-30" in item and ("60" in item or "2-4" in item) for item in protocols["static_stretching"]["rules"])
    assert any("cool-down" in item or "קירור" in item or "שחרור" in item for item in protocols["cooldown"]["rules"])
    assert any("DOMS" in item and ("לא" in item or "אינו" in item) for item in protocols["doms_truthfulness"]["rules"])
    assert any(source["organization"] == "Cochrane Stretching DOMS Review" for source in context["sources"])
    assert any(source["organization"] == "NASM Dynamic Stretching" for source in context["sources"])


def test_provider_context_keeps_warmup_mobility_summary_precise_and_compact():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")

    assert "warmup_mobility_summary" in workout_context
    summary = workout_context["warmup_mobility_summary"]
    assert any("dynamic warmup" in item or "חימום" in item for item in summary)
    assert any("static" in item or "סטטית" in item or "גמישות" in item for item in summary)
    assert any("DOMS" in item or "כאבי שרירים" in item for item in summary)
    assert "warmup_cooldown_protocols" not in workout_context
    assert "warmup_mobility_summary" not in general_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_program_lifecycle_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "program_lifecycle_protocols" in context
    protocols = context["program_lifecycle_protocols"]
    for key in [
        "normal_week",
        "reassessment_cadence",
        "plateau_decision",
        "deload_week",
        "maintenance_week",
        "taper_week",
        "test_week",
        "exercise_change",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("normal week" in item or "שבוע רגיל" in item for item in protocols["normal_week"]["rules"])
    assert any("4-6" in item or "2-4" in item for item in protocols["reassessment_cadence"]["rules"])
    assert any("plateau" in item and ("כמה" in item or "רצף" in item) for item in protocols["plateau_decision"]["rules"])
    assert any("deload" in item and ("volume" in item or "נפח" in item) for item in protocols["deload_week"]["rules"])
    assert any("maintenance" in item or "מינימום" in item for item in protocols["maintenance_week"]["rules"])
    assert any("taper" in item and ("volume" in item or "נפח" in item) for item in protocols["taper_week"]["rules"])
    assert any("test week" in item and ("submax" in item or "RPE" in item) for item in protocols["test_week"]["rules"])
    assert any("תרגיל" in item and ("כאב" in item or "ציוד" in item) for item in protocols["exercise_change"]["rules"])
    assert any(source["organization"] == "NSCA Tapering and Peaking" for source in context["sources"])
    assert any(source["organization"] == "Deloading Strength and Physique Sports Review" for source in context["sources"])
    assert any(source["organization"] == "ACE Strength Plateaus" for source in context["sources"])


def test_provider_context_periodization_summary_mentions_lifecycle_without_full_protocols():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "periodization_summary" in workout_context
    summary = workout_context["periodization_summary"]
    assert any("normal week" in item or "שבוע רגיל" in item for item in summary)
    assert any("deload" in item or "maintenance" in item for item in summary)
    assert any("test week" in item or "taper" in item or "plateau" in item for item in summary)
    assert "program_lifecycle_protocols" not in workout_context
    assert "periodization_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_assessment_and_tracking_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "assessment_tracking_protocols" in context
    protocols = context["assessment_tracking_protocols"]
    for key in [
        "client_intake",
        "baseline_snapshot",
        "movement_assessment",
        "muscular_fitness_testing",
        "cardiorespiratory_testing",
        "body_composition_tracking",
        "progress_review",
        "decision_rules",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["goal"]
        assert entry["use_when"]
        assert entry["measures"]
        assert entry["protocol_notes"]
        assert entry["interpretation"]
        assert entry["follow_up"]

    assert any("מטרה" in item for item in protocols["client_intake"]["measures"])
    assert any("cardiorespiratory" in item or "אירובי" in item for item in protocols["baseline_snapshot"]["measures"])
    assert any("סקוואט" in item for item in protocols["movement_assessment"]["measures"])
    assert any("RPE" in item or "RIR" in item for item in protocols["muscular_fitness_testing"]["protocol_notes"])
    assert any("talk test" in item for item in protocols["cardiorespiratory_testing"]["measures"])
    assert any("היקפים" in item for item in protocols["body_composition_tracking"]["measures"])
    assert any("2-4" in item for item in protocols["progress_review"]["use_when"])
    assert any("התקדם" in item for item in protocols["decision_rules"]["follow_up"])
    assert any("אבחון" in item for item in protocols["movement_assessment"]["interpretation"])
    assert any(source["organization"] == "ACSM Fitness Assessment Manual" for source in context["sources"])
    assert any(source["organization"] == "NASM Movement Assessments" for source in context["sources"])
    assert any(source["organization"] == "ACE Client-Centered Assessments" for source in context["sources"])
    assert any(source["organization"] == "CDC Measuring Physical Activity Intensity" for source in context["sources"])


def test_coaching_knowledge_contains_exercise_selection_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert any(rule["pattern"] == "squat" for rule in context["exercise_selection_rules"])
    squat_rule = next(rule for rule in context["exercise_selection_rules"] if rule["pattern"] == "squat")
    assert "סקוואט לקופסה" in squat_rule["regressions"]
    assert "סקוואט גביע" in squat_rule["progressions"]
    assert any("כאב" in rule for rule in squat_rule["safety"])


def test_coaching_knowledge_contains_preparticipation_screening_and_referral_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "preparticipation_screening" in context
    assert any("כאב בחזה" in item for item in context["preparticipation_screening"]["red_flags"])
    assert any("קוצר נשימה" in item for item in context["preparticipation_screening"]["red_flags"])
    assert any("מצב רפואי" in item for item in context["preparticipation_screening"]["readiness_questions"])
    assert any("תרופות" in item for item in context["preparticipation_screening"]["readiness_questions"])
    assert "referral_rules" in context
    assert any("עצור" in item and "איש מקצוע" in item for item in context["referral_rules"])


def test_coaching_knowledge_contains_program_design_variables_and_deload_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "program_design_variables" in context
    variables = context["program_design_variables"]
    assert any("ניתוח צרכים" in item for item in variables)
    assert any("סדר תרגילים" in item for item in variables)
    assert any("עומס וחזרות" in item for item in variables)
    assert any("מנוחה" in item for item in variables)
    assert any("FITT-VP" in item for item in variables)

    assert "deload_rules" in context
    assert any("ביצועים יורדים" in item for item in context["deload_rules"])
    assert any("אל תעלה" in item and "בבת אחת" in item for item in context["deload_rules"])


def test_coaching_knowledge_contains_technique_cues_for_major_patterns():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "technique_cues" in context
    cues = context["technique_cues"]
    for pattern in ["squat", "hinge", "push", "pull", "core"]:
        assert pattern in cues
        assert cues[pattern]["setup"]
        assert cues[pattern]["execution"]
        assert cues[pattern]["common_errors"]
        assert cues[pattern]["coach_response"]

    assert any("ברכיים" in cue for cue in cues["squat"]["execution"])
    assert any("ירך" in cue or "אגן" in cue for cue in cues["hinge"]["execution"])
    assert any("כתפיים" in cue for cue in cues["push"]["common_errors"])
    assert any("צלעות" in cue or "נשימה" in cue for cue in cues["core"]["setup"])


def test_provider_context_includes_compact_coaching_decision_framework():
    context = CoachingKnowledgeService().for_provider_context("workout_plan")

    assert "program_design_summary" in context
    assert "technique_cues_summary" in context
    assert "deload_rules" in context
    assert any("עומס וחזרות" in item for item in context["program_design_summary"])
    assert any("סקוואט" in item for item in context["technique_cues_summary"])
    assert len(str(context)) < 8500


def test_coaching_knowledge_contains_program_quality_audit_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "program_quality_audit_protocols" in context
    protocols = context["program_quality_audit_protocols"]
    for key in [
        "goal_fit_check",
        "weekly_structure_balance",
        "movement_pattern_coverage",
        "volume_recovery_audit",
        "progression_logic_check",
        "exercise_selection_fit",
        "adherence_feasibility_check",
        "safety_scope_check",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["checks"]
        assert entry["pass_signals"]
        assert entry["adjust_if_missing"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("מטרה" in item and "פרופיל" in item for item in protocols["goal_fit_check"]["checks"])
    assert any("2-3" in item or "תדירות" in item for item in protocols["weekly_structure_balance"]["checks"])
    assert any("squat" in item and "hinge" in item and "push" in item and "pull" in item for item in protocols["movement_pattern_coverage"]["checks"])
    assert any("RPE" in item and "התאוששות" in item for item in protocols["volume_recovery_audit"]["checks"])
    assert any("משתנה אחד" in item or "progressive overload" in item for item in protocols["progression_logic_check"]["checks"])
    assert any("ציוד" in item and "וריאציה" in item for item in protocols["exercise_selection_fit"]["checks"])
    assert any("מינימום" in item or "זמן" in item for item in protocols["adherence_feasibility_check"]["checks"])
    assert any("כאב" in item or "red flag" in item for item in protocols["safety_scope_check"]["checks"])
    assert any("אבחון" in item for item in protocols["safety_scope_check"]["avoid"])
    assert any(source["organization"] == "ACSM 2026 Resistance Training Position Stand" for source in context["sources"])
    assert any(source["organization"] == "ACSM Progression Models in Resistance Training" for source in context["sources"])
    assert any(source["organization"] == "NSCA Guide to Program Design" for source in context["sources"])
    assert any(source["organization"] == "ACE IFT Program Design" for source in context["sources"])


def test_provider_context_includes_compact_program_quality_audit_without_full_table():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")

    summary = workout_context["program_design_summary"]
    assert any("מטרה" in item and "דפוסים" in item and "נפח" in item for item in summary)
    assert any("FITT-VP" in item and ("משתנה אחד" in item or "שינוי אחד" in item) for item in summary)
    assert any("התאוששות" in item or "עקביות" in item for item in summary)
    assert "program_quality_audit_protocols" not in workout_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_load_monitoring_and_population_adjustments():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "load_monitoring_rules" in context
    load_rules = context["load_monitoring_rules"]
    assert any("RPE" in item or "sRPE" in item for item in load_rules)
    assert any("ביצועים" in item for item in load_rules)
    assert any("שינה" in item for item in load_rules)
    assert any("עומס חיצוני" in item and "עומס פנימי" in item for item in load_rules)

    assert "population_adjustments" in context
    adjustments = context["population_adjustments"]
    assert "older_adults" in adjustments
    assert "chronic_conditions" in adjustments
    assert "returning_after_break" in adjustments
    assert "limited_equipment" in adjustments
    assert any("שיווי משקל" in item for item in adjustments["older_adults"])
    assert any("יכולת" in item for item in adjustments["chronic_conditions"])
    assert any("הדרגה" in item for item in adjustments["returning_after_break"])
    assert any("משקל גוף" in item for item in adjustments["limited_equipment"])


def test_coaching_knowledge_contains_program_adaptation_protocols():
    context = CoachingKnowledgeService().for_intent("workout_log")

    assert "program_adaptation_protocols" in context
    protocols = context["program_adaptation_protocols"]
    for key in [
        "progression_candidate",
        "high_effort_or_fatigue",
        "performance_plateau",
        "missed_sessions",
        "exercise_substitution",
        "return_after_break",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["trigger"]
        assert entry["coach_assessment"]
        assert entry["adjustment_options"]
        assert entry["avoid"]
        assert entry["next_check"]

    assert any("משתנה אחד" in item for item in protocols["progression_candidate"]["adjustment_options"])
    assert any("RPE" in item or "sRPE" in item for item in protocols["high_effort_or_fatigue"]["trigger"])
    assert any("ביצועים" in item for item in protocols["performance_plateau"]["trigger"])
    assert any("גרסה קצרה" in item for item in protocols["missed_sessions"]["adjustment_options"])
    assert any("וריאציה" in item for item in protocols["exercise_substitution"]["adjustment_options"])
    assert any("נפח" in item and "נמוך" in item for item in protocols["return_after_break"]["adjustment_options"])
    assert any(source["organization"] == "ACSM Training Load Monitoring" for source in context["sources"])
    assert any(source["organization"] == "NSCA Overtraining and Recovery" for source in context["sources"])
    assert any(source["organization"] == "NASM Overtraining Signs" for source in context["sources"])


def test_provider_context_includes_compact_monitoring_and_population_rules():
    context = CoachingKnowledgeService().for_provider_context("workout_log")

    assert "load_monitoring_summary" in context
    assert "population_adjustment_summary" in context
    assert any("RPE" in item for item in context["load_monitoring_summary"])
    assert any("שיווי משקל" in item for item in context["population_adjustment_summary"])
    assert len(str(context)) < 9500


def test_provider_context_includes_compact_program_adaptation_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_log")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")

    assert "program_adaptation_summary" in workout_context
    summary = workout_context["program_adaptation_summary"]
    assert any("משתנה אחד" in item for item in summary)
    assert any("RPE" in item or "עייפות" in item for item in summary)
    assert any("plateau" in item or "ביצועים" in item for item in summary)
    assert "program_adaptation_protocols" not in workout_context
    assert "program_adaptation_summary" not in general_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_research_backed_sports_nutrition_rules():
    context = CoachingKnowledgeService().for_intent("meal_log")

    assert "sports_nutrition_rules" in context
    assert "protein_guidelines" in context
    assert "carbohydrate_fueling_rules" in context
    assert "hydration_rules" in context
    assert "body_composition_rules" in context
    assert "meal_timing_rules" in context

    assert any("1.4-2.0" in item for item in context["protein_guidelines"])
    assert any("20-40" in item or "0.25" in item for item in context["protein_guidelines"])
    assert any("3-4" in item for item in context["protein_guidelines"])
    assert any("1-4" in item for item in context["carbohydrate_fueling_rules"])
    assert any("פחמימות" in item for item in context["carbohydrate_fueling_rules"])
    assert any("מים" in item or "הידרציה" in item for item in context["hydration_rules"])
    assert any("משקל" in item and "הרכב גוף" in item for item in context["body_composition_rules"])
    assert any("טווח" in item or "הערכה" in item for item in context["sports_nutrition_rules"])
    assert any(source["organization"] == "ISSN" for source in context["sources"])


def test_provider_context_includes_compact_sports_nutrition_summary():
    context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "sports_nutrition_summary" in context
    assert "body_composition_summary" in context
    assert any("1.4-2.0" in item for item in context["sports_nutrition_summary"])
    assert any("פחמימות" in item for item in context["sports_nutrition_summary"])
    assert any("מים" in item or "הידרציה" in item for item in context["sports_nutrition_summary"])
    assert any("הרכב גוף" in item for item in context["body_composition_summary"])
    assert len(str(context)) < 10500


def test_coaching_knowledge_contains_body_composition_strategy_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "body_composition_strategy_protocols" in context
    protocols = context["body_composition_strategy_protocols"]
    for key in [
        "energy_balance_basics",
        "fat_loss_phase",
        "muscle_gain_phase",
        "recomposition_phase",
        "scale_trend_interpretation",
        "measurements_and_non_scale_signals",
        "plateau_review",
        "maintenance_phase",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("מאזן קלורי" in item or "מאזן אנרג" in item for item in protocols["energy_balance_basics"]["rules"])
    assert any("גירעון" in item and ("מתון" in item or "לא" in item) for item in protocols["fat_loss_phase"]["rules"])
    assert any("עודף" in item and ("קטן" in item or "מבוקר" in item) for item in protocols["muscle_gain_phase"]["rules"])
    assert any("ריקומפ" in item or "הרכב גוף" in item for item in protocols["recomposition_phase"]["rules"])
    assert any("ממוצע שבועי" in item or "מגמת משקל" in item for item in protocols["scale_trend_interpretation"]["rules"])
    assert any("היקף" in item or "בגדים" in item or "תמונה" in item for item in protocols["measurements_and_non_scale_signals"]["rules"])
    assert any("פלאטו" in item or "תקיעות" in item for item in protocols["plateau_review"]["rules"])
    assert any("תחזוקה" in item or "diet break" in item for item in protocols["maintenance_phase"]["rules"])
    assert any(source["organization"] == "ISSN Diets and Body Composition" for source in context["sources"])
    assert any(source["organization"] == "NIDDK Body Weight Planner" for source in context["sources"])
    assert any(source["organization"] == "Academy Weight Management Position" for source in context["sources"])


def test_provider_context_includes_body_recomposition_summary_for_general_and_meal_only():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")
    image_context = CoachingKnowledgeService().for_provider_context("meal_image")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")

    for context in [general_context, meal_context, image_context]:
        assert "body_recomposition_summary" in context
        summary = context["body_recomposition_summary"]
        assert any("מאזן קלורי" in item or "גירעון" in item for item in summary)
        assert any("ריקומפ" in item or "חיטוב" in item or "מסה" in item for item in summary)
        assert any("מגמת משקל" in item or "ממוצע שבועי" in item for item in summary)
        assert "body_composition_strategy_protocols" not in context

    assert "body_recomposition_summary" not in workout_context
    assert len(str(general_context)) < 7000
    assert len(str(meal_context)) < 10500
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_supplement_education_protocols():
    context = CoachingKnowledgeService().for_intent("meal_log")

    assert "supplement_education_protocols" in context
    protocols = context["supplement_education_protocols"]
    for key in [
        "creatine_monohydrate",
        "caffeine_preworkout",
        "protein_powder",
        "beta_alanine",
        "electrolytes",
        "low_evidence_high_risk",
        "quality_and_scope",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_position"]
        assert entry["evidence_notes"]
        assert entry["practical_notes"]
        assert entry["caution_notes"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("3-5" in item for item in protocols["creatine_monohydrate"]["practical_notes"])
    assert any("3-6" in item or "mg/kg" in item for item in protocols["caffeine_preworkout"]["practical_notes"])
    assert any("נוחות" in item or "convenience" in item for item in protocols["protein_powder"]["coaching_position"])
    assert any("2-4" in item or "4-6" in item for item in protocols["beta_alanine"]["practical_notes"])
    assert any("proprietary" in item or "תערובת" in item for item in protocols["caffeine_preworkout"]["avoid"])
    assert any("fat burners" in item or "testosterone" in item for item in protocols["low_evidence_high_risk"]["avoid"])
    assert any("third-party" in item or "בדיקת צד שלישי" in item for item in protocols["quality_and_scope"]["practical_notes"])
    assert any(source["organization"] == "ISSN Creatine Position Stand" for source in context["sources"])
    assert any(source["organization"] == "ISSN Caffeine Position Stand" for source in context["sources"])
    assert any(source["organization"] == "ISSN Beta-Alanine Position Stand" for source in context["sources"])
    assert any(source["organization"] == "NIH ODS Exercise Supplements" for source in context["sources"])
    assert any(source["organization"] == "IOC Dietary Supplements Consensus" for source in context["sources"])


def test_provider_context_includes_compact_supplement_summary_for_general_and_meals():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")

    for context in [general_context, meal_context]:
        assert "supplement_education_summary" in context
        summary = context["supplement_education_summary"]
        assert any("optional" in item or "אופציונלי" in item for item in summary)
        assert any("קריאטין" in item and ("3-5" in item or "monohydrate" in item) for item in summary)
        assert any("קפאין" in item and ("3-6" in item or "mg/kg" in item) for item in summary)
        assert any("fat burners" in item or "testosterone" in item for item in summary)
        assert "supplement_education_protocols" not in context

    assert "supplement_education_summary" not in workout_context
    assert len(str(general_context)) < 7000
    assert len(str(meal_context)) < 10500
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_common_fitness_myth_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "common_fitness_myth_protocols" in context
    protocols = context["common_fitness_myth_protocols"]
    for key in [
        "spot_reduction",
        "soreness_and_quality",
        "sweat_and_fat_loss",
        "fasted_cardio",
        "strength_training_bulky_fear",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["user_claims"]
        assert entry["coach_position"]
        assert entry["what_to_do_instead"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("שומן נקודתי" in item or "spot reduction" in item for item in protocols["spot_reduction"]["coach_position"])
    assert any("DOMS" in item and "מדד" in item for item in protocols["soreness_and_quality"]["coach_position"])
    assert any("זיעה" in item and "מים" in item for item in protocols["sweat_and_fat_loss"]["coach_position"])
    assert any("fasted cardio" in item and "לא עדיף" in item for item in protocols["fasted_cardio"]["coach_position"])
    assert any("כוח" in item and "נשים" in item for item in protocols["strength_training_bulky_fear"]["coach_position"])
    assert any(source["organization"] == "Abdominal Exercise Spot Reduction Trial" for source in context["sources"])
    assert any(source["organization"] == "Fasted Exercise Body Composition Review" for source in context["sources"])
    assert any(source["organization"] == "NSCA Resistance Training for Women" for source in context["sources"])


def test_provider_context_includes_compact_fitness_myth_summary_for_general_only():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "fitness_myths_summary" in general_context
    summary = general_context["fitness_myths_summary"]
    assert any("שומן נקודתי" in item or "spot reduction" in item for item in summary)
    assert any("DOMS" in item and "איכות" in item for item in summary)
    assert any("fasted cardio" in item or "זיעה" in item for item in summary)
    assert "common_fitness_myth_protocols" not in general_context
    assert "fitness_myths_summary" not in workout_context
    assert "fitness_myths_summary" not in meal_context
    assert len(str(general_context)) < 7000
    assert len(str(workout_context)) < 8500
    assert len(str(meal_context)) < 10500


def test_provider_context_retrieves_relevant_protocol_from_user_query_without_full_table():
    context = CoachingKnowledgeService().for_provider_context(
        "general_chat",
        query="האם כפיפות בטן יורידו לי שומן בבטן או שזה מיתוס?",
    )

    assert "retrieved_knowledge" in context
    hit = context["retrieved_knowledge"][0]
    assert hit["topic"] == "common_fitness_myth_protocols.spot_reduction"
    assert any("שומן נקודתי" in item or "spot reduction" in item for item in hit["guidance"])
    assert any("כוח" in item or "צעדים" in item for item in hit["action"])
    assert "common_fitness_myth_protocols" not in context
    assert len(str(context)) < 7000


def test_workout_provider_context_retrieves_specific_protocol_and_preserves_budget():
    context = CoachingKnowledgeService().for_provider_context(
        "workout_plan",
        query="יש לי רק גומייה ומשקל גוף. איך להחליף חתירה ולחיצה בלי לאבד את המטרה?",
    )

    hits = context["retrieved_knowledge"]
    assert any(hit["topic"].startswith("equipment_substitution_protocols") for hit in hits)
    assert any("דפוס" in item or "ציוד" in item for hit in hits for item in hit["guidance"])
    assert "equipment_substitution_protocols" not in context
    assert len(str(context)) < 8500


def test_provider_context_does_not_retrieve_from_intent_boost_without_query_match():
    context = CoachingKnowledgeService().for_provider_context(
        "workout_plan",
        query="איך לחלק שבוע אימונים מאוזן עם מספיק מנוחה?",
    )

    hits = context.get("retrieved_knowledge", [])
    assert not any(hit["topic"].startswith("equipment_substitution_protocols") for hit in hits)


def test_coaching_knowledge_contains_full_coach_prescription_and_adherence_rules():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "exercise_prescription_principles" in context
    assert "periodization_rules" in context
    assert "cardiorespiratory_training_rules" in context
    assert "warmup_mobility_rules" in context
    assert "assessment_reassessment_rules" in context
    assert "adherence_coaching_rules" in context

    assert any("FITT-VP" in item for item in context["exercise_prescription_principles"])
    assert any("ספציפיות" in item and "עומס יתר" in item for item in context["exercise_prescription_principles"])
    assert any("מיקרו" in item or "מזו" in item for item in context["periodization_rules"])
    assert any("150-300" in item and "75-150" in item for item in context["cardiorespiratory_training_rules"])
    assert any("talk test" in item or "RPE" in item for item in context["cardiorespiratory_training_rules"])
    assert any("חימום" in item and "ספציפי" in item for item in context["warmup_mobility_rules"])
    assert any("SMART" in item for item in context["adherence_coaching_rules"])
    assert any("חסמים" in item for item in context["adherence_coaching_rules"])
    assert any("הערכה מחדש" in item or "לוגים" in item for item in context["assessment_reassessment_rules"])
    assert any(source["organization"] == "ACSM Guidelines for Exercise Testing and Prescription" for source in context["sources"])
    assert any(source["organization"] == "ACE IFT / Mover Method" for source in context["sources"])


def test_coaching_knowledge_contains_behavior_change_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "behavior_change_protocols" in context
    protocols = context["behavior_change_protocols"]
    for key in [
        "abc_conversation",
        "barrier_problem_solving",
        "action_plan",
        "self_monitoring_feedback",
        "social_support",
        "relapse_recovery",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["goal"]
        assert entry["use_when"]
        assert entry["coach_moves"]
        assert entry["avoid"]
        assert entry["next_action"]

    assert any("פתוחה" in item for item in protocols["abc_conversation"]["coach_moves"])
    assert any("חסם" in item for item in protocols["barrier_problem_solving"]["coach_moves"])
    assert any("אם" in item and "אז" in item for item in protocols["action_plan"]["coach_moves"])
    assert any("לוג" in item or "מעקב" in item for item in protocols["self_monitoring_feedback"]["coach_moves"])
    assert any("תמיכה" in item for item in protocols["social_support"]["coach_moves"])
    assert any("חזרה" in item or "פספוס" in item for item in protocols["relapse_recovery"]["coach_moves"])
    assert any(source["organization"] == "CDC Physical Activity Behavior Supports" for source in context["sources"])
    assert any(source["organization"] == "Community Guide Behavior Change Programs" for source in context["sources"])
    assert any(source["organization"] == "ACSM CPT Behavior Change Competencies" for source in context["sources"])
    assert any(source["organization"] == "NCI Implementation Intentions" for source in context["sources"])


def test_provider_context_includes_compact_full_coach_summaries_for_workout_plan():
    context = CoachingKnowledgeService().for_provider_context("workout_plan")

    assert "exercise_prescription_summary" in context
    assert "periodization_summary" in context
    assert "cardiorespiratory_summary" in context
    assert "warmup_mobility_summary" in context
    assert "adherence_coaching_summary" in context
    assert any("FITT-VP" in item for item in context["exercise_prescription_summary"])
    assert any("מזו" in item or "מיקרו" in item for item in context["periodization_summary"])
    assert any("talk test" in item or "RPE" in item for item in context["cardiorespiratory_summary"])
    assert any("חימום" in item for item in context["warmup_mobility_summary"])
    assert any("חסמים" in item for item in context["adherence_coaching_summary"])
    assert len(str(context)) < 9500


def test_provider_context_includes_compact_adherence_summary_for_general_chat():
    context = CoachingKnowledgeService().for_provider_context("general_chat")

    assert "adherence_coaching_summary" in context
    summary = context["adherence_coaching_summary"]
    assert any("ABC" in item or "פתוחה" in item for item in summary)
    assert any("חסם" in item for item in summary)
    assert any("מעקב" in item or "לוג" in item for item in summary)
    assert "behavior_change_protocols" not in context
    assert len(str(context)) < 7000


def test_coaching_knowledge_contains_adherence_micro_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "adherence_micro_protocols" in context
    protocols = context["adherence_micro_protocols"]
    for key in [
        "motivational_interviewing_oars",
        "barrier_to_plan",
        "implementation_intention",
        "minimum_viable_workout",
        "self_monitoring_feedback",
        "relapse_recovery",
        "autonomy_choice",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]

    assert any("OARS" in item or "פתוחה" in item for item in protocols["motivational_interviewing_oars"]["rules"])
    assert any("חסם" in item and ("זמן" in item or "אנרגיה" in item) for item in protocols["barrier_to_plan"]["rules"])
    assert any("אם" in item and "אז" in item for item in protocols["implementation_intention"]["rules"])
    assert any("2-10" in item or "מינימום" in item for item in protocols["minimum_viable_workout"]["rules"])
    assert any("לוג" in item and ("הבא" in item or "התאמה" in item) for item in protocols["self_monitoring_feedback"]["rules"])
    assert any("פספוס" in item and "עונש" in item for item in protocols["relapse_recovery"]["avoid"])
    assert any("אפשרויות" in item or "בחירה" in item for item in protocols["autonomy_choice"]["rules"])
    assert any(source["organization"] == "Motivational Interviewing Network of Trainers" for source in context["sources"])
    assert any(source["organization"] == "Self-Determination Theory Exercise Review" for source in context["sources"])


def test_provider_context_includes_adherence_micro_summary_for_general_chat_only():
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "adherence_micro_summary" in general_context
    summary = general_context["adherence_micro_summary"]
    assert any("OARS" in item or "פתוחה" in item for item in summary)
    assert any("חסם" in item for item in summary)
    assert any("אם-אז" in item or "מינימום" in item for item in summary)
    assert any("אפשרויות" in item or "בחירה" in item for item in summary)
    assert "adherence_micro_protocols" not in general_context
    assert "adherence_micro_summary" not in workout_context
    assert "adherence_micro_summary" not in meal_context
    assert len(str(general_context)) < 7000


def test_coaching_knowledge_contains_hebrew_coach_language_protocols():
    context = CoachingKnowledgeService().for_intent("general_chat")

    assert "hebrew_coaching_language_protocols" in context
    protocols = context["hebrew_coaching_language_protocols"]
    for key in [
        "terminology_register",
        "response_shape",
        "plain_language_autonomy",
        "jargon_policy",
        "correction_patterns",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["examples"]
        assert entry["avoid"]
        assert entry["source_refs"]

    terminology_rules = protocols["terminology_register"]["rules"]
    assert any("RPE" in item and "1" in item and "10" in item for item in terminology_rules)
    assert any("RIR" in item and "חזרות" in item for item in terminology_rules)
    assert any("DOMS" in item and "כאבי שרירים" in item for item in terminology_rules)
    assert any("רפס" in item and "חזרות" in item for item in terminology_rules)
    assert any("סטים" in item and "חזרות" in item and "מערכות" in item for item in terminology_rules)
    assert any("דילואד" in item and "הורדת עומס" in item for item in protocols["jargon_policy"]["rules"])
    assert any("progressive overload" in item and "התקדמות הדרגתית" in item for item in protocols["jargon_policy"]["rules"])
    assert any("פעולה אחת" in item for item in protocols["response_shape"]["rules"])
    assert any("אפשר" in item or "נבחר" in item for item in protocols["plain_language_autonomy"]["examples"])
    assert any("Zone 2" in item and "לדבר" in item for item in protocols["jargon_policy"]["rules"])
    assert any("לא קרה כלום" in item or "לא להחזיר" in item for item in protocols["correction_patterns"]["examples"])
    assert any(source["organization"] == "CDC Plain Language" for source in context["sources"])
    assert any(source["organization"] == "CDC Plain Writing" for source in context["sources"])
    assert any(source["organization"] == "Motivational Interviewing Network of Trainers" for source in context["sources"])


def test_provider_context_includes_compact_hebrew_language_guidance():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    for context in [workout_context, general_context, meal_context]:
        behavior = context["coaching_behavior"]
        assert any("עברית ישראלית טבעית" in item and ("RPE" in item or "DOMS" in item) for item in behavior)
        assert any("סטים" in item and "חזרות" in item and "מערכות" in item for item in behavior)
        assert any("דילואד" in item and "progressive overload" in item for item in behavior)
        assert any("bullet" in item for item in behavior)
        assert any("פעולה אחת" in item for item in behavior)
        assert any("אשמה" in item or "חובה" in item for item in behavior)
        assert "hebrew_coaching_language_protocols" not in context

    assert len(str(workout_context)) < 8500
    assert len(str(general_context)) < 7000
    assert len(str(meal_context)) < 10500


def test_provider_context_includes_compact_goal_programming_summary():
    context = CoachingKnowledgeService().for_provider_context("workout_plan")

    assert "goal_programming_summary" in context
    summary = context["goal_programming_summary"]
    assert any("כוח" in item and "1-5" in item for item in summary)
    assert any("היפרטרופיה" in item and "6-12" in item for item in summary)
    assert any("סבולת" in item and "12-20" in item for item in summary)
    assert any("כוח מתפרץ" in item or "Power" in item for item in summary)
    assert len(str(context)) < 8500


def test_provider_context_includes_compact_profile_programming_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "profile_programming_summary" in workout_context
    summary = workout_context["profile_programming_summary"]
    assert any("מתחיל" in item and ("יציבה" in item or "טכניקה" in item) for item in summary)
    assert any("מבוגר" in item and "שיווי" in item for item in summary)
    assert any("זמן" in item or "ציוד" in item for item in summary)
    assert any("כוח" in item and "היפרטרופיה" in item for item in summary)
    assert "client_profile_programming" not in workout_context
    assert "profile_programming_summary" not in general_context
    assert "profile_programming_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_limitation_adaptation_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "limitation_adaptation_summary" in workout_context
    summary = workout_context["limitation_adaptation_summary"]
    assert any("ברך" in item and ("טווח" in item or "סקוואט לקופסה" in item) for item in summary)
    assert any("גב" in item and ("low-impact" in item or "ליבה" in item) for item in summary)
    assert any("כתף" in item and ("שכמה" in item or "rotator cuff" in item) for item in summary)
    assert "movement_limitation_adaptations" not in workout_context
    assert "limitation_adaptation_summary" not in general_context
    assert "limitation_adaptation_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_special_population_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "special_population_summary" in workout_context
    summary = workout_context["special_population_summary"]
    assert any("נוער" in item and ("טכניקה" in item or "60" in item) for item in summary)
    assert any("הריון" in item and "150" in item for item in summary)
    assert any("כרוני" in item or "מוגבלות" in item for item in summary)
    assert "special_population_programming" not in workout_context
    assert "special_population_summary" not in general_context
    assert "special_population_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_instruction_coaching_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "instruction_coaching_summary" in workout_context
    summary = workout_context["instruction_coaching_summary"]
    assert any("cue" in item or "קיו" in item for item in summary)
    assert any("feedback" in item and ("פחות" in item or "בטיחות" in item) for item in summary)
    assert any("חימום" in item and ("שחרור" in item or "cool" in item) for item in summary)
    assert "coaching_instruction_protocols" not in workout_context
    assert "instruction_coaching_summary" not in general_context
    assert "instruction_coaching_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_instruction_summary_includes_setup_safety_without_full_protocols():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")

    summary = workout_context["instruction_coaching_summary"]
    assert any("setup" in item or "כוון" in item for item in summary)
    assert any("safety pins" in item or "safeties" in item for item in summary)
    assert any("brace" in item or "נשיפה" in item for item in summary)
    assert "exercise_setup_safety_protocols" not in workout_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_weekly_structure_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "weekly_structure_summary" in workout_context
    summary = workout_context["weekly_structure_summary"]
    assert any("2-3" in item and ("גוף מלא" in item or "full-body" in item) for item in summary)
    assert any("upper/lower" in item or "עליון/תחתון" in item for item in summary)
    assert any("push" in item and "pull" in item and "legs" in item for item in summary)
    assert any("פעמיים" in item or "twice" in item for item in summary)
    assert "weekly_structure_protocols" not in workout_context
    assert "weekly_structure_summary" not in general_context
    assert "weekly_structure_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_volume_progression_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "volume_progression_summary" in workout_context
    summary = workout_context["volume_progression_summary"]
    assert any("10" in item and "סטים" in item for item in summary)
    assert any("2-for-2" in item or "2-10%" in item or "2–10%" in item for item in summary)
    assert any("RIR" in item and "RPE" in item for item in summary)
    assert "volume_progression_protocols" not in workout_context
    assert "volume_progression_summary" not in general_context
    assert "volume_progression_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_advanced_strength_hypertrophy_protocols():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "advanced_strength_hypertrophy_protocols" in context
    protocols = context["advanced_strength_hypertrophy_protocols"]
    for key in [
        "hypertrophy_volume_landmarks",
        "proximity_to_failure",
        "failure_dosage",
        "top_set_backoff",
        "specialization_phase",
        "plateau_troubleshooting_ladder",
        "exercise_rotation_specificity",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["coaching_goal"]
        assert entry["rules"]
        assert entry["decision_gate"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("10" in item and "סטים" in item for item in protocols["hypertrophy_volume_landmarks"]["rules"])
    assert any("6-10" in item and ("סטים קשים" in item or "hard" in item) for item in protocols["hypertrophy_volume_landmarks"]["rules"])
    assert any("פעמיים" in item or "2x" in item for item in protocols["hypertrophy_volume_landmarks"]["rules"])
    assert any("8-20" in item or "12-30" in item for item in protocols["hypertrophy_volume_landmarks"]["rules"])
    assert any("1-3 RIR" in item or "1-3" in item for item in protocols["proximity_to_failure"]["rules"])
    assert any("failure" in item and ("בטוח" in item or "isolation" in item) for item in protocols["failure_dosage"]["rules"])
    assert any("top set" in item and ("back-off" in item or "backoff" in item) for item in protocols["top_set_backoff"]["rules"])
    assert any("specialization" in item and ("זמני" in item or "בלוק" in item) for item in protocols["specialization_phase"]["rules"])
    assert any("עקביות" in item and "שינה" in item for item in protocols["plateau_troubleshooting_ladder"]["rules"])
    assert any("specificity" in item or "ספציפיות" in item for item in protocols["exercise_rotation_specificity"]["rules"])
    assert any(source["organization"] == "Hypertrophy Volume Meta-analysis" for source in context["sources"])
    assert any(source["organization"] == "Training to Failure Meta-analysis" for source in context["sources"])
    assert any(source["organization"] == "Loading Recommendations Review" for source in context["sources"])
    assert any(source["organization"] == "ACSM Progression Models in Resistance Training" for source in context["sources"])


def test_provider_context_volume_summary_mentions_advanced_hypertrophy_without_full_protocols():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")

    summary = workout_context["volume_progression_summary"]
    assert any("failure" in item or "כשל" in item for item in summary)
    assert any("specialization" in item or "plateau" in item for item in summary)
    assert any("RIR" in item and "RPE" in item for item in summary)
    assert "advanced_strength_hypertrophy_protocols" not in workout_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_equipment_substitution_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "equipment_substitution_summary" in workout_context
    summary = workout_context["equipment_substitution_summary"]
    assert any("דפוס" in item and "ציוד" in item for item in summary)
    assert any("משקל גוף" in item and "גומיות" in item for item in summary)
    assert any("משקולות יד" in item or "dumbbell" in item for item in summary)
    assert any("קצב" in item and "חד-צדדי" in item for item in summary)
    assert "equipment_substitution_protocols" not in workout_context
    assert "equipment_substitution_summary" not in general_context
    assert "equipment_substitution_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_session_structure_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "session_structure_summary" in workout_context
    summary = workout_context["session_structure_summary"]
    assert any("Power" in item or "מורכבים" in item for item in summary)
    assert any("2-4" in item or "2-5" in item for item in summary)
    assert any("0-90" in item or "0-60" in item for item in summary)
    assert any("superset" in item or "סופרסט" in item for item in summary)
    assert "session_structure_protocols" not in workout_context
    assert "session_structure_summary" not in general_context
    assert "session_structure_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_limits_goal_programming_summary_to_workout_intents():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_log")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")
    general_context = CoachingKnowledgeService().for_provider_context("general_chat")

    assert "goal_programming_summary" in workout_context
    assert "goal_programming_summary" not in meal_context
    assert "goal_programming_summary" not in general_context


def test_provider_context_includes_compact_cardio_programming_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "cardio_programming_summary" in workout_context
    summary = workout_context["cardio_programming_summary"]
    assert any("150-300" in item for item in summary)
    assert any("ריצה-הליכה" in item or "walk-run" in item for item in summary)
    assert any("talk test" in item for item in summary)
    assert any("נפח ריצה" in item or "קילומטר" in item for item in summary)
    assert any("Zone 2" in item for item in summary)
    assert any("Zone 3" in item or "עליות" in item for item in summary)
    assert "cardio_programming" not in workout_context
    assert "walking_running_protocols" not in workout_context
    assert "cardio_programming_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_mobility_balance_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "mobility_balance_summary" in workout_context
    summary = workout_context["mobility_balance_summary"]
    assert any("5-10" in item and "חימום" in item for item in summary)
    assert any("10-30" in item and "גמישות" in item for item in summary)
    assert any("שיווי" in item and "2-3" in item for item in summary)
    assert "mobility_balance_programming" not in workout_context
    assert "mobility_balance_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_provider_context_includes_compact_assessment_tracking_summary_for_workouts_only():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_plan")
    meal_context = CoachingKnowledgeService().for_provider_context("meal_log")

    assert "assessment_tracking_summary" in workout_context
    summary = workout_context["assessment_tracking_summary"]
    assert any("baseline" in item and "מטרה" in item for item in summary)
    assert any("movement" in item or "תנועה" in item for item in summary)
    assert any("2-4" in item and "לוגים" in item for item in summary)
    assert "assessment_tracking_protocols" not in workout_context
    assert "assessment_tracking_summary" not in meal_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_progress_measurement_protocols():
    context = CoachingKnowledgeService().for_intent("workout_log")

    assert "progress_measurement_protocols" in context
    protocols = context["progress_measurement_protocols"]
    for key in [
        "goal_metric_selection",
        "strength_progress",
        "cardio_progress",
        "body_composition_trends",
        "adherence_dashboard_review",
        "reassessment_decision",
    ]:
        assert key in protocols
        entry = protocols[key]
        assert entry["use_when"]
        assert entry["measures"]
        assert entry["interpretation"]
        assert entry["decision_rules"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("baseline" in item and "מטרה" in item for item in protocols["goal_metric_selection"]["measures"])
    assert any("חזרות" in item and ("RPE" in item or "RIR" in item) for item in protocols["strength_progress"]["measures"])
    assert any("talk test" in item or "RPE" in item for item in protocols["cardio_progress"]["measures"])
    assert any("משקל" in item and "מגמה" in item for item in protocols["body_composition_trends"]["interpretation"])
    assert any("next action" in item or "פעולה" in item for item in protocols["adherence_dashboard_review"]["decision_rules"])
    assert any("2-4" in item for item in protocols["reassessment_decision"]["decision_rules"])
    assert any(source["organization"] == "ACSM Fitness Assessment Manual" for source in context["sources"])
    assert any(source["organization"] == "ACE Client-Centered Assessments" for source in context["sources"])
    assert any(source["organization"] == "CDC Physical Activity Tracking" for source in context["sources"])
    assert any(source["organization"] == "Resistance Training Monitoring Review" for source in context["sources"])


def test_provider_context_assessment_summary_includes_goal_metrics_without_full_protocols():
    workout_context = CoachingKnowledgeService().for_provider_context("workout_log")

    summary = workout_context["assessment_tracking_summary"]
    assert any("כוח" in item and "אירובי" in item for item in summary)
    assert any("היקפים" in item or "משקל" in item for item in summary)
    assert any("מגמה" in item or "trend" in item for item in summary)
    assert any("פעולה" in item or "next action" in item for item in summary)
    assert "progress_measurement_protocols" not in workout_context
    assert len(str(workout_context)) < 8500


def test_coaching_knowledge_contains_structured_exercise_library():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "exercise_library" in context
    library = context["exercise_library"]
    for key in [
        "squat",
        "hip_hinge",
        "horizontal_push",
        "horizontal_pull",
        "lunge",
        "core_anti_extension",
        "loaded_carry",
    ]:
        assert key in library
        entry = library[key]
        assert entry["pattern"]
        assert entry["primary_muscles"]
        assert entry["coaching_cues"]
        assert entry["common_errors"]
        assert entry["regressions"]
        assert entry["progressions"]
        assert entry["safety_notes"]

    assert "סקוואט גביע" in library["squat"]["progressions"]
    assert any("ארבע ראשי" in muscle or "גלוט" in muscle for muscle in library["squat"]["primary_muscles"])
    assert any("ברכיים" in cue for cue in library["squat"]["coaching_cues"])
    assert any("גב" in error or "עמוד שדרה" in error for error in library["hip_hinge"]["common_errors"])
    assert any("חזה" in muscle or "טרייספס" in muscle for muscle in library["horizontal_push"]["primary_muscles"])
    assert any("רחב גבי" in muscle or "שכמות" in muscle for muscle in library["horizontal_pull"]["primary_muscles"])
    assert any("אנטי" in item or "קו ישר" in item for item in library["core_anti_extension"]["coaching_cues"])
    assert any(source["organization"] == "NASM Exercise Library" for source in context["sources"])
    assert any(source["organization"] == "ACE Exercise Library" for source in context["sources"])


def test_coaching_knowledge_contains_expanded_exercise_library_patterns():
    context = CoachingKnowledgeService().for_intent("workout_plan")
    library = context["exercise_library"]

    for key in [
        "vertical_push",
        "vertical_pull",
        "glute_bridge_hip_thrust",
        "step_up",
        "calf_raise",
        "arm_accessory",
    ]:
        assert key in library
        entry = library[key]
        assert entry["pattern"]
        assert entry["primary_muscles"]
        assert entry["coaching_cues"]
        assert entry["common_errors"]
        assert entry["regressions"]
        assert entry["progressions"]
        assert entry["safety_notes"]

    assert any("כתף" in muscle or "דלתא" in muscle for muscle in library["vertical_push"]["primary_muscles"])
    assert any("צלעות" in cue or "גב" in cue for cue in library["vertical_push"]["coaching_cues"])
    assert any("רחב גבי" in muscle or "לטיסימוס" in muscle for muscle in library["vertical_pull"]["primary_muscles"])
    assert any("גלוט" in muscle for muscle in library["glute_bridge_hip_thrust"]["primary_muscles"])
    assert any(
        "מדרגה" in item or "step-up" in item
        for item in library["step_up"]["regressions"] + library["step_up"]["progressions"]
    )
    assert any("שוק" in muscle or "תאומים" in muscle for muscle in library["calf_raise"]["primary_muscles"])
    assert any("בייספס" in muscle for muscle in library["arm_accessory"]["primary_muscles"])
    assert any("טרייספס" in muscle for muscle in library["arm_accessory"]["primary_muscles"])
    assert any(source["organization"] == "ACE Exercise Library - Expanded Patterns" for source in context["sources"])
    assert any(source["organization"] == "NASM Exercise Library - Expanded Patterns" for source in context["sources"])


def test_coaching_knowledge_contains_anatomy_muscle_map():
    context = CoachingKnowledgeService().for_intent("workout_plan")

    assert "anatomy_muscle_map" in context
    muscle_map = context["anatomy_muscle_map"]
    for key in [
        "lower_body",
        "upper_push",
        "upper_pull",
        "core_trunk",
        "arms_shoulders_accessory",
        "program_balance",
    ]:
        assert key in muscle_map
        entry = muscle_map[key]
        assert entry["muscle_groups"]
        assert entry["movement_patterns"]
        assert entry["coach_uses"]
        assert entry["balance_rules"]
        assert entry["avoid"]
        assert entry["source_refs"]

    assert any("ארבע ראשי" in item or "quadriceps" in item for item in muscle_map["lower_body"]["muscle_groups"])
    assert any("גלוט" in item for item in muscle_map["lower_body"]["muscle_groups"])
    assert any("חזה" in item and "טרייספס" in item for item in muscle_map["upper_push"]["muscle_groups"])
    assert any("גב" in item and "בייספס" in item for item in muscle_map["upper_pull"]["muscle_groups"])
    assert any("אנטגוניסט" in item or "push/pull" in item for item in muscle_map["program_balance"]["balance_rules"])
    assert any(source["organization"] == "ACSM Major Muscle Groups" for source in context["sources"])
    assert any(source["organization"] == "ACE Essentials of Exercise Science" for source in context["sources"])
    assert any(source["organization"] == "Movement Pattern Definitions Review" for source in context["sources"])


def test_provider_context_exercise_summary_includes_muscle_mapping_without_full_map():
    context = CoachingKnowledgeService().for_provider_context("workout_plan")

    summary = context["exercise_library_summary"]
    assert any("ארבע ראשי" in item or "quads" in item for item in summary)
    assert any("גלוט" in item and "המסטרינג" in item for item in summary)
    assert any("חזה" in item and "טרייספס" in item for item in summary)
    assert any("גב" in item and "בייספס" in item for item in summary)
    assert "anatomy_muscle_map" not in context
    assert len(str(context)) < 8500


def test_provider_context_includes_compact_exercise_library_summary():
    context = CoachingKnowledgeService().for_provider_context("workout_plan")

    assert "exercise_library_summary" in context
    summary = context["exercise_library_summary"]
    assert any("סקוואט" in item and "ברכיים" in item for item in summary)
    assert any("hinge" in item or "הינג׳" in item for item in summary)
    assert any("דחיפה" in item and "כתפיים" in item for item in summary)
    assert any("משיכה" in item and "שכמות" in item for item in summary)
    assert any("ליבה" in item for item in summary)
    assert len(str(context)) < 10500


def test_provider_context_exercise_library_summary_mentions_expanded_patterns():
    context = CoachingKnowledgeService().for_provider_context("workout_plan")
    summary = context["exercise_library_summary"]

    assert any("אנכית" in item and "דחיפה" in item for item in summary)
    assert any("אנכית" in item and "משיכה" in item for item in summary)
    assert any("hip thrust" in item or "גשר" in item for item in summary)
    assert any("זרועות" in item or "בייספס" in item for item in summary)
    assert "exercise_library" not in context
    assert len(str(context)) < 8500


def _retrieved_topics(intent: str, query: str) -> list[str]:
    context = CoachingKnowledgeService().for_provider_context(intent, query=query)
    return [hit["topic"] for hit in context.get("retrieved_knowledge", [])]


def test_retrieval_iterator_reaches_every_non_meta_knowledge_key():
    reachable = {table_key for _topic, table_key, _entry_key, _entry in _iter_knowledge_entries(_BASE_CONTEXT)}
    unreachable = [
        key
        for key in _BASE_CONTEXT
        if key not in reachable and key not in _RETRIEVAL_SKIP_KEYS
    ]

    assert unreachable == []
    # The whole knowledge base, minus a few metadata keys, is searchable.
    assert len(reachable) >= len(_BASE_CONTEXT) - len(_RETRIEVAL_SKIP_KEYS) - 1


def test_retrieval_surfaces_previously_unreachable_tables():
    # Tables that used to be stored-but-never-sent should now retrieve.
    assert "protein_guidelines" in _retrieved_topics("general_chat", "כמה חלבון לאכול ביום לבניית שריר?")
    assert "walking_running_protocols.beginner_walk_run" in _retrieved_topics(
        "general_chat", "איך מתחילים לרוץ בלי לפצוע את עצמי?"
    )
    assert "program_lifecycle_protocols.deload_week" in _retrieved_topics(
        "general_chat", "מה זה דילואד ומתי עושים אותו?"
    )
    assert "exercise_library.squat" in _retrieved_topics("workout_plan", "מה הטכניקה הנכונה בסקוואט?")
    assert any(
        topic.startswith("goal_specific_programming")
        or topic.startswith("advanced_strength_hypertrophy_protocols")
        for topic in _retrieved_topics("workout_plan", "כמה סטים לעשות להיפרטרופיה?")
    )


def test_retrieval_keeps_spot_reduction_top_hit_and_budget():
    context = CoachingKnowledgeService().for_provider_context(
        "general_chat", query="האם כפיפות בטן באמת מורידות שומן בבטן?"
    )

    assert context["retrieved_knowledge"][0]["topic"] == "common_fitness_myth_protocols.spot_reduction"
    assert "common_fitness_myth_protocols" not in context
    assert len(str(context)) < 7000


def test_retrieved_hits_carry_actual_content_for_varied_field_shapes():
    # exercise_library entries use non-standard fields (coaching_cues, progressions...).
    # The generic projection must still surface real content, not an empty shell.
    context = CoachingKnowledgeService().for_provider_context("workout_plan", query="מה הטכניקה הנכונה בסקוואט?")
    squat_hit = next(hit for hit in context["retrieved_knowledge"] if hit["topic"] == "exercise_library.squat")

    assert squat_hit.get("guidance") or squat_hit.get("action")
    assert any(any("֐" <= ch <= "׿" for ch in item) for item in squat_hit.get("guidance", []) + squat_hit.get("action", []))


def test_tokenize_strips_hebrew_prefixes_for_matching():
    # A query word carrying attached prefixes must still share a token with the bare word.
    assert "חלבון" in _tokenize("ובחלבון")
    assert "ריצה" in _tokenize("שהריצה")
    assert _tokenize("כמה חלבון") & _tokenize("צריכת החלבון היומית")


def test_retrieval_respects_provider_context_budget_for_all_intents():
    queries = {
        "general_chat": "מה זה דילואד ואיך יודעים שצריך?",
        "workout_plan": "כמה סטים לעשות להיפרטרופיה עם משקולות?",
        "workout_log": "עשיתי אימון כבד ואני תפוס, מה עכשיו?",
        "meal_log": "מה לאכול לפני אימון בערב?",
        "meal_image": "כמה קלוריות בצלחת הזאת בערך?",
    }
    budgets = {
        "general_chat": 7000,
        "workout_plan": 8500,
        "workout_log": 8500,
        "meal_log": 10500,
        "meal_image": 10500,
    }
    for intent, query in queries.items():
        context = CoachingKnowledgeService().for_provider_context(intent, query=query)
        assert len(str(context)) <= budgets[intent], intent
