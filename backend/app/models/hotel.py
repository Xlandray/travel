import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tour import Tour


class Hotel(Base, TimestampMixin):
    """Accommodation used by tours, reusable across multiple tours."""

    __tablename__ = "hotels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    star_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 yildiz
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tour_links: Mapped[list["TourHotel"]] = relationship(
        back_populates="hotel", cascade="all, delete-orphan"
    )


class TourHotel(Base, TimestampMixin):
    """Hotel assignment to a tour, ordered by night (gece sirasi)."""

    __tablename__ = "tour_hotels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"), index=True
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hotels.id", ondelete="CASCADE"), index=True
    )
    night_order: Mapped[int] = mapped_column(Integer, default=1)  # 1 = ilk gece
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tour: Mapped["Tour"] = relationship(back_populates="hotels")
    hotel: Mapped["Hotel"] = relationship(back_populates="tour_links")
