from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import ChatMessage, Meal, SafetyEvent, WorkoutPlan
from backend.app.services.coach_intent_service import CoachIntentService


def test_intent_service_handles_common_user_typos():
    service = CoachIntentService()

    assert service.classify("buld me a begginer wrkout plan for tody 20 minuts no equipmant").name == "workout_plan"
    assert service.classify("i aet rise chiken sald and thini for lanch").name == "meal_log"
    assert service.classify("can u analize my food foto and tell exact callories").name == "meal_image_guidance"
    assert service.classify("תבני לי תוכנית אימן של 2 ימם בלי ציוד ובלי ריצה").name == "workout_plan"
    assert service.classify("אכלטי אורז אוף וסלת בצהרים").name == "meal_log"


def test_typo_workout_request_saves_plan_without_ai_provider(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "buld me a begginer wrkout plan for tody 20 minuts no equipmant"},
    )

    assert response.status_code == 200
    assert response.json()["provider_status"] == "local_tool"
    assert db.scalar(select(func.count()).select_from(WorkoutPlan)) == 1


def test_dual_meal_and_plan_does_not_silently_drop_second_state_intent(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "אכלתי פיצה וגם תבנה לי אימון קצר להיום"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert db.scalar(select(func.count()).select_from(Meal)) == 1
    assert db.scalar(select(func.count()).select_from(WorkoutPlan)) == 0
    assert "אימון" in body["response"]
    coach_message = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert coach_message is not None
    assert coach_message.metadata_json["secondary_intent"] == "workout_plan"


def test_typo_extreme_diet_request_is_safety_blocked(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "i need lose 8kg this mnth give me 800 cal meal plan"},
    )

    assert response.status_code == 200
    assert response.json()["safety_flagged"] is True
    assert db.scalar(select(func.count()).select_from(SafetyEvent)) == 1


def test_obvious_non_fitness_request_is_handled_locally_without_provider(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "Can you help me write a resignation email to my manager?"},
    )

    assert response.status_code == 200
    assert response.json()["provider_status"] == "local_tool"
    assert "כושר" in response.json()["response"]
    assert db.scalar(select(func.count()).select_from(WorkoutPlan)) == 0
    assert db.scalar(select(func.count()).select_from(Meal)) == 0


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'adversarial.db'}")
    init_db(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    db = testing_session()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
