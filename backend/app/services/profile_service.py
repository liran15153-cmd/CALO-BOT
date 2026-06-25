from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import User, UserProfile
from backend.app.schemas import OnboardingPayload, UserProfileResponse


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_default_user(self) -> User:
        user = self.get_existing_default_user()
        if user:
            return user
        user = User(name="משתמש מקומי")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_existing_default_user(self) -> User | None:
        return self.db.scalar(select(User).order_by(User.id.asc()))

    def get_or_create_auth_user(self, *, auth_user_id: str, email: str | None = None) -> User:
        user = self.db.scalar(select(User).where(User.auth_user_id == auth_user_id))
        if user:
            if email and user.email != email:
                user.email = email
                self.db.commit()
                self.db.refresh(user)
            return user
        user = User(
            auth_user_id=auth_user_id,
            email=email,
            name=email.split("@", 1)[0] if email else "משתמש Supabase",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_profile(self, *, create_user: bool = True) -> UserProfile | None:
        user = self.get_default_user() if create_user else self.get_existing_default_user()
        if user is None:
            return None
        return self.db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))

    def get_profile_for_user(self, user_id: int) -> UserProfile | None:
        return self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))

    def upsert_onboarding(self, payload: OnboardingPayload, user_id: int | None = None) -> UserProfile:
        user = self.db.get(User, user_id) if user_id is not None else self.get_default_user()
        if user is None:
            raise ValueError("משתמש לא נמצא")
        user.name = payload.name
        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
        if profile is None:
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)

        for field, value in payload.model_dump(exclude={"name"}).items():
            setattr(profile, field, value)

        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(user)
        return profile

    @staticmethod
    def to_response(profile: UserProfile) -> UserProfileResponse:
        return UserProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            name=profile.user.name,
            age_range=profile.age_range,
            gender=profile.gender,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            main_goal=profile.main_goal,
            experience_level=profile.experience_level,
            training_location=profile.training_location,
            available_equipment=profile.available_equipment or [],
            weekly_availability=profile.weekly_availability,
            session_length_minutes=profile.session_length_minutes,
            preferred_workout_days=profile.preferred_workout_days or [],
            injuries_limitations=profile.injuries_limitations,
            nutrition_preference=profile.nutrition_preference,
            foods_disliked=profile.foods_disliked,
            allergies=profile.allergies,
            typical_schedule=profile.typical_schedule,
            coaching_style=profile.coaching_style,
            consent_disclaimer=profile.consent_disclaimer,
        )
