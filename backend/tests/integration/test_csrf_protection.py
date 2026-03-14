from pathlib import Path
import re

from fastapi.testclient import TestClient


def _client(tmp_path: Path) -> TestClient:
    from meterweb.main import create_app

    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)


def _setup_auth_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'meterweb.db'}")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-32-characters!!")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _login(client: TestClient) -> None:
    login_page = client.get("/login")
    csrf_token = _extract_csrf_token(login_page.text)
    response = client.post(
        "/login",
        data={"username": "admin_user", "password": "SehrSicheresPasswort123", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_login_rejects_missing_and_invalid_csrf_token(monkeypatch, tmp_path: Path) -> None:
    _setup_auth_env(monkeypatch, tmp_path)
    client = _client(tmp_path)

    missing = client.post("/login", data={"username": "admin_user", "password": "SehrSicheresPasswort123"}, follow_redirects=False)
    assert missing.status_code == 403
    assert missing.json()["detail"] == "Invalid CSRF token"

    client.get("/login")
    invalid = client.post(
        "/login",
        data={"username": "admin_user", "password": "SehrSicheresPasswort123", "csrf_token": "invalid-token"},
        follow_redirects=False,
    )
    assert invalid.status_code == 403
    assert invalid.json()["detail"] == "Invalid CSRF token"


def test_api_rejects_missing_and_invalid_csrf_token_for_authenticated_session(monkeypatch, tmp_path: Path) -> None:
    _setup_auth_env(monkeypatch, tmp_path)
    client = _client(tmp_path)
    _login(client)

    missing = client.post("/api/v1/buildings", json={"name": "Haus CSRF"})
    assert missing.status_code == 403
    assert missing.json()["detail"] == "Invalid CSRF token"

    invalid = client.post(
        "/api/v1/buildings",
        json={"name": "Haus CSRF"},
        headers={"X-CSRF-Token": "invalid-token"},
    )
    assert invalid.status_code == 403
    assert invalid.json()["detail"] == "Invalid CSRF token"

    dashboard = client.get("/dashboard")
    valid_token = _extract_csrf_token(dashboard.text)
    valid = client.post(
        "/api/v1/buildings",
        json={"name": "Haus CSRF"},
        headers={"X-CSRF-Token": valid_token},
    )
    assert valid.status_code == 200
