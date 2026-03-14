"""add ocr fields to readings

Revision ID: 0002_add_ocr_fields_to_readings
Revises: 0001_initial_metering_schema
Create Date: 2026-03-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_ocr_fields_to_readings"
down_revision = "0001_initial_metering_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("readings", sa.Column("image_path", sa.String(length=1024), nullable=True))
    op.add_column("readings", sa.Column("ocr_confidence", sa.Numeric(5, 4), nullable=True))
    op.add_column("readings", sa.Column("ocr_text", sa.Text(), nullable=True))
    op.add_column("readings", sa.Column("ocr_candidates", sa.Text(), nullable=True))
    op.add_column("readings", sa.Column("ocr_status", sa.String(length=32), nullable=False, server_default="manual"))
    op.alter_column("readings", "ocr_status", server_default=None)


def downgrade() -> None:
    op.drop_column("readings", "ocr_status")
    op.drop_column("readings", "ocr_candidates")
    op.drop_column("readings", "ocr_text")
    op.drop_column("readings", "ocr_confidence")
    op.drop_column("readings", "image_path")
