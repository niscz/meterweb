from uuid import uuid4

import pytest

import meterweb.interfaces.http.web.readings_router as readings_router


class _FakeRepo:
    def __init__(self, register_id=None):
        self._register_id = register_id

    def get_current_register_for_meter_point(self, _meter_point_id):
        return self._register_id


def test_resolve_register_id_accepts_direct_meter_register_id() -> None:
    register_id = uuid4()
    resolved = readings_router._resolve_register_id(session=None, meter_register_id=str(register_id), meter_point_id=None)
    assert resolved == register_id


def test_resolve_register_id_supports_meter_point_fallback(monkeypatch) -> None:
    register_id = uuid4()
    monkeypatch.setattr(readings_router, "SqlAlchemyReadingRepository", lambda _session: _FakeRepo(register_id))

    resolved = readings_router._resolve_register_id(session=object(), meter_register_id=None, meter_point_id=str(uuid4()))

    assert resolved == register_id


def test_resolve_register_id_raises_when_no_active_register(monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "SqlAlchemyReadingRepository", lambda _session: _FakeRepo(None))

    with pytest.raises(ValueError, match="kein aktives Register"):
        readings_router._resolve_register_id(session=object(), meter_register_id=None, meter_point_id=str(uuid4()))
