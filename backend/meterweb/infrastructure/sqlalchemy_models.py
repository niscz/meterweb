from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BuildingRecord(Base):
    __tablename__ = "buildings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class UnitRecord(Base):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    building_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class MeterPointRecord(Base):
    __tablename__ = "meter_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    unit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class MeterDeviceRecord(Base):
    __tablename__ = "meter_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_point_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_points.id", ondelete="CASCADE"), nullable=False
    )
    serial_number: Mapped[str] = mapped_column(String(128), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MeterDeviceHistoryRecord(Base):
    __tablename__ = "meter_device_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_point_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_points.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_devices.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class MeterRegisterRecord(Base):
    __tablename__ = "meter_registers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_devices.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    measurement_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    tariff_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rollover_limit: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)


class RegisterTariffBindingRecord(Base):
    __tablename__ = "register_tariff_bindings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    tariff_code: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadingRecord(Base):
    __tablename__ = "readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    ocr_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_candidates: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_status: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")


class RolloverEventRecord(Base):
    __tablename__ = "rollover_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    rollover_limit: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)


class RawAbsoluteReadingRecord(Base):
    __tablename__ = "raw_absolute_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)


class RawPulseReadingRecord(Base):
    __tablename__ = "raw_pulse_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pulse_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse_factor: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)


class RawIntervalReadingRecord(Base):
    __tablename__ = "raw_interval_readings"
    __table_args__ = (
        UniqueConstraint("meter_register_id", "start_at", "end_at", name="uq_interval_window"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)


class AggregateConsumptionRecord(Base):
    __tablename__ = "aggregate_consumption"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_point_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_points.id", ondelete="CASCADE"), nullable=False
    )
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumption: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
