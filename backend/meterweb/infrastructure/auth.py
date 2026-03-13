import base64
import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path

from meterweb.application.ports import Authenticator
from meterweb.domain.auth import AuthenticationError, Credentials, User

MIN_ADMIN_USERNAME_LENGTH = 3
MIN_ADMIN_PASSWORD_LENGTH = 12
MIN_SECRET_KEY_LENGTH = 32
PASSWORD_COMPLEXITY_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$")
SECRET_KEY_COMPLEXITY_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$")
PLACEHOLDER_TOKENS = (
    "changeme",
    "change-me",
    "replace",
    "placeholder",
    "example",
    "set-me",
    "set_me",
    "please-change",
    "default",
)
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16


class EnvAuthenticator(Authenticator):
    def __init__(self) -> None:
        self._username = _require_env("ADMIN_USERNAME", min_length=MIN_ADMIN_USERNAME_LENGTH)
        _require_not_placeholder("ADMIN_USERNAME", self._username)

        admin_password = _require_env("ADMIN_PASSWORD", min_length=MIN_ADMIN_PASSWORD_LENGTH)
        _require_not_placeholder("ADMIN_PASSWORD", admin_password)
        if not PASSWORD_COMPLEXITY_PATTERN.match(admin_password):
            raise RuntimeError(
                "Environment variable ADMIN_PASSWORD must include at least one lowercase letter, "
                "one uppercase letter, one digit, and one special character"
            )

        hash_file = Path(os.getenv("ADMIN_PASSWORD_HASH_FILE", ".meterweb_admin_password.hash"))
        self._password_hash = _load_or_initialize_password_hash(hash_file, admin_password)

    def authenticate(self, credentials: Credentials) -> User:
        valid_user = secrets.compare_digest(credentials.username, self._username)
        valid_pass = _verify_password(credentials.password, self._password_hash)
        if not (valid_user and valid_pass):
            raise AuthenticationError("Ungültiger Login")
        return User(username=credentials.username)


def validate_runtime_security_config() -> str:
    secret_key = _require_env("SECRET_KEY", min_length=MIN_SECRET_KEY_LENGTH)
    _require_not_placeholder("SECRET_KEY", secret_key)
    if not SECRET_KEY_COMPLEXITY_PATTERN.match(secret_key):
        raise RuntimeError(
            "Environment variable SECRET_KEY must include at least one lowercase letter, "
            "one uppercase letter, one digit, and one special character"
        )

    EnvAuthenticator()
    return secret_key


def _require_env(name: str, *, min_length: int) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    if len(value) < min_length:
        raise RuntimeError(f"Environment variable {name} must be at least {min_length} characters long")
    return value


def _require_not_placeholder(name: str, value: str) -> None:
    normalized = value.strip().lower()
    if normalized in {"admin", "please-change-me"}:
        raise RuntimeError(f"Environment variable {name} uses an insecure default value")

    if "<" in value or ">" in value or "__" in value:
        raise RuntimeError(f"Environment variable {name} appears to be an unreplaced placeholder value")

    if any(token in normalized for token in PLACEHOLDER_TOKENS):
        raise RuntimeError(f"Environment variable {name} appears to be an unreplaced placeholder value")


def _load_or_initialize_password_hash(hash_file: Path, admin_password: str) -> str:
    if hash_file.exists():
        stored_hash = hash_file.read_text(encoding="utf-8").strip()
        if not stored_hash:
            raise RuntimeError(f"Password hash file is empty: {hash_file}")
        if not _verify_password(admin_password, stored_hash):
            raise RuntimeError(
                "ADMIN_PASSWORD does not match the existing admin password hash. "
                "Set the correct password or remove ADMIN_PASSWORD_HASH_FILE for a controlled re-bootstrap."
            )
        return stored_hash

    hash_file.parent.mkdir(parents=True, exist_ok=True)
    generated_hash = _hash_password(admin_password)
    hash_file.write_text(generated_hash, encoding="utf-8")
    os.chmod(hash_file, 0o600)
    return generated_hash


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64(salt)}${_b64(digest)}"


def _verify_password(password: str, encoded_hash: str) -> bool:
    algorithm, iteration_s, salt_b64, digest_b64 = encoded_hash.split("$", 3)
    if algorithm != "pbkdf2_sha256":
        raise RuntimeError("Unsupported admin password hash algorithm")

    iterations = int(iteration_s)
    salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
    expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))

    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(derived, expected)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii")
