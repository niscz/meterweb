"""initial metering schema

Revision ID: 0001_initial_metering_schema
Revises:
Create Date: 2026-03-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_metering_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("building_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "meter_points",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("unit_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "meter_devices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("meter_point_id", sa.String(length=36), nullable=False),
        sa.Column("serial_number", sa.String(length=128), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["meter_point_id"], ["meter_points.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "meter_registers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("meter_device_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("measurement_unit", sa.String(length=32), nullable=False),
        sa.Column("rollover_limit", sa.Numeric(20, 6), nullable=True),
        sa.ForeignKeyConstraint(["meter_device_id"], ["meter_devices.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "readings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("meter_register_id", sa.String(length=36), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["meter_register_id"], ["meter_registers.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_units_building_id", "units", ["building_id"])
    op.create_index("ix_meter_points_unit_id", "meter_points", ["unit_id"])
    op.create_index("ix_meter_devices_meter_point_id", "meter_devices", ["meter_point_id"])
    op.create_index("ix_meter_registers_meter_device_id", "meter_registers", ["meter_device_id"])
    op.create_index("ix_readings_meter_register_id", "readings", ["meter_register_id"])


def downgrade() -> None:
    op.drop_index("ix_readings_meter_register_id", table_name="readings")
    op.drop_index("ix_meter_registers_meter_device_id", table_name="meter_registers")
    op.drop_index("ix_meter_devices_meter_point_id", table_name="meter_devices")
    op.drop_index("ix_meter_points_unit_id", table_name="meter_points")
    op.drop_index("ix_units_building_id", table_name="units")

    op.drop_table("readings")
    op.drop_table("meter_registers")
    op.drop_table("meter_devices")
    op.drop_table("meter_points")
    op.drop_table("units")
    op.drop_table("buildings")
