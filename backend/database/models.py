from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, LargeBinary, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from .connection import Base


class Master(Base):
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    value = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_masters_category", "category"),
    )


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    nearest_station = Column(String(100), nullable=True)
    genre_id = Column(Integer, ForeignKey("masters.id"), nullable=True)
    scene = Column(String(50), nullable=True)
    stars = Column(Integer, nullable=True)
    rating_overall = Column(Numeric(2, 1), nullable=True)
    rating_food = Column(Numeric(2, 1), nullable=True)
    rating_service = Column(Numeric(2, 1), nullable=True)
    rating_atmosphere = Column(Numeric(2, 1), nullable=True)
    rating_cost_performance = Column(Numeric(2, 1), nullable=True)
    rating_drinks = Column(Numeric(2, 1), nullable=True)
    visit_date = Column(String(20), nullable=True)
    review_comment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    genre = relationship("Master", foreign_keys=[genre_id])
    photos = relationship("Photo", back_populates="restaurant", order_by="Photo.sort_order")

    __table_args__ = (
        Index("ix_restaurants_nearest_station", "nearest_station"),
        Index("ix_restaurants_genre_id", "genre_id"),
        Index("ix_restaurants_visit_date", "visit_date"),
        Index("ix_restaurants_deleted_at", "deleted_at"),
    )


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    thumbnail_data = Column(LargeBinary, nullable=False)
    sort_order = Column(Integer, default=0)
    rotation = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    restaurant = relationship("Restaurant", back_populates="photos")

    __table_args__ = (
        Index("ix_photos_restaurant_id", "restaurant_id"),
    )
