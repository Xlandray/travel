from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.booking import BookingStatus
from app.models.payment import PaymentStatus
from app.schemas.base import Schema

if TYPE_CHECKING:
    from app.models.booking import Booking


class BookingBase(Schema):
    """Base schema for shared booking attributes."""

    departure_id: UUID = Field(
        ...,
        description="Secilen tur kalkisinin essiz ID'si",
    )
    boarding_point_id: UUID | None = Field(
        default=None,
        description="Yolcunun binmeyi sectigi noktanin ID'si",
    )
    seat_count: int = Field(
        ...,
        gt=0,
        le=10,
        description="Alinacak koltuk sayisi. Tek seferde en fazla 10 koltuk alinabilir.",
    )


class BookingCreate(BookingBase):
    """Next.js tarafindaki rezervasyon formundan gonderilecek veriler.

    user_id (Token'dan) ve total_price (DB'den) asla buradan alinmaz.
    """

    pass


class BookingResponse(BookingBase):
    """Next.js tarafina donulecek rezervasyon detay ve durum semasi."""

    id: UUID
    user_id: UUID
    total_price: float
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    # Iliskili kayitlardan zenginlestirilen alanlar (admin ve profil gorunumleri icin)
    user_email: EmailStr | None = None
    user_full_name: str | None = None
    tour_id: UUID | None = None
    tour_title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    boarding_point_name: str | None = None

    # En guncel odeme bilgisi (varliginda)
    payment_id: UUID | None = None
    payment_status: PaymentStatus | None = None


# Alias for backwards compatibility with existing route imports
BookingRead = BookingResponse


def booking_to_response(booking: "Booking") -> BookingResponse:
    """Serialize a Booking ORM object into BookingResponse with joined info.

    Relationships (departure -> tour, user, boarding_point, payments) must
    already be eagerly loaded to avoid lazy-loading on an async session.
    """
    response = BookingResponse.model_validate(booking)

    departure = booking.departure
    if departure is not None:
        response.tour_id = departure.tour_id
        response.tour_title = departure.tour.title if departure.tour else None
        response.start_date = departure.start_date
        response.end_date = departure.end_date

    if booking.user is not None:
        response.user_email = booking.user.email
        response.user_full_name = booking.user.full_name

    if booking.boarding_point is not None:
        response.boarding_point_name = booking.boarding_point.name

    if booking.payments:
        latest_payment = booking.payments[-1]
        response.payment_id = latest_payment.id
        response.payment_status = latest_payment.status

    return response
