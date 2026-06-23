from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


Goal = Literal[
    "build_muscle",
    "lose_fat",
    "improve_fitness",
    "maintain_health",
    "improve_consistency",
    "improve_strength",
    "improve_endurance",
]
Experience = Literal["beginner", "intermediate", "advanced"]
TrainingLocation = Literal["home", "gym", "outdoors", "mixed"]
CoachingStyle = Literal["direct", "supportive", "strict", "minimal", "detailed"]
WorkoutPlanType = Literal["multi_week", "single_session"]
ReadinessLevel = Literal["green", "yellow", "red"]
WorkoutLogStatus = Literal["completed", "partial", "skipped", "modified"]


class OnboardingPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age_range: str | None = Field(default=None, max_length=40)
    gender: str | None = Field(default=None, max_length=40)
    height_cm: float | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, ge=25, le=350)
    main_goal: Goal
    experience_level: Experience
    training_location: TrainingLocation
    available_equipment: list[str] = Field(default_factory=list, max_length=20)
    weekly_availability: int = Field(ge=1, le=7)
    session_length_minutes: int = Field(ge=15, le=120)
    preferred_workout_days: list[str] = Field(default_factory=list, max_length=7)
    injuries_limitations: str | None = Field(default=None, max_length=1200)
    nutrition_preference: str | None = Field(default=None, max_length=80)
    foods_disliked: str | None = Field(default=None, max_length=1200)
    allergies: str | None = Field(default=None, max_length=1200)
    typical_schedule: str | None = Field(default=None, max_length=1200)
    coaching_style: CoachingStyle = "direct"
    consent_disclaimer: bool

    @field_validator("consent_disclaimer")
    @classmethod
    def consent_required(cls, value: bool) -> bool:
        if not value:
            raise ValueError("יש לאשר שהאפליקציה מספקת הכוונת כושר ותזונה כללית בלבד")
        return value

    @field_validator("available_equipment", "preferred_workout_days")
    @classmethod
    def normalize_strings(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    age_range: str | None
    gender: str | None
    height_cm: float | None
    weight_kg: float | None
    main_goal: str
    experience_level: str
    training_location: str
    available_equipment: list[str]
    weekly_availability: int
    session_length_minutes: int
    preferred_workout_days: list[str]
    injuries_limitations: str | None
    nutrition_preference: str | None
    foods_disliked: str | None
    allergies: str | None
    typical_schedule: str | None
    coaching_style: str
    consent_disclaimer: bool


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: int | None = None


class ChatSessionCreate(BaseModel):
    title: str = Field(default="צ'אט מאמן", min_length=1, max_length=160)


class ChatResponse(BaseModel):
    session_id: int
    user_message_id: int
    coach_message_id: int
    response: str
    safety_flagged: bool = False
    provider_status: str


class WorkoutPlanRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    plan_type: WorkoutPlanType | None = None
    goal: Goal | None = None
    experience_level: Experience | None = None
    duration_weeks: int | None = Field(default=None, ge=1, le=4)
    days_per_week: int | None = Field(default=None, ge=1, le=7)
    session_length_minutes: int | None = Field(default=None, ge=10, le=120)
    equipment: list[str] = Field(default_factory=list)
    limitations: str | None = Field(default=None, max_length=1200)
    readiness: ReadinessLevel | None = None


class ActivateWorkoutPlanRequest(BaseModel):
    delete_previous: bool = True


class PendingActionResolveRequest(BaseModel):
    decision: Literal["confirm", "decline"]


class StructuredExercise(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    sets: str = Field(min_length=1, max_length=40)
    reps_or_duration: str = Field(min_length=1, max_length=80)
    rest: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    difficulty: str = Field(default="moderate", max_length=40)
    alternatives: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    movement_pattern: str | None = Field(default=None, max_length=80)
    target_muscles: list[str] = Field(default_factory=list)
    progression: str | None = Field(default=None, max_length=300)
    regression: str | None = Field(default=None, max_length=300)
    source_refs: list[str] = Field(default_factory=list)


class StructuredWorkoutDay(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    focus: str = Field(default="full_body", max_length=80)
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=180)
    warmup: list[str] = Field(min_length=1)
    exercises: list[StructuredExercise] = Field(min_length=1)
    difficulty: str = Field(default="moderate", max_length=40)
    notes: str | None = Field(default=None, max_length=700)


class StructuredWorkoutPlan(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    goal: str = Field(min_length=1, max_length=120)
    plan_type: WorkoutPlanType = "multi_week"
    training_split: str = Field(default="full_body", max_length=80)
    experience_level: str = Field(default="beginner", max_length=40)
    duration_weeks: int = Field(ge=1, le=4)
    days_per_week: int = Field(ge=1, le=7)
    session_length_minutes: int | None = Field(default=None, ge=1, le=180)
    equipment_needed: list[str] = Field(default_factory=list)
    days: list[StructuredWorkoutDay] = Field(min_length=1)
    progression_rule: str = Field(min_length=1, max_length=1000)
    progression_model: str | None = Field(default=None, max_length=500)
    recovery_note: str | None = Field(default=None, max_length=1000)
    safety_notes: list[str] = Field(default_factory=list)
    decision_inputs: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)


class WorkoutSetLogInput(BaseModel):
    set_index: int = Field(ge=1, le=40)
    reps: int | None = Field(default=None, ge=0, le=300)
    weight: str | None = Field(default=None, max_length=80)
    duration_seconds: int | None = Field(default=None, ge=0, le=7200)
    completed: bool = True


class WorkoutExerciseLogInput(BaseModel):
    exercise_id: int | None = None
    exercise_name: str = Field(min_length=1, max_length=160)
    status: WorkoutLogStatus = "completed"
    sets: list[WorkoutSetLogInput] = Field(default_factory=list, max_length=40)
    rpe: int | None = Field(default=None, ge=1, le=10)
    rir: int | None = Field(default=None, ge=0, le=10)
    notes: str | None = Field(default=None, max_length=700)


class WorkoutLogRequest(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=2000)
    workout_id: int | None = None
    logged_on: date | None = None
    status: WorkoutLogStatus | None = None
    exercises: list[WorkoutExerciseLogInput] = Field(default_factory=list, max_length=80)
    rpe: int | None = Field(default=None, ge=1, le=10)
    rir: int | None = Field(default=None, ge=0, le=10)
    pain_flag: bool = False
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def has_log_content(self) -> "WorkoutLogRequest":
        if self.text or self.notes or self.exercises or self.status in {"skipped", "partial", "modified", "completed"}:
            return self
        raise ValueError("Workout log requires text, structured exercises, notes, or status")


class MealTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    eaten_on: date | None = None
    meal_type: str | None = None


class MealResponse(BaseModel):
    id: int
    note: str | None
    image_path: str | None
    calories_min: int | None
    calories_max: int | None
    confidence: str | None


class BodyMetricRequest(BaseModel):
    measured_on: date | None = None
    weight_kg: float | None = Field(default=None, ge=25, le=350)
    body_fat_percent: float | None = Field(default=None, ge=2, le=75)
    measurements: dict[str, float] = Field(default_factory=dict)
    source: str = Field(default="manual", min_length=1, max_length=80)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("measurements")
    @classmethod
    def validate_measurements(cls, value: dict[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for key, raw_measurement in value.items():
            clean_key = key.strip()
            if not clean_key or len(clean_key) > 60:
                raise ValueError("measurement names must be 1-60 characters")
            measurement = float(raw_measurement)
            if measurement < 0 or measurement > 500:
                raise ValueError("measurement values must be between 0 and 500")
            normalized[clean_key] = measurement
        return normalized

    @model_validator(mode="after")
    def has_metric_content(self) -> "BodyMetricRequest":
        if self.weight_kg is not None or self.body_fat_percent is not None or self.measurements:
            return self
        raise ValueError("body metric requires weight, body fat, or at least one measurement")


class BodyMetricResponse(BaseModel):
    id: int
    measured_on: date
    weight_kg: float | None
    body_fat_percent: float | None
    measurements: dict[str, float]
    source: str
    note: str | None


class SettingsResponse(BaseModel):
    ai_provider: str
    model: str
    chat_model: str
    database: str
    api_key_present: bool
    supabase: str = "not_configured"
    supabase_storage: str = "local"
    disclaimer: str


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    ai_provider: str
    no_api_key_mode: bool


class ResetResponse(BaseModel):
    deleted_records: int
    message: str

    
class UsageResponse(BaseModel):
    usage_date: date
    chat_requests_count: int
    image_analysis_count: int
    summary_requests_count: int
    estimated_tokens_in: int
    estimated_tokens_out: int
    estimated_tokens_total: int
    token_breakdown: dict[str, int] = Field(default_factory=dict)
    daily_ai_token_limit: int
    tokens_remaining: int
