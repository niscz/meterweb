import os
import secrets

from meterweb.application.ports import Authenticator
from meterweb.domain.auth import AuthenticationError, Credentials, User


class EnvAuthenticator(Authenticator):
    def __init__(self) -> None:
        self._username = os.getenv("ADMIN_USERNAME", "admin")
        self._password = os.getenv("ADMIN_PASSWORD", "admin")

    def authenticate(self, credentials: Credentials) -> User:
        valid_user = secrets.compare_digest(credentials.username, self._username)
        valid_pass = secrets.compare_digest(credentials.password, self._password)
        if not (valid_user and valid_pass):
            raise AuthenticationError("Ungültiger Login")
        return User(username=credentials.username)
