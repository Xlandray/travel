import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.tour import TourDeparture

logger = logging.getLogger(__name__)


async def release_expired_bookings(db: AsyncSession) -> int:
    """Find and cancel PENDING bookings older than 15 minutes, returning reserved seats.

    Uses with_for_update(skip_locked=True) to avoid deadlocks with concurrent checkout operations.
    """
    # Su anki zamandan 15 dakika oncesini hesapla (UTC)
    expire_threshold = datetime.now(UTC) - timedelta(minutes=15)

    # 15 dakikayi gecmis, PENDING statusundeki rezervasyonlari bul ve KILITLE (skip_locked=True)
    stmt = (
        select(Booking)
        .where(
            Booking.status == BookingStatus.PENDING,
            Booking.created_at <= expire_threshold,
        )
        .with_for_update(skip_locked=True)
    )

    result = await db.execute(stmt)
    expired_bookings = result.scalars().all()

    if not expired_bookings:
        return 0

    released_count = 0
    for booking in expired_bookings:
        # Kalkis (TourDeparture) kaydini bul ve stogu geri ver
        dep_stmt = (
            select(TourDeparture)
            .where(TourDeparture.id == booking.departure_id)
            .with_for_update()
        )
        dep_result = await db.execute(dep_stmt)
        departure = dep_result.scalar_one_or_none()

        if departure:
            # 1. Stogu Geri Yukle
            departure.available_seats += booking.seat_count

        # 2. Rezervasyonu Iptal Et
        booking.status = BookingStatus.CANCELLED
        released_count += 1

        logger.info(
            f"Zaman asimi: {booking.id} nolu rezervasyon iptal edildi. {booking.seat_count} koltuk iade edildi."
        )

    await db.commit()
    return released_count
