from meterweb.application.dto import LoginDTO
from meterweb.application.ports import Authenticator
from meterweb.domain.auth import Credentials, User


class LoginUseCase:
    def __init__(self, authenticator: Authenticator) -> None:
        self._authenticator = authenticator

    def execute(self, data: LoginDTO) -> User:
        return self._authenticator.authenticate(
            Credentials(username=data.username, password=data.password)
        )
