import json
import logging
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from meterweb.application.dto import OCRCandidateDTO, ReadingOCRMetadataDTO
from meterweb.application.ports import BuildingRepository, MeterPointRepository, ReadingRepository, UnitRepository, WeatherStationRepository
from meterweb.application.ports.repositories import MeterDeviceRepository, MeterRegisterRepository
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


logger = logging.getLogger(__name__)


class SqlAlchemyBuildingRepository(BuildingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, building: Building) -> None:
        self._session.add(BuildingRecord(id=str(building.id), name=building.name.value))

    def list_all(self) -> list[Building]:
        rows = self._session.scalars(select(BuildingRecord).order_by(BuildingRecord.name)).all()
        return [Building(id=UUID(row.id), name=BuildingName(row.name)) for row in rows]


class SqlAlchemyUnitRepository(UnitRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, unit: Unit) -> None:
        self._session.add(UnitRecord(id=str(unit.id), building_id=str(unit.building_id), name=unit.name))

    def list_all(self) -> list[Unit]:
        rows = self._session.scalars(select(UnitRecord).order_by(UnitRecord.name)).all()
        return [Unit(id=UUID(r.id), building_id=UUID(r.building_id), name=r.name) for r in rows]


class SqlAlchemyMeterPointRepository(MeterPointRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, meter_point: MeterPoint) -> None:
        self._session.add(MeterPointRecord(id=str(meter_point.id), unit_id=str(meter_point.unit_id), name=meter_point.name))

    def list_all(self) -> list[MeterPoint]:
        rows = self._session.scalars(select(MeterPointRecord).order_by(MeterPointRecord.name)).all()
        return [MeterPoint(id=UUID(r.id), unit_id=UUID(r.unit_id), name=r.name) for r in rows]


class SqlAlchemyReadingRepository(ReadingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_manual(self, meter_register_id: UUID, measured_at: datetime, value: Decimal) -> Reading:
        return self._add_reading(meter_register_id, measured_at, value, source="manual")

    def add_photo(
        self,
        meter_register_id: UUID,
        measured_at: datetime,
        value: Decimal,
        image_path: str,
        ocr_confidence: float,
        ocr_text: str,
        ocr_candidates: list[OCRCandidateDTO],
        ocr_status: str = "suggested",
    ) -> Reading:
        return self._add_reading(
            meter_register_id,
            measured_at,
            value,
            source="photo",
            image_path=image_path,
            ocr_confidence=ocr_confidence,
            ocr_text=ocr_text,
            ocr_candidates=ocr_candidates,
            ocr_status=ocr_status,
        )

    def update_ocr_status(
        self,
        reading_id: UUID,
        *,
        status: str,
        corrected_value: Decimal | None = None,
    ) -> Reading:
        row = self._session.scalar(select(ReadingRecord).where(ReadingRecord.id == str(reading_id)).limit(1))
        if row is None:
            raise ValueError("Ablesung nicht gefunden.")

        row.ocr_status = status
        if corrected_value is not None:
            row.value = corrected_value

        return Reading(
            id=UUID(row.id),
            meter_register_id=UUID(row.meter_register_id),
            measured_at=row.measured_at,
            value=row.value,
        )

    def get_ocr_metadata(self, reading_id: UUID) -> ReadingOCRMetadataDTO:
        row = self._session.scalar(select(ReadingRecord).where(ReadingRecord.id == str(reading_id)).limit(1))
        if row is None:
            raise ValueError("Ablesung nicht gefunden.")

        parsed_candidates: list[OCRCandidateDTO] = []
        if row.ocr_candidates:
            for item in json.loads(row.ocr_candidates):
                parsed_candidates.append(OCRCandidateDTO(value=Decimal(str(item["value"])), confidence=float(item["confidence"])))

        return ReadingOCRMetadataDTO(
            image_path=row.image_path,
            ocr_confidence=float(row.ocr_confidence) if row.ocr_confidence is not None else None,
            ocr_text=row.ocr_text,
            ocr_candidates=parsed_candidates,
            ocr_status=row.ocr_status,
        )

    def _add_reading(
        self,
        meter_register_id: UUID,
        measured_at: datetime,
        value: Decimal,
        source: str,
        *,
        image_path: str | None = None,
        ocr_confidence: float | None = None,
        ocr_text: str | None = None,
        ocr_candidates: list[OCRCandidateDTO] | None = None,
        ocr_status: str = "manual",
    ) -> Reading:
        register_exists = self._session.scalar(
            select(MeterRegisterRecord.id).where(MeterRegisterRecord.id == str(meter_register_id)).limit(1)
        )
        if register_exists is None:
            raise ValueError("Zählwerk existiert nicht.")

        reading = Reading(id=uuid4(), meter_register_id=meter_register_id, measured_at=measured_at, value=value)
        self._session.add(
            ReadingRecord(
                id=str(reading.id),
                meter_register_id=str(meter_register_id),
                measured_at=reading.measured_at,
                value=reading.value,
                source=source,
                image_path=image_path,
                ocr_confidence=ocr_confidence,
                ocr_text=ocr_text,
                ocr_candidates=(
                    json.dumps([{"value": str(item.value), "confidence": item.confidence} for item in ocr_candidates])
                    if ocr_candidates is not None
                    else None
                ),
                ocr_status=ocr_status,
            )
        )
        return reading

    def list_for_meter_register(self, meter_register_id: UUID) -> list[Reading]:
        rows = self._session.scalars(
            select(ReadingRecord)
            .where(ReadingRecord.meter_register_id == str(meter_register_id))
            .order_by(ReadingRecord.measured_at)
        ).all()
        return [Reading(id=UUID(r.id), meter_register_id=UUID(r.meter_register_id), measured_at=r.measured_at, value=r.value) for r in rows]

    def list_for_meter_point(self, meter_point_id: UUID) -> list[Reading]:
        rows = self._session.scalars(
            select(ReadingRecord)
            .join(MeterRegisterRecord, ReadingRecord.meter_register_id == MeterRegisterRecord.id)
            .join(MeterDeviceRecord, MeterRegisterRecord.meter_device_id == MeterDeviceRecord.id)
            .where(MeterDeviceRecord.meter_point_id == str(meter_point_id))
            .order_by(ReadingRecord.measured_at)
        ).all()
        return [Reading(id=UUID(r.id), meter_register_id=UUID(r.meter_register_id), measured_at=r.measured_at, value=r.value) for r in rows]

    def list_for_building(self, building_id: UUID) -> list[Reading]:
        rows = self._session.scalars(
            select(ReadingRecord)
            .join(MeterRegisterRecord, ReadingRecord.meter_register_id == MeterRegisterRecord.id)
            .join(MeterDeviceRecord, MeterRegisterRecord.meter_device_id == MeterDeviceRecord.id)
            .join(MeterPointRecord, MeterDeviceRecord.meter_point_id == MeterPointRecord.id)
            .join(UnitRecord, MeterPointRecord.unit_id == UnitRecord.id)
            .where(UnitRecord.building_id == str(building_id))
            .order_by(ReadingRecord.measured_at)
        ).all()
        return [Reading(id=UUID(r.id), meter_register_id=UUID(r.meter_register_id), measured_at=r.measured_at, value=r.value) for r in rows]

    def get_current_register_for_meter_point(self, meter_point_id: UUID) -> UUID | None:
        register_id = self._session.scalar(
            select(MeterRegisterRecord.id)
            .join(MeterDeviceRecord, MeterRegisterRecord.meter_device_id == MeterDeviceRecord.id)
            .where(MeterDeviceRecord.meter_point_id == str(meter_point_id), MeterDeviceRecord.removed_at.is_(None))
            .order_by(MeterDeviceRecord.installed_at.desc(), MeterRegisterRecord.code.asc())
            .limit(1)
        )
        return UUID(register_id) if register_id else None


class SqlAlchemyMeterDeviceRepository(MeterDeviceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_default_for_meter_point(self, meter_point_id: UUID) -> UUID:
        device_id = uuid4()
        self._session.add(
            MeterDeviceRecord(
                id=str(device_id),
                meter_point_id=str(meter_point_id),
                serial_number=f"AUTO-{str(meter_point_id)[:8]}",
                installed_at=datetime.now(timezone.utc),
                removed_at=None,
            )
        )
        return device_id


class SqlAlchemyMeterRegisterRepository(MeterRegisterRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_default_for_device(self, meter_device_id: UUID) -> UUID:
        register_id = uuid4()
        self._session.add(
            MeterRegisterRecord(
                id=str(register_id),
                meter_device_id=str(meter_device_id),
                code="MAIN",
                measurement_unit="kWh",
                rollover_limit=None,
            )
        )
        return register_id


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

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self._storage_file.parent, delete=False) as handle:
                handle.write(json.dumps(payload))
                temp_path = Path(handle.name)

            temp_path.replace(self._storage_file)
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise

    def _load(self) -> dict[str, str]:
        if not self._storage_file.exists():
            return {}
        try:
            return json.loads(self._storage_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Could not read weather station overrides from %s", self._storage_file)
            return {}
