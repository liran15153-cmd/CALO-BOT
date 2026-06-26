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
        "memory_facts",
    }.issubset(tables)


def test_init_db_rebuilds_legacy_memory_facts_schema(tmp_path):
    db_path = tmp_path / "legacy.db"
    engine = make_engine(f"sqlite:///{db_path}")

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.exec_driver_sql("INSERT INTO users (id, name) VALUES (1, 'Local User')")
        connection.exec_driver_sql(
            """
            CREATE TABLE memory_facts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type VARCHAR(60) NOT NULL,
                subject VARCHAR(120),
                predicate VARCHAR(80) NOT NULL,
                value JSON NOT NULL,
                text_he TEXT NOT NULL,
                confidence FLOAT NOT NULL,
                status VARCHAR(40) NOT NULL,
                source_message_id INTEGER,
                source_safety_event_id INTEGER,
                extracted_by VARCHAR(40) NOT NULL,
                valid_from DATETIME,
                valid_to DATETIME,
                superseded_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO memory_facts (
                id, user_id, type, subject, predicate, value, text_he, confidence, status, extracted_by
            )
            VALUES (1, 1, 'injury', 'knee', 'has_pain', '{}', 'knee pain', 0.9, 'active', 'legacy')
            """
        )

    init_db(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("memory_facts")}

    assert {"slot", "value_text", "source", "safety_event_id", "valid_at", "metadata_json"}.issubset(columns)
    assert {"predicate", "value", "extracted_by"}.isdisjoint(columns)

    with Session(engine) as session:
        session.execute(
            text(
                """
                INSERT INTO memory_facts (
                    user_id, type, status, text_he, confidence, salience, source, provenance_json, metadata_json
                )
                VALUES (1, 'allergy', 'active', 'peanut allergy', 'high', 1.0, 'sync_safety', '{}', '{}')
                """
            )
        )
        session.commit()


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
