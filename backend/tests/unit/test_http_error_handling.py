from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from starlette.requests import Request

from meterweb.application.dto import UnitViewDTO
from meterweb.application.errors import UpstreamServiceError
from meterweb.interfaces.http.api.v1 import router as api_router
from meterweb.interfaces.http.errors import register_exception_handlers
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


def test_create_unit_wrapper_returns_unit_response_shape(monkeypatch) -> None:
    monkeypatch.setattr(api_router, "require_auth", lambda request: "admin")
    unit_id = uuid4()
    building_id = uuid4()

    class DummyUseCase:
        def execute(self, _data):
            return UnitViewDTO(id=unit_id, building_id=building_id, name="WEG 1")

    response = api_router.create_unit(
        request=_request("/api/v1/units"),
        payload=UnitCreateRequest(building_id=building_id, name="WEG 1"),
        use_case=DummyUseCase(),
    )

    assert response.id == str(unit_id)
    assert response.building_id == str(building_id)
    assert response.name == "WEG 1"


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


def test_dashboard_create_building_wrapper_redirects_on_success(monkeypatch) -> None:
    monkeypatch.setattr(web_router, "require_auth", lambda request: "admin")

    class SuccessfulCreateBuildingUseCase:
        def execute(self, _data):
            return None

    class EmptyListUseCase:
        def execute(self):
            return []

    response = web_router.create_building(
        request=_request("/dashboard/buildings"),
        name="Haus A",
        use_case=SuccessfulCreateBuildingUseCase(),
        list_buildings=EmptyListUseCase(),
        list_units=EmptyListUseCase(),
        list_meter_points=EmptyListUseCase(),
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/dashboard"


@pytest.mark.anyio
async def test_upstream_service_error_maps_to_bad_gateway() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    handler = app.exception_handlers[UpstreamServiceError]
    request = Request({"type": "http", "method": "GET", "path": "/api/v1/weather", "headers": [], "query_string": b""})
    response = await handler(request, UpstreamServiceError("Bright Sky Wetterserienabruf fehlgeschlagen."))

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.body == b'{"detail":"Bright Sky Wetterserienabruf fehlgeschlagen."}'
