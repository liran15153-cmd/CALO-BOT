import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db import init_db, make_engine


def test_init_db_creates_core_tables(tmp_path):
    db_path = tmp_path / "app.db"
    engine = make_engine(f"sqlite:///{db_path}")

    init_db(engine)

    tables = set(inspect(engine).get_table_names())
    assert {
        "users",
        "fitness_profiles",
        "chat_sessions",
        "chat_messages",
        "workout_plans",
        "workouts",
        "workout_exercises",
        "workout_logs",
        "meal_logs",
        "meal_items",
        "meal_image_analyses",
        "body_metrics",
        "safety_events",
        "usage_events",
        "pending_actions",
    }.issubset(tables)


def test_sqlite_engine_enforces_foreign_keys(tmp_path):
    db_path = tmp_path / "app.db"
    engine = make_engine(f"sqlite:///{db_path}")
    init_db(engine)

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1

    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            session.execute(
                text(
                    "INSERT INTO chat_messages (session_id, user_id, role, content) "
                    "VALUES (999, 999, 'user', 'orphan')"
                )
            )
            session.commit()

    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            session.execute(
                text(
                    "INSERT INTO pending_actions "
                    "(user_id, action_type, status, subject_type, subject_id, payload_json) "
                    "VALUES (999, 'activate_workout_plan', 'pending', 'workout_plan', 1, '{}')"
                )
            )
            session.commit()
