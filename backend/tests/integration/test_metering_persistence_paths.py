from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from meterweb.infrastructure.sqlalchemy_models import (
    AggregateConsumptionRecord,
    Base,
    MeterDeviceHistoryRecord,
    MeterDeviceRecord,
    MeterPointRecord,
    MeterRegisterRecord,
    RawAbsoluteReadingRecord,
    RawIntervalReadingRecord,
    RawPulseReadingRecord,
    RegisterTariffBindingRecord,
    RolloverEventRecord,
    UnitRecord,
    BuildingRecord,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def test_persists_meter_replacement_and_rollover_history() -> None:
    session = _session()
    building_id = str(uuid4())
    unit_id = str(uuid4())
    meter_point_id = str(uuid4())
    old_device_id = str(uuid4())
    new_device_id = str(uuid4())
    register_id = str(uuid4())

    session.add(BuildingRecord(id=building_id, name="Haus 1"))
    session.add(UnitRecord(id=unit_id, building_id=building_id, name="E1"))
    session.add(MeterPointRecord(id=meter_point_id, unit_id=unit_id, name="Strom"))
    session.add(
        MeterDeviceRecord(
            id=old_device_id,
            meter_point_id=meter_point_id,
            serial_number="OLD-1",
            installed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            removed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
    )
    session.add(
        MeterDeviceRecord(
            id=new_device_id,
            meter_point_id=meter_point_id,
            serial_number="NEW-1",
            installed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            removed_at=None,
        )
    )
    session.add(
        MeterDeviceHistoryRecord(
            id=str(uuid4()),
            meter_point_id=meter_point_id,
            device_id=new_device_id,
            event_type="replaced",
            occurred_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            note="turnus",
        )
    )
    session.add(
        MeterRegisterRecord(
            id=register_id,
            meter_device_id=new_device_id,
            code="MAIN",
            measurement_unit="kWh",
            tariff_code="HT",
            rollover_limit=Decimal("10000"),
        )
    )
    session.add(
        RolloverEventRecord(
            id=str(uuid4()),
            meter_register_id=register_id,
            occurred_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
            previous_value=Decimal("9999"),
            current_value=Decimal("4"),
            rollover_limit=Decimal("10000"),
        )
    )
    session.commit()

    history_count = session.scalar(select(func.count()).select_from(MeterDeviceHistoryRecord))
    rollover_count = session.scalar(select(func.count()).select_from(RolloverEventRecord))
    assert history_count == 1
    assert rollover_count == 1


def test_persists_multi_register_raw_and_aggregate_paths() -> None:
    session = _session()
    building_id = str(uuid4())
    unit_id = str(uuid4())
    meter_point_id = str(uuid4())
    device_id = str(uuid4())
    register_ht = str(uuid4())
    register_nt = str(uuid4())

    session.add(BuildingRecord(id=building_id, name="Haus 2"))
    session.add(UnitRecord(id=unit_id, building_id=building_id, name="E2"))
    session.add(MeterPointRecord(id=meter_point_id, unit_id=unit_id, name="Strom"))
    session.add(
        MeterDeviceRecord(
            id=device_id,
            meter_point_id=meter_point_id,
            serial_number="M-1",
            installed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            removed_at=None,
        )
    )
    session.add_all(
        [
            MeterRegisterRecord(
                id=register_ht,
                meter_device_id=device_id,
                code="HT",
                measurement_unit="kWh",
                tariff_code="HT",
                rollover_limit=None,
            ),
            MeterRegisterRecord(
                id=register_nt,
                meter_device_id=device_id,
                code="NT",
                measurement_unit="kWh",
                tariff_code="NT",
                rollover_limit=None,
            ),
        ]
    )
    session.add_all(
        [
            RegisterTariffBindingRecord(
                id=str(uuid4()),
                meter_register_id=register_ht,
                tariff_code="HT",
                valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
                valid_to=None,
            ),
            RegisterTariffBindingRecord(
                id=str(uuid4()),
                meter_register_id=register_nt,
                tariff_code="NT",
                valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
                valid_to=None,
            ),
        ]
    )
    session.add(RawAbsoluteReadingRecord(id=str(uuid4()), meter_register_id=register_ht, measured_at=datetime(2025, 2, 1, tzinfo=timezone.utc), value=Decimal("123"), source="manual"))
    session.add(RawPulseReadingRecord(id=str(uuid4()), meter_register_id=register_nt, measured_at=datetime(2025, 2, 1, tzinfo=timezone.utc), pulse_count=300, pulse_factor=Decimal("0.01"), source="gateway"))
    session.add(RawIntervalReadingRecord(id=str(uuid4()), meter_register_id=register_ht, start_at=datetime(2025, 2, 1, 0, tzinfo=timezone.utc), end_at=datetime(2025, 2, 1, 1, tzinfo=timezone.utc), value=Decimal("1.5"), source="smart_meter"))
    session.add(AggregateConsumptionRecord(id=str(uuid4()), meter_point_id=meter_point_id, meter_register_id=register_ht, period_start=datetime(2025, 2, 1, tzinfo=timezone.utc), period_end=datetime(2025, 3, 1, tzinfo=timezone.utc), consumption=Decimal("33.1"), computed_at=datetime.now(timezone.utc)))
    session.commit()

    raw_abs = session.scalar(select(func.count()).select_from(RawAbsoluteReadingRecord))
    raw_pulse = session.scalar(select(func.count()).select_from(RawPulseReadingRecord))
    raw_interval = session.scalar(select(func.count()).select_from(RawIntervalReadingRecord))
    aggregates = session.scalar(select(func.count()).select_from(AggregateConsumptionRecord))

    assert raw_abs == 1
    assert raw_pulse == 1
    assert raw_interval == 1
    assert aggregates == 1
