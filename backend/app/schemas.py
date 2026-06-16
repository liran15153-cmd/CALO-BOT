from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


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
            raise ValueError("consent_disclaimer must be accepted")
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
    title: str = Field(default="Coach chat", min_length=1, max_length=160)


class ChatMessageCreate(BaseModel):
    session_id: int
    role: Literal["user", "coach", "system"]
    content: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: int
    user_message_id: int
    coach_message_id: int
    response: str
    safety_flagged: bool = False
    provider_status: str


class WorkoutPlanRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    days_per_week: int | None = Field(default=None, ge=1, le=7)
    session_length_minutes: int | None = Field(default=None, ge=10, le=120)
    equipment: list[str] = Field(default_factory=list)


class StructuredExercise(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    sets: str = Field(min_length=1, max_length=40)
    reps_or_duration: str = Field(min_length=1, max_length=80)
    rest: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    difficulty: str = Field(default="moderate", max_length=40)
    alternatives: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class StructuredWorkoutDay(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    warmup: list[str] = Field(min_length=1)
    exercises: list[StructuredExercise] = Field(min_length=1)
    difficulty: str = Field(default="moderate", max_length=40)
    notes: str | None = Field(default=None, max_length=700)


class StructuredWorkoutPlan(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    goal: str = Field(min_length=1, max_length=120)
    duration_weeks: int = Field(ge=1, le=52)
    days_per_week: int = Field(ge=1, le=7)
    equipment_needed: list[str] = Field(default_factory=list)
    days: list[StructuredWorkoutDay] = Field(min_length=1)
    progression_rule: str = Field(min_length=1, max_length=1000)
    recovery_note: str | None = Field(default=None, max_length=1000)


class WorkoutLogRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    workout_id: int | None = None
    logged_on: date | None = None


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


class SummaryResponse(BaseModel):
    summary: str
    metrics: dict[str, Any]
    next_action: str


class SettingsResponse(BaseModel):
    ai_provider: str
    model: str
    database: str
    api_key_present: bool
    disclaimer: str


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
