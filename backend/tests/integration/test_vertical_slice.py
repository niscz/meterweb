from pathlib import Path

from fastapi.testclient import TestClient

from meterweb.main import create_app


def _client_with_temp_db(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "test.db"
    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)


def test_login_and_create_building_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin")

    client = TestClient(create_app())

    login_response = client.post(
        "/login", data={"username": "admin", "password": "admin"}, follow_redirects=False
    )
    assert login_response.status_code == 303

    create_response = client.post(
        "/buildings", data={"name": "Haus A"}, follow_redirects=False
    )
    assert create_response.status_code == 303

    list_response = client.get("/api/v1/buildings")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "Haus A"
