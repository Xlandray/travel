import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tour import BoardingPoint, Tour

# Rota duragi ve binis duragi arasindaki coktan-coga iliski tablosu
route_stop_boarding_points = Table(
    "route_stop_boarding_points",
    Base.metadata,
    Column(
        "route_stop_id",
        UUID(as_uuid=True),
        ForeignKey("route_stops.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "boarding_point_id",
        UUID(as_uuid=True),
        ForeignKey("boarding_points.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class RouteStop(Base, TimestampMixin):
    """A single day/stop within a tour's itinerary (rota)."""

    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"), index=True
    )
    day_number: Mapped[int] = mapped_column(Integer, default=1)  # 1 = 1. gun
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tour: Mapped["Tour"] = relationship(back_populates="route_stops")
    boarding_points: Mapped[list["BoardingPoint"]] = relationship(
        secondary=route_stop_boarding_points
    )
