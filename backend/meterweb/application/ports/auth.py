from abc import ABC, abstractmethod

from meterweb.domain.auth import Credentials, User


class Authenticator(ABC):
    @abstractmethod
    def authenticate(self, credentials: Credentials) -> User:
        raise NotImplementedError
