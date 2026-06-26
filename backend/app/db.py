from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.config import get_settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_parent(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    raw_path = database_url.replace("sqlite:///", "", 1)
    if raw_path == ":memory:":
        return
    Path(raw_path).parent.mkdir(parents=True, exist_ok=True)


def make_engine(database_url: str) -> Engine:
    _ensure_sqlite_parent(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    created_engine = create_engine(database_url, connect_args=connect_args)
    if database_url.startswith("sqlite"):
        event.listen(created_engine, "connect", _enable_sqlite_foreign_keys)
    return created_engine


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


settings = get_settings()
engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db(target_engine: Engine = engine) -> None:
    import backend.app.models  # noqa: F401

    if target_engine.dialect.name != "sqlite":
        return
    Base.metadata.create_all(bind=target_engine)
    _ensure_user_auth_schema(target_engine)
    _ensure_usage_event_schema(target_engine)
    _ensure_body_metric_schema(target_engine)
    _ensure_memory_fact_schema(target_engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_usage_event_schema(target_engine: Engine) -> None:
    if target_engine.dialect.name != "sqlite":
        return
    inspector = inspect(target_engine)
    if "usage_events" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("usage_events")}
    if "token_breakdown_json" in columns:
        return
    with target_engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE usage_events ADD COLUMN token_breakdown_json JSON DEFAULT '{}'")


def _ensure_user_auth_schema(target_engine: Engine) -> None:
    if target_engine.dialect.name != "sqlite":
        return
    inspector = inspect(target_engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    with target_engine.begin() as connection:
        if "auth_user_id" not in columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN auth_user_id VARCHAR(64)")
            connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_auth_user_id ON users (auth_user_id)")
        if "email" not in columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN email VARCHAR(255)")


def _ensure_body_metric_schema(target_engine: Engine) -> None:
    if target_engine.dialect.name != "sqlite":
        return
    inspector = inspect(target_engine)
    if "body_metrics" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("body_metrics")}
    with target_engine.begin() as connection:
        if "body_fat_percent" not in columns:
            connection.exec_driver_sql("ALTER TABLE body_metrics ADD COLUMN body_fat_percent FLOAT")
        if "measurements_json" not in columns:
            connection.exec_driver_sql("ALTER TABLE body_metrics ADD COLUMN measurements_json JSON DEFAULT '{}'")
        if "source" not in columns:
            connection.exec_driver_sql("ALTER TABLE body_metrics ADD COLUMN source VARCHAR(80) DEFAULT 'manual' NOT NULL")


def _ensure_memory_fact_schema(target_engine: Engine) -> None:
    if target_engine.dialect.name != "sqlite":
        return
    inspector = inspect(target_engine)
    table_names = set(inspector.get_table_names())
    if "memory_facts" not in table_names:
        return
    columns = {column["name"] for column in inspector.get_columns("memory_facts")}
    required_columns = {
        "slot",
        "value_text",
        "source",
        "safety_event_id",
        "valid_at",
        "invalid_at",
        "expired_at",
        "provenance_json",
        "metadata_json",
    }
    legacy_required_columns = {"predicate", "value", "extracted_by"}
    if required_columns.issubset(columns) and not legacy_required_columns.intersection(columns):
        if "memory_facts_legacy" in table_names:
            with target_engine.begin() as connection:
                connection.exec_driver_sql("DROP TABLE memory_facts_legacy")
        return

    import backend.app.models  # noqa: F401

    legacy_table = "memory_facts_legacy_rebuild"
    with target_engine.begin() as connection:
        connection.exec_driver_sql(f"DROP TABLE IF EXISTS {legacy_table}")
        connection.exec_driver_sql(f"ALTER TABLE memory_facts RENAME TO {legacy_table}")
        for index_name, in connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = ?",
            (legacy_table,),
        ):
            connection.exec_driver_sql(f"DROP INDEX IF EXISTS {index_name}")
        Base.metadata.tables["memory_facts"].create(bind=connection)
        legacy_columns = {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({legacy_table})")}
        safety_event_column = (
            "source_safety_event_id"
            if "source_safety_event_id" in legacy_columns
            else "safety_event_id"
            if "safety_event_id" in legacy_columns
            else "NULL"
        )
        valid_at_column = "valid_from" if "valid_from" in legacy_columns else "valid_at" if "valid_at" in legacy_columns else "NULL"
        expired_at_column = "valid_to" if "valid_to" in legacy_columns else "expired_at" if "expired_at" in legacy_columns else "NULL"
        connection.exec_driver_sql(
            f"""
            INSERT INTO memory_facts (
                id, user_id, type, status, slot, value_text, text_he, confidence, salience, source,
                source_message_id, safety_event_id, valid_at, invalid_at, expired_at, superseded_by,
                provenance_json, metadata_json, created_at, updated_at
            )
            SELECT
                id,
                user_id,
                type,
                CASE WHEN status IN ('active', 'superseded', 'retracted', 'expired') THEN status ELSE 'active' END,
                NULL,
                NULL,
                text_he,
                CASE
                    WHEN CAST(confidence AS REAL) >= 0.8 THEN 'high'
                    WHEN CAST(confidence AS REAL) <= 0.3 THEN 'low'
                    ELSE 'medium'
                END,
                0.5,
                'legacy_sqlite_migration',
                source_message_id,
                {safety_event_column},
                {valid_at_column},
                NULL,
                {expired_at_column},
                NULL,
                '{{}}',
                '{{}}',
                created_at,
                updated_at
            FROM {legacy_table}
            WHERE type IN (
                'allergy', 'medical', 'injury', 'restriction_nutrition', 'equipment', 'schedule',
                'preference', 'goal', 'context_life', 'pattern_motivation', 'other'
            )
            AND text_he IS NOT NULL
            """
        )
        connection.exec_driver_sql(f"DROP TABLE {legacy_table}")
