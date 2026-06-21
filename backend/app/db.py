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
