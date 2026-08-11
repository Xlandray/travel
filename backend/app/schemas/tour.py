import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.hotel import TourHotelIn, TourHotelRead
from app.schemas.route import RouteStopIn, RouteStopRead


class BoardingPointResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TourImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    sort_order: int = 0
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class TourImageIn(BaseModel):
    url: str
    sort_order: int = 0


class TourCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class TourCategoryCreate(BaseModel):
    name: str
    slug: str | None = None
    is_active: bool = True


class TourCategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None


class TourDepartureResponse(BaseModel):
    id: uuid.UUID
    tour_id: uuid.UUID
    start_date: date
    end_date: date
    price: float
    available_seats: int
    total_quota: int
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class TourCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = ""
    days: int = Field(default=1, ge=1)
    nights: int = Field(default=0, ge=0)
    price: float = Field(default=0.0, ge=0)
    image_url: str | None = None
    is_active: bool = True
    category_id: uuid.UUID | None = None
    images: list[TourImageIn] = []
    hotels: list[TourHotelIn] = []
    route_stops: list[RouteStopIn] = []


class TourUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    days: int | None = Field(default=None, ge=1)
    nights: int | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, ge=0)
    image_url: str | None = None
    is_active: bool | None = None
    category_id: uuid.UUID | None = None
    images: list[TourImageIn] | None = None
    hotels: list[TourHotelIn] | None = None
    route_stops: list[RouteStopIn] | None = None


class TourDepartureUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    price: float | None = Field(default=None, ge=0)
    total_quota: int | None = Field(default=None, ge=1)
    available_seats: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class TourResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    description: str
    days: int
    nights: int
    is_active: bool
    price: float = Field(default=0.0)
    image_url: str | None = None
    category_id: uuid.UUID | None = None
    category: TourCategoryResponse | None = None
    images: list[TourImageResponse] = []
    hotels: list[TourHotelRead] = []
    route_stops: list[RouteStopRead] = []
    departures: list[TourDepartureResponse] = []
    boarding_points: list[BoardingPointResponse] = []

    model_config = ConfigDict(from_attributes=True)
