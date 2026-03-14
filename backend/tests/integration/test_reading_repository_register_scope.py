from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from meterweb.infrastructure.repositories import SqlAlchemyReadingRepository
from meterweb.infrastructure.sqlalchemy_models import Base, BuildingRecord, MeterDeviceRecord, MeterPointRecord, MeterRegisterRecord, ReadingRecord, UnitRecord


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def _seed_meter_with_two_registers(session: Session) -> tuple[UUID, UUID, UUID, UUID]:
    building_id, unit_id, meter_point_id = str(uuid4()), str(uuid4()), str(uuid4())
    device_id = str(uuid4())
    register_ht, register_nt = str(uuid4()), str(uuid4())
    session.add_all([
        BuildingRecord(id=building_id, name="Haus"),
        UnitRecord(id=unit_id, building_id=building_id, name="U1"),
        MeterPointRecord(id=meter_point_id, unit_id=unit_id, name="Strom"),
        MeterDeviceRecord(id=device_id, meter_point_id=meter_point_id, serial_number="S1", installed_at=datetime(2025, 1, 1, tzinfo=timezone.utc), removed_at=None),
        MeterRegisterRecord(id=register_ht, meter_device_id=device_id, code="HT", measurement_unit="kWh", rollover_limit=None),
        MeterRegisterRecord(id=register_nt, meter_device_id=device_id, code="NT", measurement_unit="kWh", rollover_limit=None),
    ])
    session.commit()
    return UUID(meter_point_id), UUID(register_ht), UUID(register_nt), UUID(building_id)


def test_multi_register_reads_are_explicitly_scoped() -> None:
    session = _session()
    meter_point_id, register_ht, register_nt, _building_id = _seed_meter_with_two_registers(session)
    repo = SqlAlchemyReadingRepository(session)

    repo.add_manual(register_ht, datetime(2025, 1, 1, tzinfo=timezone.utc), Decimal("100"))
    repo.add_manual(register_nt, datetime(2025, 1, 1, tzinfo=timezone.utc), Decimal("40"))
    session.commit()

    ht_readings = repo.list_for_meter_register(register_ht)
    nt_readings = repo.list_for_meter_register(register_nt)
    point_readings = repo.list_for_meter_point(meter_point_id)

    assert len(ht_readings) == 1
    assert len(nt_readings) == 1
    assert len(point_readings) == 2


def test_meter_replacement_changes_current_register_lookup() -> None:
    session = _session()
    meter_point_id, old_register, _nt, _building_id = _seed_meter_with_two_registers(session)

    old_device = session.query(MeterDeviceRecord).filter(MeterDeviceRecord.meter_point_id == str(meter_point_id)).one()
    old_device.removed_at = datetime(2025, 2, 1, tzinfo=timezone.utc)
    new_device_id = str(uuid4())
    new_register = str(uuid4())
    session.add(MeterDeviceRecord(id=new_device_id, meter_point_id=str(meter_point_id), serial_number="S2", installed_at=datetime(2025, 2, 1, tzinfo=timezone.utc), removed_at=None))
    session.add(MeterRegisterRecord(id=new_register, meter_device_id=new_device_id, code="MAIN", measurement_unit="kWh", rollover_limit=None))
    session.commit()

    repo = SqlAlchemyReadingRepository(session)
    assert repo.get_current_register_for_meter_point(meter_point_id) == UUID(new_register)
    assert repo.get_current_register_for_meter_point(uuid4()) is None

    with pytest.raises(ValueError):
        repo.add_manual(uuid4(), datetime(2025, 3, 1, tzinfo=timezone.utc), Decimal("1"))

    repo.add_manual(UUID(new_register), datetime(2025, 3, 1, tzinfo=timezone.utc), Decimal("1"))
    session.commit()
    assert all(reading.meter_register_id == UUID(new_register) for reading in repo.list_for_meter_register(UUID(new_register)))


def test_get_ocr_metadata_returns_empty_candidates_for_invalid_payload(caplog) -> None:
    session = _session()
    _meter_point_id, register_ht, _register_nt, _building_id = _seed_meter_with_two_registers(session)
    reading_id = str(uuid4())
    session.add(
        ReadingRecord(
            id=reading_id,
            meter_register_id=str(register_ht),
            measured_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
            value=Decimal("123"),
            source="photo",
            image_path="/uploads/meter.jpg",
            ocr_confidence=Decimal("0.8700"),
            ocr_text="123",
            ocr_candidates='{"broken": ',
            ocr_status="suggested",
        )
    )
    session.commit()

    repo = SqlAlchemyReadingRepository(session)

    with caplog.at_level("WARNING"):
        metadata = repo.get_ocr_metadata(UUID(reading_id))

    assert metadata.ocr_candidates == []
    assert metadata.ocr_status == "suggested"
    assert any(
        record.message == "invalid_ocr_candidates_payload" and getattr(record, "reading_id", None) == reading_id
        for record in caplog.records
    )
