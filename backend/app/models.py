from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    auth_user_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False)


class UserProfile(Base, TimestampMixin):
    __tablename__ = "fitness_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    age_range: Mapped[str | None] = mapped_column(String(40))
    gender: Mapped[str | None] = mapped_column(String(40))
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    main_goal: Mapped[str] = mapped_column(String(80), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(40), nullable=False)
    training_location: Mapped[str] = mapped_column(String(40), nullable=False)
    available_equipment: Mapped[list[str]] = mapped_column(JSON, default=list)
    weekly_availability: Mapped[int] = mapped_column(Integer, nullable=False)
    session_length_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_workout_days: Mapped[list[str]] = mapped_column(JSON, default=list)
    injuries_limitations: Mapped[str | None] = mapped_column(Text)
    nutrition_preference: Mapped[str | None] = mapped_column(String(80))
    foods_disliked: Mapped[str | None] = mapped_column(Text)
    allergies: Mapped[str | None] = mapped_column(Text)
    typical_schedule: Mapped[str | None] = mapped_column(Text)
    coaching_style: Mapped[str] = mapped_column(String(40), nullable=False, default="direct")
    consent_disclaimer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship(back_populates="profile")


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160), default="צ'אט מאמן")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class PendingAction(Base, TimestampMixin):
    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("chat_sessions.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending", index=True)
    subject_type: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    resolution: Mapped[str | None] = mapped_column(String(40))
    created_from_message_id: Mapped[int | None] = mapped_column(ForeignKey("chat_messages.id"), nullable=True)
    resolved_by_message_id: Mapped[int | None] = mapped_column(ForeignKey("chat_messages.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkoutPlan(Base, TimestampMixin):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    goal: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, default=4)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    equipment_needed: Mapped[list[str]] = mapped_column(JSON, default=list)
    plan_json: Mapped[dict] = mapped_column(JSON, default=dict)
    progression_rule: Mapped[str | None] = mapped_column(Text)
    recovery_note: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class Workout(Base, TimestampMixin):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("workout_plans.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    scheduled_day: Mapped[str | None] = mapped_column(String(40))
    difficulty: Mapped[str | None] = mapped_column(String(40))
    workout_json: Mapped[dict] = mapped_column(JSON, default=dict)


class WorkoutExercise(Base, TimestampMixin):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sets: Mapped[str | None] = mapped_column(String(40))
    reps_or_duration: Mapped[str | None] = mapped_column(String(80))
    rest: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    alternatives: Mapped[list[str]] = mapped_column(JSON, default=list)


class WorkoutLog(Base, TimestampMixin):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id"))
    logged_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    exercise_results: Mapped[list[dict]] = mapped_column(JSON, default=list)
    rpe: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    pain_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    parse_confidence: Mapped[str] = mapped_column(String(20), default="medium")


class Meal(Base, TimestampMixin):
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    eaten_on: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(500))
    calories_min: Mapped[int | None] = mapped_column(Integer)
    calories_max: Mapped[int | None] = mapped_column(Integer)
    protein_min: Mapped[int | None] = mapped_column(Integer)
    protein_max: Mapped[int | None] = mapped_column(Integer)
    carbs_min: Mapped[int | None] = mapped_column(Integer)
    carbs_max: Mapped[int | None] = mapped_column(Integer)
    fat_min: Mapped[int | None] = mapped_column(Integer)
    fat_max: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[str | None] = mapped_column(String(20))


class MealItem(Base, TimestampMixin):
    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meal_logs.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(120))
    calories_min: Mapped[int | None] = mapped_column(Integer)
    calories_max: Mapped[int | None] = mapped_column(Integer)
    protein_min: Mapped[int | None] = mapped_column(Integer)
    protein_max: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[str | None] = mapped_column(String(20))


class MealImageAnalysis(Base, TimestampMixin):
    __tablename__ = "meal_image_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meal_logs.id"), index=True)
    detected_items: Mapped[list[dict]] = mapped_column(JSON, default=list)
    follow_up_questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    analysis_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provider_status: Mapped[str] = mapped_column(String(40), default="not_configured")


class BodyMetric(Base, TimestampMixin):
    __tablename__ = "body_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    measured_on: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    body_fat_percent: Mapped[float | None] = mapped_column(Float)
    waist_cm: Mapped[float | None] = mapped_column(Float)
    measurements_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="manual")
    note: Mapped[str | None] = mapped_column(Text)


class SafetyEvent(Base, TimestampMixin):
    __tablename__ = "safety_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class MemoryFact(Base, TimestampMixin):
    __tablename__ = "memory_facts"
    __table_args__ = (
        CheckConstraint(
            "type in ("
            "'allergy','medical','injury','restriction_nutrition','equipment','schedule',"
            "'preference','goal','context_life','pattern_motivation','other'"
            ")",
            name="ck_memory_facts_type",
        ),
        CheckConstraint(
            "status in ('active','superseded','retracted','expired')",
            name="ck_memory_facts_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    fact_type: Mapped[str] = mapped_column("type", String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    slot: Mapped[str | None] = mapped_column(String(80), index=True)
    value_text: Mapped[str | None] = mapped_column(Text)
    text_he: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    salience: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="sync_safety")
    source_message_id: Mapped[int | None] = mapped_column(ForeignKey("chat_messages.id"), index=True)
    safety_event_id: Mapped[int | None] = mapped_column(ForeignKey("safety_events.id"), index=True)
    valid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by: Mapped[int | None] = mapped_column(ForeignKey("memory_facts.id"))
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class UsageEvent(Base, TimestampMixin):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    task: Mapped[str] = mapped_column(String(60), nullable=False)
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))
    estimated_tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    estimated_tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    token_breakdown_json: Mapped[dict] = mapped_column(JSON, default=dict)
    cost_estimate: Mapped[float | None] = mapped_column(Float)
