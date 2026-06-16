from sqlalchemy import inspect

from backend.app.db import init_db, make_engine


def test_init_db_creates_core_tables(tmp_path):
    db_path = tmp_path / "app.db"
    engine = make_engine(f"sqlite:///{db_path}")

    init_db(engine)

    tables = set(inspect(engine).get_table_names())
    assert {
        "users",
        "user_profile",
        "chat_sessions",
        "chat_messages",
        "workout_plans",
        "workouts",
        "workout_exercises",
        "workout_logs",
        "meals",
        "meal_items",
        "meal_image_analysis",
        "user_memories",
        "weekly_summaries",
        "safety_events",
        "usage_events",
    }.issubset(tables)

