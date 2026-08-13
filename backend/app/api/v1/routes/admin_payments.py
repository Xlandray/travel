import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep, get_current_superuser
from app.models.booking import BookingStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.schemas.pagination import Page
from app.schemas.payment import PaymentResponse
from app.services import payment_service

router = APIRouter(dependencies=[Depends(get_current_superuser)])

PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get("/payments", response_model=Page[PaymentResponse])
async def list_admin_payments(
    session: SessionDep,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    payment_status: PaymentStatus | None = None,
    method: PaymentMethod | None = None,
) -> Page[PaymentResponse]:
    """List all payments across the platform (paginated, optional filters)."""
    stmt = select(Payment).options(selectinload(Payment.booking))
    if payment_status:
        stmt = stmt.where(Payment.status == payment_status)
    if method:
        stmt = stmt.where(Payment.method == method)

    total_stmt = select(Payment.id)
    if payment_status:
        total_stmt = total_stmt.where(Payment.status == payment_status)
    if method:
        total_stmt = total_stmt.where(Payment.method == method)
    total = len((await session.execute(total_stmt)).scalars().all())

    stmt = stmt.order_by(Payment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    payments = result.scalars().all()

    return Page(data=[PaymentResponse.model_validate(p) for p in payments], total=total)


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_admin_payment(payment_id: uuid.UUID, session: SessionDep) -> PaymentResponse:
    """Get a single payment record and its booking context."""
    stmt = select(Payment).options(selectinload(Payment.booking)).where(Payment.id == payment_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )
    return PaymentResponse.model_validate(payment)


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_admin_payment(payment_id: uuid.UUID, session: SessionDep) -> PaymentResponse:
    """Refund a PAID payment; the linked booking is cancelled and seats released."""
    payment = await payment_service.refund_payment(session, payment_id)
    stmt = select(Payment).options(selectinload(Payment.booking)).where(Payment.id == payment.id)
    result = await session.execute(stmt)
    return PaymentResponse.model_validate(result.scalar_one())


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_transfer_payment(payment_id: uuid.UUID, session: SessionDep) -> PaymentResponse:
    """Manually confirm a TRANSFER payment (admin marks that the remittance arrived)."""
    payment_uuid = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id

    stmt = select(Payment).options(selectinload(Payment.booking)).where(Payment.id == payment_uuid)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sadece bekleyen (PENDING) odemeler onaylanabilir.",
        )

    # `payment_service.mock_pay` ile ayni kural: rezervasyon PENDING degilse
    # odeme tamamlanamaz. Iptal edilmis bir rezervasyonun koltuklari satisa
    # dondu, CONFIRMED olan ise zaten odenmis demektir.
    if payment.booking is None or payment.booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rezervasyon bekleyen durumda olmadığı için ödeme onaylanamadı.",
        )

    payment.status = PaymentStatus.PAID
    payment.paid_at = datetime.now(UTC)
    payment.transaction_id = payment.transaction_id or "ADMIN-CONFIRM"
    payment.booking.status = BookingStatus.CONFIRMED

    await session.commit()
    await session.refresh(payment)
    return PaymentResponse.model_validate(payment)
