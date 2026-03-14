from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from meterweb.application.dto import OCRCandidateDTO, OCRRunResultDTO, ReadingViewDTO
from meterweb.application.ports.weather_provider import WeatherSeriesPoint
from meterweb.interfaces.http.dependencies import get_add_photo_reading_use_case, get_ocr_run_use_case, get_weather_sync_use_case


def _setup_auth_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-32-characters!!")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))


def _client(tmp_path: Path) -> TestClient:
    from meterweb.main import create_app

    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/login", data={"username": "admin_user", "password": "SehrSicheresPasswort123"}, follow_redirects=False)
    assert response.status_code == 303


class _FakeOCRRunUseCase:
    def execute(self, _image_path):
        return OCRRunResultDTO(
            text="Meter 1234",
            candidates=[OCRCandidateDTO(value=Decimal("1234"), confidence=0.91)],
            best_candidate=OCRCandidateDTO(value=Decimal("1234"), confidence=0.91),
        )


class _FakePhotoUseCase:
    def execute(self, data, confirmed_value=None):
        reading = ReadingViewDTO(
            id=uuid4(),
            meter_register_id=data.meter_register_id,
            measured_at=data.measured_at,
            value=confirmed_value or Decimal("1234"),
            plausible=True,
        )
        ocr_result = OCRRunResultDTO(
            text="Meter 1234",
            candidates=[OCRCandidateDTO(value=Decimal("1234"), confidence=0.91)],
            best_candidate=OCRCandidateDTO(value=Decimal("1234"), confidence=0.91),
        )
        return reading, ocr_result, type("Plausibility", (), {"warning": None})()


class _FakeWeatherSyncUseCase:
    def __init__(self):
        self.calls = []

    def select_station(self, *_args, **_kwargs):
        return "station-1"

    def set_auto_station(self, *_args, **_kwargs):
        return None

    def set_manual_station(self, *_args, **_kwargs):
        return None

    def get_series(self, *_args, **_kwargs):
        self.calls.append((_args, _kwargs))
        return [WeatherSeriesPoint(timestamp="2025-01-01T00:00:00Z", temperature_c=2.0, cloud_cover_percent=55.0)]


def test_extended_v1_endpoints_and_validation(monkeypatch, tmp_path: Path) -> None:
    _setup_auth_env(monkeypatch, tmp_path)
    client = _client(tmp_path)

    weather_use_case = _FakeWeatherSyncUseCase()
    client.app.dependency_overrides[get_ocr_run_use_case] = lambda: _FakeOCRRunUseCase()
    client.app.dependency_overrides[get_add_photo_reading_use_case] = lambda: _FakePhotoUseCase()
    client.app.dependency_overrides[get_weather_sync_use_case] = lambda: weather_use_case

    unauth = client.post("/api/v1/ocr/run", json={"image_path": "x.png"})
    assert unauth.status_code == 401

    _login(client)

    building = client.post("/api/v1/buildings", json={"name": "Haus API"}).json()
    unit = client.post("/api/v1/units", json={"building_id": building["id"], "name": "WEG API"}).json()
    meter_point = client.post("/api/v1/meter-points", json={"unit_id": unit["id"], "name": "Strom"}).json()
    current_register = client.get(f"/api/v1/meter-points/{meter_point['id']}/current-register").json()

    ocr_run = client.post("/api/v1/ocr/run", json={"image_path": "tests/fixtures/meter.jpg"})
    assert ocr_run.status_code == 200
    assert ocr_run.json()["best_candidate"]["value"] == "1234"

    ocr_reading = client.post(
        "/api/v1/ocr/readings",
        json={
            "meter_register_id": current_register["meter_register_id"],
            "measured_at": "2025-01-01T00:00:00+00:00",
            "image_path": "tests/fixtures/meter.jpg",
            "confirmed_value": "1240",
        },
    )
    assert ocr_reading.status_code == 200
    assert ocr_reading.json()["reading"]["value"] == "1240"

    monthly = client.post("/api/v1/reports/monthly", json={"meter_register_id": current_register["meter_register_id"]})
    export_csv = client.post("/api/v1/reports/export/csv", json={"meter_register_id": current_register["meter_register_id"]})

    assert monthly.status_code == 200
    assert export_csv.status_code == 200
