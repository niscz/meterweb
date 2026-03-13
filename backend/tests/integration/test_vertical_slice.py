from pathlib import Path

from fastapi.testclient import TestClient

from meterweb.main import create_app


def _client(tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=False)
    assert response.status_code == 303


def test_masterdata_and_reading_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin")

    client = _client(tmp_path)
    _login(client)

    building = client.post("/api/v1/buildings", json={"name": "Haus A"}).json()
    unit = client.post("/api/v1/units", json={"building_id": building["id"], "name": "WEG 1"}).json()
    meter_point = client.post("/api/v1/meter-points", json={"unit_id": unit["id"], "name": "Strom"}).json()

    first = client.post(
        "/api/v1/readings",
        json={"meter_point_id": meter_point["id"], "measured_at": "2025-01-01T00:00:00+00:00", "value": "100"},
    )
    second = client.post(
        "/api/v1/readings",
        json={"meter_point_id": meter_point["id"], "measured_at": "2025-02-01T00:00:00+00:00", "value": "140"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["plausible"] is True

    analytics = client.get(f"/api/v1/analytics/{meter_point['id']}?price_per_unit=0.5")
    assert analytics.status_code == 200
    assert analytics.json()["consumption"] == "40.000000"


def test_reading_plausibility_flags_negative_delta(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin")

    client = _client(tmp_path)
    _login(client)

    building = client.post("/api/v1/buildings", json={"name": "Haus B"}).json()
    unit = client.post("/api/v1/units", json={"building_id": building["id"], "name": "WEG 2"}).json()
    meter_point = client.post("/api/v1/meter-points", json={"unit_id": unit["id"], "name": "Wasser"}).json()

    client.post(
        "/api/v1/readings",
        json={"meter_point_id": meter_point["id"], "measured_at": "2025-01-01T00:00:00+00:00", "value": "100"},
    )
    second = client.post(
        "/api/v1/readings",
        json={"meter_point_id": meter_point["id"], "measured_at": "2025-02-01T00:00:00+00:00", "value": "90"},
    )

    assert second.status_code == 200
    assert second.json()["plausible"] is False
