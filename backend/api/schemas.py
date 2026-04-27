from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

_VALID_SCENES = {"", "朝", "昼", "夜", "持ち帰り", "その他"}


class RestaurantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    nearest_station: Optional[str] = Field(None, max_length=100)
    genre_id: Optional[int] = Field(None, ge=1)
    scene: Optional[str] = Field(None, max_length=50)
    stars: Optional[int] = Field(None, ge=1, le=5)
    rating_overall: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_food: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_service: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_atmosphere: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_cost_performance: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    rating_drinks: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("5.0"))
    visit_date: Optional[str] = Field(None, max_length=20)
    review_comment: Optional[str] = Field(None, max_length=5000)
    notes: Optional[str] = Field(None, max_length=2000)
    tabelog_id: Optional[str] = Field(None, max_length=20)
    prefecture: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=300)
    phone: Optional[str] = Field(None, max_length=30)
    business_hours: Optional[str] = Field(None, max_length=500)
    regular_holiday: Optional[str] = Field(None, max_length=100)

    @field_validator("scene")
    @classmethod
    def scene_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_SCENES:
            raise ValueError(f"scene は {sorted(_VALID_SCENES)} のいずれかである必要があります")
        return v


class RestaurantUpdate(RestaurantCreate):
    name: Optional[str] = Field(None, min_length=1, max_length=200)


class MasterCreate(BaseModel):
    category: str = Field(..., max_length=50)
    value: str = Field(..., max_length=100)
    sort_order: int = Field(0, ge=0)


class AdminVerify(BaseModel):
    password: str = Field(..., max_length=200)


class PhotoReorder(BaseModel):
    photo_ids: list[int] = Field(..., min_length=1)
