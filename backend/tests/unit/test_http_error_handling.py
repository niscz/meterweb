from uuid import uuid4

import pytest
from fastapi import status
from starlette.requests import Request

from meterweb.application.dto import UnitViewDTO
from meterweb.interfaces.http.api.v1 import router as api_router
from meterweb.interfaces.http.schemas import UnitCreateRequest
from meterweb.interfaces.http.web import router as web_router


def _request(path: str) -> Request:
    return Request({"type": "http", "method": "POST", "path": path, "headers": [], "query_string": b"", "session": {}})


def test_create_unit_propagates_domain_validation_error(monkeypatch) -> None:
    monkeypatch.setattr(api_router, "require_auth", lambda request: "admin")

    class DummyUseCase:
        def execute(self, _data):
            raise ValueError("Referenz auf Gebäude unbekannt.")

    with pytest.raises(ValueError):
        api_router.create_unit(
            request=_request("/api/v1/units"),
            payload=UnitCreateRequest(building_id=uuid4(), name="WEG 1"),
            use_case=DummyUseCase(),
        )


def test_dashboard_create_building_returns_validation_response(monkeypatch) -> None:
    monkeypatch.setattr(web_router, "require_auth", lambda request: "admin")
    monkeypatch.setattr(web_router, "get_locale", lambda request: "de")

    class FailingCreateBuildingUseCase:
        def execute(self, _data):
            raise ValueError("Gebäudename existiert bereits.")

    class EmptyListUseCase:
        def execute(self):
            return []

    response = web_router.create_building(
        request=_request("/dashboard/buildings"),
        name="Haus A",
        use_case=FailingCreateBuildingUseCase(),
        list_buildings=EmptyListUseCase(),
        list_units=EmptyListUseCase(),
        list_meter_points=EmptyListUseCase(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
