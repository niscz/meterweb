from abc import ABC, abstractmethod

from meterweb.domain.auth import Credentials, User
from meterweb.domain.building import Building


class Authenticator(ABC):
    @abstractmethod
    def authenticate(self, credentials: Credentials) -> User:
        raise NotImplementedError


class BuildingRepository(ABC):
    @abstractmethod
    def add(self, building: Building) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Building]:
        raise NotImplementedError
