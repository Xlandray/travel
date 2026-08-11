import uuid

from pydantic import Field

from app.schemas.base import Schema


class BoardingPointRead(Schema):
    id: uuid.UUID
    name: str
    description: str | None = None


class RouteStopIn(Schema):
    day_number: int = Field(default=1, ge=1)
    sort_order: int = 0
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    boarding_point_ids: list[uuid.UUID] = Field(default_factory=list)


class RouteStopUpdate(Schema):
    day_number: int | None = Field(default=None, ge=1)
    sort_order: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    boarding_point_ids: list[uuid.UUID] | None = None


class RouteStopRead(Schema):
    id: uuid.UUID
    tour_id: uuid.UUID
    day_number: int
    sort_order: int
    title: str
    description: str | None
    is_active: bool
    boarding_points: list[BoardingPointRead] = Field(default_factory=list)
