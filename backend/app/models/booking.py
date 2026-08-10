import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.tour import BoardingPoint, TourDeparture
    from app.models.user import User


class BookingStatus(enum.StrEnum):
    """Booking lifecycle states."""


    PENDING = "pending"  # Sepette/Odeme bekliyor
    CONFIRMED = "confirmed"  # Odendi ve Onaylandi
    CANCELLED = "cancelled"  # Iptal edildi


class Booking(Base, TimestampMixin):
    """Tour booking entity with stock reservation tracking."""

    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Iliskiler
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    departure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tour_departures.id", ondelete="RESTRICT"), index=True
    )
    boarding_point_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("boarding_points.id", ondelete="SET NULL"), nullable=True
    )

    # Satis Detaylari
    seat_count: Mapped[int] = mapped_column(Integer)  # Kac koltuk alindi?
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))  # Satis anindaki toplam fiyat

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="bookingstatus"),
        default=BookingStatus.PENDING,
        index=True,
    )

    # Referans baglantilari
    user: Mapped["User"] = relationship()
    departure: Mapped["TourDeparture"] = relationship()
    boarding_point: Mapped["BoardingPoint | None"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")
