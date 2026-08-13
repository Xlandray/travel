import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus
from app.models.tour import TourDeparture

logger = logging.getLogger(__name__)


async def create_booking(
    db: AsyncSession,
    user_id: uuid.UUID | str,
    departure_id: uuid.UUID | str,
    seat_count: int,
    boarding_point_id: uuid.UUID | str | None = None,
) -> Booking:
    """Create a tour booking with row-level locking (with_for_update) to prevent race conditions."""
    user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    departure_id_uuid = uuid.UUID(departure_id) if isinstance(departure_id, str) else departure_id
    boarding_point_uuid = (
        uuid.UUID(boarding_point_id)
        if boarding_point_id and isinstance(boarding_point_id, str)
        else boarding_point_id
    )

    # 1. Row-Level Lock: Satiri okurken KILITLE (with_for_update)
    stmt = select(TourDeparture).where(TourDeparture.id == departure_id_uuid).with_for_update()
    result = await db.execute(stmt)
    departure = result.scalar_one_or_none()

    if not departure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kalkis bulunamadi.",
        )

    # 2. Stok Kontrolu
    if departure.available_seats < seat_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Yetersiz kontenjan. Kalan koltuk: {departure.available_seats}",
        )

    # 3. Rezervasyonu Olustur ve Fiyati Sabitle
    total_price = departure.price * seat_count

    new_booking = Booking(
        user_id=user_id_uuid,
        departure_id=departure_id_uuid,
        boarding_point_id=boarding_point_uuid,
        seat_count=seat_count,
        total_price=total_price,
        status=BookingStatus.PENDING,  # Henuz odeme yapilmadi
    )

    # 4. Stogu Dus
    departure.available_seats -= seat_count

    db.add(new_booking)

    # Islemi Veritabanina Yansit ve Kilidi Serbest Birak
    await db.commit()
    await db.refresh(new_booking)

    return new_booking


async def cancel_expired_booking(
    booking_id: uuid.UUID | str,
    db: AsyncSession | None = None,
) -> bool:
    """Cancels a booking if it is still PENDING and releases reserved seats back to departure."""
    booking_uuid = uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id

    async def _process(session: AsyncSession) -> bool:
        stmt = select(Booking).where(Booking.id == booking_uuid).with_for_update()
        res = await session.execute(stmt)
        booking = res.scalar_one_or_none()

        if not booking or booking.status != BookingStatus.PENDING:
            return False

        dep_stmt = (
            select(TourDeparture).where(TourDeparture.id == booking.departure_id).with_for_update()
        )
        dep_res = await session.execute(dep_stmt)
        departure = dep_res.scalar_one_or_none()

        if departure:
            departure.available_seats += booking.seat_count

        booking.status = BookingStatus.CANCELLED
        await session.commit()
        logger.info(
            f"Booking {booking_uuid} expired and cancelled. Released {booking.seat_count} seats."
        )
        return True

    if db is not None:
        return await _process(db)
    else:
        async with AsyncSessionLocal() as session:
            return await _process(session)


async def cancel_booking(
    booking_id: uuid.UUID | str,
    db: AsyncSession,
) -> Booking:
    """Admin-level cancel: releases reserved seats back for any non-cancelled booking.

    Unlike ``cancel_expired_booking`` (PENDING-only), this also cancels CONFIRMED
    bookings and always returns the booking.
    """
    booking_uuid = uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id

    stmt = select(Booking).where(Booking.id == booking_uuid).with_for_update()
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı.",
        )

    if booking.status != BookingStatus.CANCELLED:
        dep_stmt = (
            select(TourDeparture).where(TourDeparture.id == booking.departure_id).with_for_update()
        )
        dep_res = await db.execute(dep_stmt)
        departure = dep_res.scalar_one_or_none()
        if departure:
            departure.available_seats += booking.seat_count
        booking.status = BookingStatus.CANCELLED
        await db.commit()
        await db.refresh(booking)
        logger.info(
            f"Booking {booking_uuid} cancelled by admin. Released {booking.seat_count} seats."
        )

    return booking


# Kaldirildi: `schedule_booking_timeout_release` ve
# `release_all_expired_pending_bookings`. Ikisi de suresi dolmus rezervasyonlari
# toplama isini ucuncu kez uyguluyordu; tek gecerli uygulama lifespan'daki
# supurucu (`core/tasks.start_booking_sweeper` -> `cleanup_service`), cunku
# yeniden baslatmayi atlatir ve `skip_locked` ile kilitlenmeden calisir.
