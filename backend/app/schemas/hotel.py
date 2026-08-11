import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import Schema


class HotelCreate(Schema):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class HotelUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class HotelRead(Schema):
    id: uuid.UUID
    name: str
    city: str
    address: str | None
    phone: str | None
    star_rating: int | None
    description: str | None
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TourHotelIn(Schema):
    hotel_id: uuid.UUID
    night_order: int = Field(default=1, ge=1)


class TourHotelRead(Schema):
    id: uuid.UUID
    tour_id: uuid.UUID
    night_order: int
    is_active: bool
    hotel: HotelRead
