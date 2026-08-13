import logging
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.audit_log import AuditAction
from app.models.booking import BookingStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.services import audit_service, booking_service
from app.services.booking_service import lock_booking

logger = logging.getLogger(__name__)

# Kilit sirasi her yolda ayni: once rezervasyon, sonra odeme. Iki islem ters
# sirada kilit alirsa birbirlerini bekleyip deadlock olurlar.


def _lock_payment(payment_id: uuid.UUID) -> Select[tuple[Payment]]:
    """See `booking_service.lock_booking` for why populate_existing is required."""
    return (
        select(Payment)
        .where(Payment.id == payment_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def _booking_id_of(db: AsyncSession, payment_id: uuid.UUID) -> uuid.UUID:
    """Read which booking a payment belongs to, so it can be locked first."""
    result = await db.execute(select(Payment.booking_id).where(Payment.id == payment_id))
    booking_id = result.scalar_one_or_none()
    if booking_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )
    return booking_id


def _new_transaction_id(length: int = 16) -> str:
    """Short pseudo-random mock transaction reference (e.g. \"TXN-7f3a...\")."""
    return "TXN-" + secrets.token_hex(length // 2).upper()


async def create_payment(
    db: AsyncSession,
    actor: User,
    booking_id: uuid.UUID | str,
    method: PaymentMethod,
) -> Payment:
    """Open a payment attempt for a user-owned booking.

    The amount is always snapshotted from the booking's ``total_price``;
    a booking must be PENDING (not yet paid nor cancelled) and must not
    already have a PAID payment.

    The booking row is locked so this cannot interleave with `mock_pay` on the
    same booking; otherwise both read a PENDING booking with no PAID payment and
    the customer is charged twice.
    """
    booking_uuid = uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id

    result = await db.execute(lock_booking(booking_uuid))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadi.",
        )

    if booking.user_id != actor.id:
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
    await db.flush()

    audit_service.record(
        db,
        AuditAction.PAYMENT_OPENED,
        actor=actor,
        booking_id=booking_uuid,
        payment_id=payment.id,
        amount=payment.amount,
        detail={"method": method.value},
    )

    await db.commit()
    await db.refresh(payment)
    logger.info(f"Payment {payment.id} opened for booking {booking_uuid} via {method.value}.")
    return payment


async def mock_pay(
    db: AsyncSession,
    actor: User,
    payment_id: uuid.UUID | str,
) -> Payment:
    """Simulate a successful card charge against a PENDING payment.

    On success the payment becomes PAID (with a mock ``transaction_id`` and
    ``paid_at``) and the linked booking is promoted to CONFIRMED.

    Both rows are locked before any status is read. A booking may have several
    open attempts (card and transfer, say); without the booking lock two of them
    can be charged at the same instant, because each sees a booking that is
    still PENDING.
    """
    payment_uuid = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id

    booking_id = await _booking_id_of(db, payment_uuid)

    booking_result = await db.execute(lock_booking(booking_id))
    booking = booking_result.scalar_one_or_none()

    if not booking or booking.user_id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu odemeyi tamamlama yetkiniz yok.",
        )

    result = await db.execute(_lock_payment(payment_uuid))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
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

    audit_service.record(
        db,
        AuditAction.PAYMENT_PAID,
        actor=actor,
        booking_id=booking.id,
        payment_id=payment.id,
        amount=payment.amount,
        detail={"method": payment.method.value, "transaction_id": payment.transaction_id},
    )
    audit_service.record(
        db,
        AuditAction.BOOKING_CONFIRMED,
        actor=actor,
        booking_id=booking.id,
        payment_id=payment.id,
        amount=booking.total_price,
        detail={"seat_count": booking.seat_count, "by": "payment"},
    )

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
    actor: User,
) -> Payment:
    """Admin-level refund: refunds a PAID payment and cancels its booking.

    The refunded amount is not re-chargeable; the booking is cancelled and
    its reserved seats are released back to the departure.

    Locked in the usual order (booking, then payment) so that two admins hitting
    refund at once do not both see a PAID payment and refund it twice.
    """
    payment_uuid = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id

    booking_id = await _booking_id_of(db, payment_uuid)
    await db.execute(lock_booking(booking_id))

    result = await db.execute(_lock_payment(payment_uuid))
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

    # Sirasi onemli: `cancel_booking` icerde commit atiyor ve o commit satir
    # kilitlerini birakiyor. Odemeyi once isaretlemezsek, bekleyen ikinci istek
    # kilidi aldiginda odemeyi hala PAID gorur ve ayni parayi bir daha iade eder.
    payment.status = PaymentStatus.REFUNDED
    payment.refunded_at = datetime.now(UTC)

    # Money leaving the business. Written before `cancel_booking`, which
    # commits, so the entry is carried by that same commit rather than a later
    # one that might never happen.
    audit_service.record(
        db,
        AuditAction.PAYMENT_REFUNDED,
        actor=actor,
        booking_id=payment.booking_id,
        payment_id=payment.id,
        amount=payment.amount,
        detail={"method": payment.method.value, "transaction_id": payment.transaction_id},
    )

    await booking_service.cancel_booking(payment.booking_id, db, actor=actor)

    await db.commit()
    await db.refresh(payment)
    logger.info(f"Payment {payment_uuid} refunded; its booking was cancelled.")
    return payment


async def confirm_transfer(
    db: AsyncSession,
    payment_id: uuid.UUID | str,
    actor: User,
) -> Payment:
    """Admin marks a remittance as arrived: the payment is PAID, booking CONFIRMED.

    Same rules and same locking as `mock_pay`; only the trigger differs. This
    lived inline in the route with no locking and no booking-status check at
    all, so a transfer against a cancelled booking confirmed it without taking
    the seats back off sale.
    """
    payment_uuid = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id

    booking_id = await _booking_id_of(db, payment_uuid)

    booking = (await db.execute(lock_booking(booking_id))).scalar_one_or_none()
    payment = (await db.execute(_lock_payment(payment_uuid))).scalar_one_or_none()

    if not payment or not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sadece bekleyen (PENDING) odemeler onaylanabilir.",
        )

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rezervasyon bekleyen durumda olmadığı için ödeme onaylanamadı.",
        )

    payment.status = PaymentStatus.PAID
    payment.paid_at = datetime.now(UTC)
    payment.transaction_id = payment.transaction_id or "ADMIN-CONFIRM"
    booking.status = BookingStatus.CONFIRMED

    audit_service.record(
        db,
        AuditAction.PAYMENT_PAID,
        actor=actor,
        booking_id=booking.id,
        payment_id=payment.id,
        amount=payment.amount,
        detail={
            "method": payment.method.value,
            "transaction_id": payment.transaction_id,
            "by": "admin",
        },
    )
    audit_service.record(
        db,
        AuditAction.BOOKING_CONFIRMED,
        actor=actor,
        booking_id=booking.id,
        payment_id=payment.id,
        amount=booking.total_price,
        detail={"seat_count": booking.seat_count, "by": "admin"},
    )

    await db.commit()
    await db.refresh(payment)
    logger.info(f"Payment {payment_uuid} confirmed by admin; booking {booking_id} confirmed.")
    return payment
