import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.models.booking import Booking
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services import payment_service

router = APIRouter()


class MockCardPay(BaseModel):
    """Simulated card payload for the mock payment step.

    Nothing sensitive is persisted — the backend immediately produces a
    fake ``transaction_id`` for a successful charge.
    """

    card_holder: str | None = Field(default=None, max_length=150)
    card_number: str | None = Field(default=None, min_length=12, max_length=19)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Rezervasyon Icin Odeme Baslat",
)
async def create_booking_payment(
    payment_in: PaymentCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> PaymentResponse:
    """Open a new payment attempt for one of the current user's PENDING bookings."""
    payment = await payment_service.create_payment(
        db=session,
        user_id=current_user.id,
        booking_id=payment_in.booking_id,
        method=payment_in.method,
    )
    return PaymentResponse.model_validate(payment)


@router.post(
    "/{payment_id}/pay",
    response_model=PaymentResponse,
    summary="Mock Kart Odemesini Tamamla",
    description="Simule edilmis bir kredi karti islemidir: rezervasyon CONFIRMED'e gecer.",
)
async def pay_booking(
    payment_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    _payload: MockCardPay | None = None,
) -> PaymentResponse:
    """Simulate a successful card charge and confirm the linked booking."""
    payment = await payment_service.mock_pay(
        db=session,
        user_id=current_user.id,
        payment_id=payment_id,
    )
    return PaymentResponse.model_validate(payment)


@router.get(
    "/me",
    response_model=list[PaymentResponse],
    summary="Kullanicinin Odemelerini Listele",
)
async def list_my_payments(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[PaymentResponse]:
    """List every payment attached to the current user's bookings."""
    stmt = (
        select(Payment)
        .join(Booking, Booking.id == Payment.booking_id)
        .where(Booking.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    result = await session.execute(stmt)
    payments = result.scalars().all()
    return [PaymentResponse.model_validate(p) for p in payments]


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Odeme Detayini Getir",
)
async def get_my_payment(
    payment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> PaymentResponse:
    """Get a single payment record owned by the current user."""
    stmt = select(Payment).options(selectinload(Payment.booking)).where(Payment.id == payment_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment or (
        payment.booking.user_id != current_user.id and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odeme bulunamadi.",
        )
    return PaymentResponse.model_validate(payment)
