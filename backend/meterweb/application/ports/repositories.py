from abc import ABC, abstractmethod

from meterweb.domain.building import Building


class BuildingRepository(ABC):
    @abstractmethod
    def add(self, building: Building) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Building]:
        raise NotImplementedError
