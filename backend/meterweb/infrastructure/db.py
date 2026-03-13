import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from meterweb.infrastructure.sqlalchemy_models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def configure_database(database_url: str | None = None) -> None:
    global _engine, _SessionLocal
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./meterweb.db")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, connect_args=connect_args)

    if url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            cursor.close()

    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def _ensure_configured() -> None:
    if _engine is None or _SessionLocal is None:
        configure_database()


def init_db() -> None:
    _ensure_configured()
    Base.metadata.create_all(bind=_engine)


def get_session() -> Generator[Session, None, None]:
    _ensure_configured()
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
