from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient


def _client(tmp_path: Path) -> TestClient:
    from meterweb.main import create_app

    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/login", data={"username": "admin_user", "password": "SehrSicheresPasswort123"}, follow_redirects=False)
    assert response.status_code == 303


def _setup_auth_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-32-characters!!")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))


def test_invalid_uuid_is_rejected_with_422(monkeypatch, tmp_path: Path) -> None:
    _setup_auth_env(monkeypatch, tmp_path)
    client = _client(tmp_path)
    _login(client)

    response = client.post("/api/v1/units", json={"building_id": "not-a-uuid", "name": "WEG 1"})

    assert response.status_code == 422


def test_negative_or_zero_reading_values_are_rejected_with_422(monkeypatch, tmp_path: Path) -> None:
    _setup_auth_env(monkeypatch, tmp_path)
    client = _client(tmp_path)
    _login(client)

    building = client.post("/api/v1/buildings", json={"name": "Haus C"}).json()
    unit = client.post("/api/v1/units", json={"building_id": building["id"], "name": "WEG 3"}).json()
    meter_point = client.post("/api/v1/meter-points", json={"unit_id": unit["id"], "name": "Strom"}).json()
    current_register = client.get(f"/api/v1/meter-points/{meter_point['id']}/current-register").json()

    response = client.post(
        "/api/v1/readings",
        json={"meter_register_id": current_register["meter_register_id"], "measured_at": "2025-01-01T00:00:00+00:00", "value": "0"},
    )

    assert response.status_code == 422


def test_unknown_reference_returns_400(monkeypatch, tmp_path: Path) -> None:
    _setup_auth_env(monkeypatch, tmp_path)
    client = _client(tmp_path)
    _login(client)

    response = client.post(
        "/api/v1/readings",
        json={
            "meter_register_id": str(uuid4()),
            "measured_at": "2025-01-01T00:00:00+00:00",
            "value": "100",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Zählwerk existiert nicht."
