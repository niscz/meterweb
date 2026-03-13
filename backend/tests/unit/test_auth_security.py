import pytest

from meterweb.domain.auth import AuthenticationError, Credentials
from meterweb.infrastructure.auth import EnvAuthenticator, validate_runtime_security_config


def test_create_app_fails_when_secret_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123!")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_runtime_security_config()


def test_create_app_fails_when_admin_password_missing(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "SehrSichererSecretKeyMit123!UndMehr")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        validate_runtime_security_config()


def test_create_app_fails_for_placeholder_admin_username(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "SehrSichererSecretKeyMit123!UndMehr")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123!")

    with pytest.raises(RuntimeError, match="ADMIN_USERNAME"):
        validate_runtime_security_config()


def test_create_app_fails_for_weak_admin_password(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "SehrSichererSecretKeyMit123!UndMehr")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "nurkleinbuchstaben")

    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        validate_runtime_security_config()


def test_create_app_fails_for_placeholder_secret_key(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "__SET_A_SECURE_SECRET_KEY_MIN_32_CHARS__")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123!")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_runtime_security_config()


def test_env_authenticator_uses_hashed_password(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123!")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_FILE", str(tmp_path / "admin.hash"))

    authenticator = EnvAuthenticator()

    assert (tmp_path / "admin.hash").exists()
    assert authenticator.authenticate(Credentials(username="admin_user", password="SehrSicheresPasswort123!")).username == "admin_user"

    with pytest.raises(AuthenticationError):
        authenticator.authenticate(Credentials(username="admin_user", password="falsches-passwort"))
