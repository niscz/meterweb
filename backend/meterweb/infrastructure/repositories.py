import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from meterweb.application.ports import BuildingRepository, MeterPointRepository, ReadingRepository, UnitRepository, WeatherStationRepository
from meterweb.domain.building import Building, BuildingName
from meterweb.domain.metering import MeterPoint, Reading, Unit
from meterweb.infrastructure.sqlalchemy_models import (
    BuildingRecord,
    MeterDeviceRecord,
    MeterPointRecord,
    MeterRegisterRecord,
    ReadingRecord,
    UnitRecord,
)


class SqlAlchemyBuildingRepository(BuildingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, building: Building) -> None:
        self._session.add(BuildingRecord(id=str(building.id), name=building.name.value))
        self._session.commit()

    def list_all(self) -> list[Building]:
        rows = self._session.scalars(select(BuildingRecord).order_by(BuildingRecord.name)).all()
        return [Building(id=UUID(row.id), name=BuildingName(row.name)) for row in rows]


class SqlAlchemyUnitRepository(UnitRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, unit: Unit) -> None:
        self._session.add(UnitRecord(id=str(unit.id), building_id=str(unit.building_id), name=unit.name))
        self._session.commit()

    def list_all(self) -> list[Unit]:
        rows = self._session.scalars(select(UnitRecord).order_by(UnitRecord.name)).all()
        return [Unit(id=UUID(r.id), building_id=UUID(r.building_id), name=r.name) for r in rows]


class SqlAlchemyMeterPointRepository(MeterPointRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, meter_point: MeterPoint) -> None:
        self._session.add(MeterPointRecord(id=str(meter_point.id), unit_id=str(meter_point.unit_id), name=meter_point.name))
        device_id = str(uuid4())
        self._session.add(
            MeterDeviceRecord(
                id=device_id,
                meter_point_id=str(meter_point.id),
                serial_number=f"AUTO-{str(meter_point.id)[:8]}",
                installed_at=datetime.now(timezone.utc),
                removed_at=None,
            )
        )
        self._session.add(
            MeterRegisterRecord(
                id=str(uuid4()),
                meter_device_id=device_id,
                code="MAIN",
                measurement_unit="kWh",
                rollover_limit=None,
            )
        )
        self._session.commit()

    def list_all(self) -> list[MeterPoint]:
        rows = self._session.scalars(select(MeterPointRecord).order_by(MeterPointRecord.name)).all()
        return [MeterPoint(id=UUID(r.id), unit_id=UUID(r.unit_id), name=r.name) for r in rows]


class SqlAlchemyReadingRepository(ReadingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_manual(self, meter_point_id: UUID, measured_at: datetime, value: Decimal) -> Reading:
        return self._add_reading(meter_point_id, measured_at, value, source="manual")

    def add_photo(self, meter_point_id: UUID, measured_at: datetime, value: Decimal, image_path: str, ocr_confidence: float) -> Reading:
        del image_path, ocr_confidence
        return self._add_reading(meter_point_id, measured_at, value, source="photo")

    def _add_reading(self, meter_point_id: UUID, measured_at: datetime, value: Decimal, source: str) -> Reading:
        register_id = self._session.scalar(
            select(MeterRegisterRecord.id)
            .join(MeterDeviceRecord, MeterRegisterRecord.meter_device_id == MeterDeviceRecord.id)
            .where(MeterDeviceRecord.meter_point_id == str(meter_point_id), MeterDeviceRecord.removed_at.is_(None))
            .limit(1)
        )
        if register_id is None:
            raise ValueError("Messpunkt hat kein aktives Register.")
        reading = Reading(id=uuid4(), meter_register_id=UUID(register_id), measured_at=measured_at, value=value)
        self._session.add(
            ReadingRecord(
                id=str(reading.id),
                meter_register_id=register_id,
                measured_at=reading.measured_at,
                value=reading.value,
                source=source,
            )
        )
        self._session.commit()
        return reading

    def list_for_meter_point(self, meter_point_id: UUID) -> list[Reading]:
        rows = self._session.scalars(
            select(ReadingRecord)
            .join(MeterRegisterRecord, ReadingRecord.meter_register_id == MeterRegisterRecord.id)
            .join(MeterDeviceRecord, MeterRegisterRecord.meter_device_id == MeterDeviceRecord.id)
            .where(MeterDeviceRecord.meter_point_id == str(meter_point_id))
            .order_by(ReadingRecord.measured_at)
        ).all()
        return [Reading(id=UUID(r.id), meter_register_id=UUID(r.meter_register_id), measured_at=r.measured_at, value=r.value) for r in rows]


class JsonWeatherStationRepository(WeatherStationRepository):
    def __init__(self, storage_file: Path) -> None:
        self._storage_file = storage_file
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)

    def get_override(self, building_id: UUID) -> str | None:
        payload = self._load()
        return payload.get(str(building_id))

    def set_override(self, building_id: UUID, station_id: str | None) -> None:
        payload = self._load()
        if station_id is None:
            payload.pop(str(building_id), None)
        else:
            payload[str(building_id)] = station_id
        self._storage_file.write_text(json.dumps(payload), encoding="utf-8")

    def _load(self) -> dict[str, str]:
        if not self._storage_file.exists():
            return {}
        return json.loads(self._storage_file.read_text(encoding="utf-8"))
