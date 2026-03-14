from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from meterweb.infrastructure import db as db_module
from meterweb.infrastructure.sqlalchemy_models import UnitRecord


def test_sqlite_foreign_key_violation_raises_integrity_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(db_module, "_engine", None)
    monkeypatch.setattr(db_module, "_SessionLocal", None)

    db_url = f"sqlite:///{tmp_path / 'fk_test.db'}"
    db_module.configure_database(db_url)
    db_module.init_db()

    session_gen = db_module.get_session()
    session = next(session_gen)

    try:
        session.add(
            UnitRecord(
                id=str(uuid4()),
                building_id=str(uuid4()),
                name="FK-Verstoß",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()
        session_gen.close()
