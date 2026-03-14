from datetime import datetime, timedelta

import pytest

from meterweb.domain.auth import AuthenticationError, Credentials
from meterweb.infrastructure.auth import EnvAuthenticator, validate_runtime_security_config
from meterweb.interfaces.http.web.auth_security import LoginAttemptGuard


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


def test_create_app_accepts_secret_key_containing_example_substring(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "MyExampleSecret123!MitZusatzLang")
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_PASSWORD", "SehrSicheresPasswort123!")

    validate_runtime_security_config()


def test_create_app_fails_for_angle_bracket_placeholder_secret_key(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "<SET_A_SECURE_SECRET_KEY>")
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


def test_login_attempt_guard_allows_normal_login_after_success() -> None:
    guard = LoginAttemptGuard(max_attempts=3, window_seconds=60, lock_duration_seconds=120)

    guard.register_failure("account:admin")
    guard.register_success("account:admin")

    assert guard.is_locked("account:admin") is False


def test_login_attempt_guard_locks_after_repeated_failures() -> None:
    guard = LoginAttemptGuard(max_attempts=3, window_seconds=60, lock_duration_seconds=120)
    start = datetime(2026, 1, 1, 12, 0, 0)

    guard.register_failure("ip:127.0.0.1", now=start)
    guard.register_failure("ip:127.0.0.1", now=start + timedelta(seconds=10))
    guard.register_failure("ip:127.0.0.1", now=start + timedelta(seconds=20))

    assert guard.is_locked("ip:127.0.0.1", now=start + timedelta(seconds=30)) is True


def test_login_attempt_guard_unlocks_after_lock_duration_elapsed() -> None:
    guard = LoginAttemptGuard(max_attempts=2, window_seconds=60, lock_duration_seconds=30)
    start = datetime(2026, 1, 1, 12, 0, 0)

    guard.register_failure("account:admin", now=start)
    guard.register_failure("account:admin", now=start + timedelta(seconds=5))

    assert guard.is_locked("account:admin", now=start + timedelta(seconds=20)) is True
    assert guard.is_locked("account:admin", now=start + timedelta(seconds=36)) is False


def test_login_attempt_guard_evicts_stale_attempt_buckets() -> None:
    guard = LoginAttemptGuard(max_attempts=3, window_seconds=10, lock_duration_seconds=30)
    start = datetime(2026, 1, 1, 12, 0, 0)

    guard.register_failure("account:random-user", now=start)
    assert "account:random-user" in guard._buckets

    guard.is_locked("account:other", now=start + timedelta(seconds=11))

    assert "account:random-user" not in guard._buckets


def test_login_attempt_guard_register_success_removes_bucket() -> None:
    guard = LoginAttemptGuard(max_attempts=3, window_seconds=60, lock_duration_seconds=30)
    start = datetime(2026, 1, 1, 12, 0, 0)

    guard.register_failure("account:admin", now=start)
    assert "account:admin" in guard._buckets

    guard.register_success("account:admin", now=start + timedelta(seconds=1))

    assert "account:admin" not in guard._buckets
