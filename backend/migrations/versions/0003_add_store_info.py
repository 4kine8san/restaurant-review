"""add address, phone, business_hours, regular_holiday to restaurants

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("restaurants", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("restaurants", sa.Column("phone", sa.String(30), nullable=True))
    op.add_column("restaurants", sa.Column("business_hours", sa.Text, nullable=True))
    op.add_column("restaurants", sa.Column("regular_holiday", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("restaurants", "regular_holiday")
    op.drop_column("restaurants", "business_hours")
    op.drop_column("restaurants", "phone")
    op.drop_column("restaurants", "address")
