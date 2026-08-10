import logging
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.services import booking_service

logger = logging.getLogger(__name__)


def _new_transaction_id(length: int = 16) -> str:
    """Short pseudo-random mock transaction reference (e.g. \"TXN-7f3a...\")."""
    return "TXN-" + secrets.token_hex(length // 2).upper()


async def create_payment(
    db: AsyncSession,
    user_id: uuid.UUID | str,
    booking_id: uuid.UUID | str,
    method: PaymentMethod,
) -> Payment:
    """Open a payment attempt for a user-owned booking.

    The amount is always snapshotted from the booking's ``total_price``;
    a booking must be PENDING (not yet paid nor cancelled) and must not
    already have a PAID payment.
    """
    booking_uuid = uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id

    stmt = select(Booking).where(Booking.id == booking_uuid)
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadi.",
        )

    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    if booking.user_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rezervasyona odeme acma yetkiniz yok.",
        )

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sadece bekleyen (PENDING) rezervasyonlar icin odeme acilabilir.",
        )

    paid_stmt = select(Payment).where(
        Payment.booking_id == booking_uuid, Payment.status == PaymentStatus.PAID
    )
    paid_result = await db.execute(paid_stmt)
    if paid_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu rezervasyon zaten odenmis durumda.",
        )

    payment = Payment(
        booking_id=booking_uuid,
        amount=float(booking.total_price),
        method=method,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    logger.info(f"Payment {payment.id} opened for booking {booking_uuid} via {method.value}.")
    return payment


async def mock_pay(
    db: AsyncSession,
    user_id: uuid.UUID | str,
    payment_id: uuid.UUID | str,
) -> Payment:
    """Simulate a successful card charge against a PENDING payment.

    On success the payment becomes PAID (with a mock ``transaction_id`` and
    ``paid_at``) and the linked booking is promoted to CONFIRMED.
    """
    payment_uuid = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

    stmt = select(Payment).where(Payment.id == payment_uuid)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )

    booking_stmt = select(Booking).where(Booking.id == payment.booking_id)
    booking_result = await db.execute(booking_stmt)
    booking = booking_result.scalar_one_or_none()

    if not booking or booking.user_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu odemeyi tamamlama yetkiniz yok.",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sadece bekleyen (PENDING) odemeler tamamlanabilir.",
        )

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rezervasyon bekleyen durumda olmadigi icin odeme tamamlanamadi.",
        )

    payment.status = PaymentStatus.PAID
    payment.transaction_id = _new_transaction_id()
    payment.paid_at = datetime.now(UTC)

    booking.status = BookingStatus.CONFIRMED

    await db.commit()
    await db.refresh(payment)
    logger.info(
        f"Payment {payment_uuid} marked PAID ({payment.transaction_id}); "
        f"booking {booking.id} confirmed."
    )
    return payment


async def refund_payment(
    db: AsyncSession,
    payment_id: uuid.UUID | str,
) -> Payment:
    """Admin-level refund: refunds a PAID payment and cancels its booking.

    The refunded amount is not re-chargeable; the booking is cancelled and
    its reserved seats are released back to the departure.
    """
    payment_uuid = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id

    stmt = select(Payment).where(Payment.id == payment_uuid)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )

    if payment.status != PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sadece odenmis (PAID) odemeler iade edilebilir.",
        )

    await booking_service.cancel_booking(payment.booking_id, db)

    payment.status = PaymentStatus.REFUNDED
    payment.refunded_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(payment)
    logger.info(f"Payment {payment_uuid} refunded; its booking was cancelled.")
    return payment
