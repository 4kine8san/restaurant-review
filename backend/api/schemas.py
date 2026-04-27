from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class RestaurantCreate(BaseModel):
    name: str = Field(..., max_length=200)
    nearest_station: Optional[str] = Field(None, max_length=100)
    genre_id: Optional[int] = None
    scene: Optional[str] = Field(None, max_length=50)
    stars: Optional[int] = Field(None, ge=1, le=5)
    rating_overall: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_food: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_service: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_atmosphere: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_cost_performance: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_drinks: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    visit_date: Optional[str] = Field(None, max_length=20)
    review_comment: Optional[str] = None
    notes: Optional[str] = None
    tabelog_id: Optional[str] = Field(None, max_length=20)
    prefecture: Optional[str] = Field(None, max_length=50)


class RestaurantUpdate(RestaurantCreate):
    name: Optional[str] = Field(None, max_length=200)


class MasterCreate(BaseModel):
    category: str = Field(..., max_length=50)
    value: str = Field(..., max_length=100)
    sort_order: int = Field(0, ge=0)


class AdminVerify(BaseModel):
    password: str = Field(..., max_length=200)


class PhotoReorder(BaseModel):
    photo_ids: list[int]
