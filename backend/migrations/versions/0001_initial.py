"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "masters",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_masters_category", "masters", ["category"])

    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("nearest_station", sa.String(100), nullable=True),
        sa.Column("genre_id", sa.Integer, sa.ForeignKey("masters.id"), nullable=True),
        sa.Column("scene", sa.String(50), nullable=True),
        sa.Column("stars", sa.Integer, nullable=True),
        sa.Column("rating_overall", sa.Numeric(2, 1), nullable=True),
        sa.Column("rating_food", sa.Numeric(2, 1), nullable=True),
        sa.Column("rating_service", sa.Numeric(2, 1), nullable=True),
        sa.Column("rating_atmosphere", sa.Numeric(2, 1), nullable=True),
        sa.Column("rating_cost_performance", sa.Numeric(2, 1), nullable=True),
        sa.Column("rating_drinks", sa.Numeric(2, 1), nullable=True),
        sa.Column("visit_date", sa.String(20), nullable=True),
        sa.Column("review_comment", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_restaurants_nearest_station", "restaurants", ["nearest_station"])
    op.create_index("ix_restaurants_genre_id", "restaurants", ["genre_id"])
    op.create_index("ix_restaurants_visit_date", "restaurants", ["visit_date"])
    op.create_index("ix_restaurants_deleted_at", "restaurants", ["deleted_at"])

    op.create_table(
        "photos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("restaurant_id", sa.Integer, sa.ForeignKey("restaurants.id"), nullable=False),
        sa.Column("image_data", sa.LargeBinary, nullable=False),
        sa.Column("thumbnail_data", sa.LargeBinary, nullable=False),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("rotation", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_photos_restaurant_id", "photos", ["restaurant_id"])

    op.execute("""
        INSERT INTO masters (category, value, sort_order) VALUES
        ('genre', '和食', 1), ('genre', '洋食', 2), ('genre', '中華', 3),
        ('genre', 'イタリアン', 4), ('genre', 'フレンチ', 5), ('genre', '焼肉', 6),
        ('genre', '寿司', 7), ('genre', 'ラーメン', 8), ('genre', '居酒屋', 9),
        ('genre', 'カフェ', 10), ('genre', 'その他', 99)
    """)


def downgrade() -> None:
    op.drop_table("photos")
    op.drop_table("restaurants")
    op.drop_table("masters")
