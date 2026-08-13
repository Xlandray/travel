import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.audit_log import AuditAction
from app.models.booking import Booking, BookingStatus
from app.models.tour import TourDeparture
from app.services import audit_service

logger = logging.getLogger(__name__)


def lock_booking(booking_id: uuid.UUID) -> Select[tuple[Booking]]:
    """Row lock that also refreshes the session's copy of the row.

    `with_for_update()` on its own is not enough. If the row is already in the
    session's identity map — and it is, because the route loaded it to check
    ownership — SQLAlchemy hands back the cached object and throws away the
    values the locking SELECT just read. The lock is genuinely held, but the
    status check that follows runs against stale data, so every waiter still
    sees the booking as it was before the winner committed.

    That is how four concurrent cancels of one three-seat booking returned the
    same three seats four times, taking a five-seat departure to fourteen.
    `populate_existing` makes the locked re-read overwrite the cached values.
    """
    return (
        select(Booking)
        .where(Booking.id == booking_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def lock_departure(departure_id: uuid.UUID) -> Select[tuple[TourDeparture]]:
    """See `lock_booking`: lock the row and take its committed values."""
    return (
        select(TourDeparture)
        .where(TourDeparture.id == departure_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def create_booking(
    db: AsyncSession,
    actor: User,
    departure_id: uuid.UUID | str,
    seat_count: int,
    boarding_point_id: uuid.UUID | str | None = None,
) -> Booking:
    """Create a tour booking with row-level locking (with_for_update) to prevent race conditions."""
    user_id_uuid = actor.id
    departure_id_uuid = uuid.UUID(departure_id) if isinstance(departure_id, str) else departure_id
    boarding_point_uuid = (
        uuid.UUID(boarding_point_id)
        if boarding_point_id and isinstance(boarding_point_id, str)
        else boarding_point_id
    )

    # 1. Row-Level Lock: Satiri okurken KILITLE (bkz. lock_departure)
    result = await db.execute(lock_departure(departure_id_uuid))
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
    # Flush, not commit: the booking needs an id before the audit entry can
    # point at it, but both still have to land in one transaction.
    await db.flush()

    audit_service.record(
        db,
        AuditAction.BOOKING_CREATED,
        actor=actor,
        booking_id=new_booking.id,
        amount=total_price,
        detail={
            "departure_id": str(departure_id_uuid),
            "seat_count": seat_count,
            "seats_left": departure.available_seats,
        },
    )

    # Islemi Veritabanina Yansit ve Kilidi Serbest Birak
    await db.commit()
    await db.refresh(new_booking)

    return new_booking


async def cancel_pending_booking(
    db: AsyncSession,
    booking_id: uuid.UUID | str,
    actor: User,
) -> Booking:
    """Self-service cancel: drop a PENDING booking and release its seats once.

    Every state check happens *after* the row lock is taken, so concurrent calls
    serialise: the first one cancels, the rest see CANCELLED and return without
    touching the departure. A CONFIRMED booking has money against it and cannot
    be dropped here; the refund route is its only exit.
    """
    booking_uuid = uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id

    booking = (await db.execute(lock_booking(booking_uuid))).scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadi.",
        )

    if booking.status == BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Onaylanmış rezervasyon buradan iptal edilemez; iade talebi oluşturun.",
        )

    if booking.status == BookingStatus.CANCELLED:
        return booking

    departure = (await db.execute(lock_departure(booking.departure_id))).scalar_one_or_none()
    if departure:
        departure.available_seats += booking.seat_count

    booking.status = BookingStatus.CANCELLED

    audit_service.record(
        db,
        AuditAction.BOOKING_CANCELLED,
        actor=actor,
        booking_id=booking.id,
        amount=booking.total_price,
        detail={"seat_count": booking.seat_count, "by": "customer"},
    )

    await db.commit()
    # `updated_at` is server-managed (FetchedValue), so it is expired by the
    # UPDATE and has to be re-read before anything serialises the booking.
    await db.refresh(booking)
    logger.info(f"Booking {booking_uuid} cancelled. Released {booking.seat_count} seats.")
    return booking


async def cancel_booking(
    booking_id: uuid.UUID | str,
    db: AsyncSession,
    actor: User | None,
) -> Booking:
    """Admin-level cancel: releases reserved seats back for any non-cancelled booking.

    Unlike ``cancel_pending_booking`` this also cancels CONFIRMED bookings and
    always returns the booking. Same locking rule: the status is read under the
    lock, so repeated or concurrent calls release the seats exactly once.
    """
    booking_uuid = uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id

    booking = (await db.execute(lock_booking(booking_uuid))).scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı.",
        )

    if booking.status != BookingStatus.CANCELLED:
        departure = (await db.execute(lock_departure(booking.departure_id))).scalar_one_or_none()
        if departure:
            departure.available_seats += booking.seat_count
        booking.status = BookingStatus.CANCELLED

        audit_service.record(
            db,
            AuditAction.BOOKING_CANCELLED,
            actor=actor,
            booking_id=booking.id,
            amount=booking.total_price,
            detail={"seat_count": booking.seat_count, "by": "admin"},
        )

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
