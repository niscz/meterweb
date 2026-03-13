from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class User:
    username: str


class AuthenticationError(Exception):
    """Raised when authentication fails."""
