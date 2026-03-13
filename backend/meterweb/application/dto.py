from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LoginDTO:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class BuildingCreateDTO:
    name: str


@dataclass(frozen=True, slots=True)
class UnitCreateDTO:
    building_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class MeterPointCreateDTO:
    unit_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ReadingCreateDTO:
    meter_point_id: UUID
    measured_at: datetime
    value: Decimal


@dataclass(frozen=True, slots=True)
class BuildingViewDTO:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class UnitViewDTO:
    id: UUID
    building_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class MeterPointViewDTO:
    id: UUID
    unit_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ReadingViewDTO:
    id: UUID
    meter_point_id: UUID
    measured_at: datetime
    value: Decimal
    plausible: bool


@dataclass(frozen=True, slots=True)
class AnalyticsViewDTO:
    meter_point_id: UUID
    consumption: Decimal
    cost: Decimal
