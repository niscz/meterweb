from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from meterweb.application.dto import OCRCandidateDTO, OCRRunResultDTO, ReadingViewDTO
from meterweb.application.ports.weather_provider import WeatherSeriesPoint
from meterweb.infrastructure.db import init_db
from meterweb.interfaces.http.dependencies import (
    get_add_photo_reading_use_case,
    get_confirm_reading_use_case,
    get_correct_reading_use_case,
    get_ocr_accept_use_case,
    get_ocr_reject_use_case,
    get_ocr_run_use_case,
    get_weather_sync_use_case,
)


def _setup_auth_env(monkeypatch, tmp_path: Path) -> None:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "Test-secret-key-with-32-characters1!")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123!")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "false")
    monkeypatch.setenv("UPLOADS_DIR", str(uploads_dir))


def _client(tmp_path: Path) -> TestClient:
    from meterweb.main import create_app

    app = create_app()
    init_db()
    app.dependency_overrides = {}
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/login", data={"username": "admin_user", "password": "SehrSicheresPasswort123!"}, follow_redirects=False)
    assert response.status_code == 303


class _FakeOCRRunUseCase:
    def execute(self, _image_path):
        return OCRRunResultDTO(
            text="Meter 1234",
            candidates=[OCRCandidateDTO(value=Decimal("1234"), confidence=0.91)],
            best_candidate=OCRCandidateDTO(value=Decimal("1234"), confidence=0.91),
        )


class _FakePhotoUseCase:
    def __init__(self):
        self.last_reading_id = uuid4()

    def execute(self, data, confirmed_value=None):
        reading = ReadingViewDTO(
            id=self.last_reading_id,
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




class _FakeConfirmUseCase:
    def execute(self, data):
        return ReadingViewDTO(
            id=data.reading_id,
            meter_register_id=uuid4(),
            measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            value=Decimal("1240"),
            plausible=True,
        )


class _FakeCorrectUseCase:
    def execute(self, data):
        return ReadingViewDTO(
            id=data.reading_id,
            meter_register_id=uuid4(),
            measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            value=data.value,
            plausible=True,
        )


class _FakeOCRDecisionUseCase:
    def __init__(self, status: str):
        self._status = status

    def execute(self, _data):
        return type("Meta", (), {
            "image_path": "tests/fixtures/meter.jpg",
            "ocr_confidence": 0.91,
            "ocr_text": "Meter 1234",
            "ocr_candidates": [OCRCandidateDTO(value=Decimal("1234"), confidence=0.91)],
            "ocr_status": self._status,
        })()

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
    fake_photo_use_case = _FakePhotoUseCase()
    client.app.dependency_overrides[get_ocr_run_use_case] = lambda: _FakeOCRRunUseCase()
    client.app.dependency_overrides[get_add_photo_reading_use_case] = lambda: fake_photo_use_case
    client.app.dependency_overrides[get_confirm_reading_use_case] = lambda: _FakeConfirmUseCase()
    client.app.dependency_overrides[get_correct_reading_use_case] = lambda: _FakeCorrectUseCase()
    client.app.dependency_overrides[get_ocr_accept_use_case] = lambda: _FakeOCRDecisionUseCase("accepted")
    client.app.dependency_overrides[get_ocr_reject_use_case] = lambda: _FakeOCRDecisionUseCase("rejected")
    client.app.dependency_overrides[get_weather_sync_use_case] = lambda: weather_use_case

    unauth = client.post("/api/v1/ocr/run", json={"image_path": "x.png"})
    assert unauth.status_code == 401

    _login(client)

    building = client.post("/api/v1/buildings", json={"name": "Haus API"}).json()
    unit = client.post("/api/v1/units", json={"building_id": building["id"], "name": "WEG API"}).json()
    meter_point = client.post("/api/v1/meter-points", json={"unit_id": unit["id"], "name": "Strom"}).json()
    current_register = client.get(f"/api/v1/meter-points/{meter_point['id']}/current-register").json()

    upload_image_path = str((tmp_path / "uploads" / "meter.jpg").resolve())

    ocr_run = client.post("/api/v1/ocr/run", json={"image_path": upload_image_path})
    assert ocr_run.status_code == 200
    assert ocr_run.json()["best_candidate"]["value"] == "1234"

    ocr_reading = client.post(
        "/api/v1/ocr/readings",
        json={
            "meter_register_id": current_register["meter_register_id"],
            "measured_at": "2025-01-01T00:00:00+00:00",
            "image_path": upload_image_path,
            "confirmed_value": "1240",
        },
    )
    assert ocr_reading.status_code == 200
    assert ocr_reading.json()["reading"]["value"] == "1240"


    blocked_ocr_run = client.post("/api/v1/ocr/run", json={"image_path": "../etc/passwd"})
    assert blocked_ocr_run.status_code == 400
    assert "innerhalb des Upload-Verzeichnisses" in blocked_ocr_run.json()["detail"]

    blocked_ocr_reading = client.post(
        "/api/v1/ocr/readings",
        json={
            "meter_register_id": current_register["meter_register_id"],
            "measured_at": "2025-01-02T00:00:00+00:00",
            "image_path": "/tmp/escape.jpg",
            "confirmed_value": "1240",
        },
    )
    assert blocked_ocr_reading.status_code == 400
    assert "innerhalb des Upload-Verzeichnisses" in blocked_ocr_reading.json()["detail"]


    confirm_resp = client.post(f"/api/v1/readings/{fake_photo_use_case.last_reading_id}/confirm")
    assert confirm_resp.status_code == 200

    correct_resp = client.post(
        f"/api/v1/readings/{fake_photo_use_case.last_reading_id}/correct",
        json={"value": "1250"},
    )
    assert correct_resp.status_code == 200
    assert correct_resp.json()["value"] == "1250"

    ocr_accept = client.post(f"/api/v1/ocr/{fake_photo_use_case.last_reading_id}/accept")
    assert ocr_accept.status_code == 200
    assert ocr_accept.json()["status"] == "accepted"

    ocr_reject = client.post(f"/api/v1/ocr/{fake_photo_use_case.last_reading_id}/reject")
    assert ocr_reject.status_code == 200
    assert ocr_reject.json()["status"] == "rejected"

    invalid_series_resolution = client.get(
        f"/api/v1/weather/buildings/{building['id']}/series",
        params={
            "lat": 48.1,
            "lon": 11.5,
            "start_date": "2025-01-01",
            "end_date": "2025-01-02",
            "resolution": "weekly",
        },
    )
    assert invalid_series_resolution.status_code == 422

    invalid_series_range = client.get(
        f"/api/v1/weather/buildings/{building['id']}/series",
        params={
            "lat": 48.1,
            "lon": 11.5,
            "start_date": "2025-01-03",
            "end_date": "2025-01-02",
            "resolution": "daily",
        },
    )
    assert invalid_series_range.status_code == 422

    invalid_sync_resolution = client.post(
        f"/api/v1/weather/buildings/{building['id']}/sync",
        json={"lat": 48.1, "lon": 11.5, "resolutions": ["weekly"]},
    )
    assert invalid_sync_resolution.status_code == 422

    monthly = client.post("/api/v1/reports/monthly", json={"meter_register_id": current_register["meter_register_id"]})
    export_csv = client.post("/api/v1/reports/export/csv", json={"meter_register_id": current_register["meter_register_id"]})

    assert monthly.status_code == 200
    assert export_csv.status_code == 200
