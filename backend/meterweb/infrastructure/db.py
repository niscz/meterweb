import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from meterweb.infrastructure.sqlalchemy_models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def configure_database(database_url: str | None = None) -> None:
    global _engine, _SessionLocal
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./meterweb.db")
    _engine = create_engine(url, connect_args={"check_same_thread": False})
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
