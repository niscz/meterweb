from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from meterweb.domain.building import Building
from meterweb.domain.metering import MeterPoint, Reading, Unit


class BuildingRepository(ABC):
    @abstractmethod
    def add(self, building: Building) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Building]:
        raise NotImplementedError


class UnitRepository(ABC):
    @abstractmethod
    def add(self, unit: Unit) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Unit]:
        raise NotImplementedError


class MeterPointRepository(ABC):
    @abstractmethod
    def add(self, meter_point: MeterPoint) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[MeterPoint]:
        raise NotImplementedError


class MeterDeviceRepository(ABC):
    @abstractmethod
    def add_default_for_meter_point(self, meter_point_id: UUID) -> UUID:
        raise NotImplementedError


class MeterRegisterRepository(ABC):
    @abstractmethod
    def add_default_for_device(self, meter_device_id: UUID) -> UUID:
        raise NotImplementedError


class ReadingRepository(ABC):
    @abstractmethod
    def add_manual(self, meter_register_id: UUID, measured_at: datetime, value: Decimal) -> Reading:
        raise NotImplementedError

    @abstractmethod
    def add_photo(self, meter_register_id: UUID, measured_at: datetime, value: Decimal, image_path: str, ocr_confidence: float) -> Reading:
        raise NotImplementedError

    @abstractmethod
    def list_for_meter_register(self, meter_register_id: UUID) -> list[Reading]:
        raise NotImplementedError

    @abstractmethod
    def list_for_meter_point(self, meter_point_id: UUID) -> list[Reading]:
        raise NotImplementedError

    @abstractmethod
    def list_for_building(self, building_id: UUID) -> list[Reading]:
        raise NotImplementedError

    @abstractmethod
    def get_current_register_for_meter_point(self, meter_point_id: UUID) -> UUID | None:
        raise NotImplementedError


class WeatherStationRepository(ABC):
    @abstractmethod
    def get_override(self, building_id: UUID) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def set_override(self, building_id: UUID, station_id: str | None) -> None:
        raise NotImplementedError
