from abc import ABC, abstractmethod

from meterweb.application.ports.repositories import (
    BuildingRepository,
    MeterDeviceRepository,
    MeterPointRepository,
    MeterRegisterRepository,
    ReadingRepository,
    UnitRepository,
)


class UnitOfWork(ABC):
    building_repository: BuildingRepository
    unit_repository: UnitRepository
    meter_point_repository: MeterPointRepository
    meter_device_repository: MeterDeviceRepository
    meter_register_repository: MeterRegisterRepository
    reading_repository: ReadingRepository

    @abstractmethod
    def begin(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError
