from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
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


class MeterRegisterRecord(Base):
    __tablename__ = "meter_registers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_devices.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    measurement_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    rollover_limit: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)


class ReadingRecord(Base):
    __tablename__ = "readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meter_register_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meter_registers.id", ondelete="CASCADE"), nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
