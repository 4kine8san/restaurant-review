"""add tabelog_id to restaurants

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("restaurants", sa.Column("tabelog_id", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("restaurants", "tabelog_id")
