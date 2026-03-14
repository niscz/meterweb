from pathlib import Path
import re

from fastapi.testclient import TestClient


def _client(tmp_path: Path) -> TestClient:
    from meterweb.main import create_app

    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)




def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _csrf_headers(client: TestClient) -> dict[str, str]:
    page = client.get("/dashboard")
    token = _extract_csrf_token(page.text)
    return {"X-CSRF-Token": token}

def _login(client: TestClient) -> None:
    login_page = client.get("/login")
    csrf_token = _extract_csrf_token(login_page.text)
    response = client.post("/login", data={"username": "admin_user", "password": "SehrSicheresPasswort123", "csrf_token": csrf_token}, follow_redirects=False)
    assert response.status_code == 303


def test_masterdata_and_reading_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-32-characters!!")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))

    client = _client(tmp_path)
    _login(client)

    building = client.post("/api/v1/buildings", headers=_csrf_headers(client), json={"name": "Haus A"}).json()
    unit = client.post("/api/v1/units", headers=_csrf_headers(client), json={"building_id": building["id"], "name": "WEG 1"}).json()
    meter_point = client.post("/api/v1/meter-points", headers=_csrf_headers(client), json={"unit_id": unit["id"], "name": "Strom"}).json()
    current_register = client.get(f"/api/v1/meter-points/{meter_point['id']}/current-register").json()

    first = client.post(
        "/api/v1/readings", headers=_csrf_headers(client),
        json={"meter_register_id": current_register["meter_register_id"], "measured_at": "2025-01-01T00:00:00+00:00", "value": "100"},
    )
    second = client.post(
        "/api/v1/readings", headers=_csrf_headers(client),
        json={"meter_register_id": current_register["meter_register_id"], "measured_at": "2025-02-01T00:00:00+00:00", "value": "140"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["plausible"] is True

    analytics = client.get(f"/api/v1/analytics/{meter_point['id']}?price_per_unit=0.5")
    assert analytics.status_code == 200
    assert analytics.json()["consumption"] == "40.000000"


def test_reading_plausibility_flags_negative_delta(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-32-characters!!")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))

    client = _client(tmp_path)
    _login(client)

    building = client.post("/api/v1/buildings", headers=_csrf_headers(client), json={"name": "Haus B"}).json()
    unit = client.post("/api/v1/units", headers=_csrf_headers(client), json={"building_id": building["id"], "name": "WEG 2"}).json()
    meter_point = client.post("/api/v1/meter-points", headers=_csrf_headers(client), json={"unit_id": unit["id"], "name": "Wasser"}).json()
    current_register = client.get(f"/api/v1/meter-points/{meter_point['id']}/current-register").json()

    client.post(
        "/api/v1/readings", headers=_csrf_headers(client),
        json={"meter_register_id": current_register["meter_register_id"], "measured_at": "2025-01-01T00:00:00+00:00", "value": "100"},
    )
    second = client.post(
        "/api/v1/readings", headers=_csrf_headers(client),
        json={"meter_register_id": current_register["meter_register_id"], "measured_at": "2025-02-01T00:00:00+00:00", "value": "90"},
    )

    assert second.status_code == 200
    assert second.json()["plausible"] is False
