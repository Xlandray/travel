import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.models.booking import Booking
from app.models.tour import TourDeparture
from app.schemas.booking import BookingCreate, BookingResponse, booking_to_response
from app.services import booking_service

router = APIRouter()

BOOKING_JOINED_LOAD = (
    selectinload(Booking.departure).selectinload(TourDeparture.tour),
    selectinload(Booking.user),
    selectinload(Booking.boarding_point),
    selectinload(Booking.payments),
)


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Tur Rezervasyonu Olustur",
    description="Kullanicidan gelen sefer ve koltuk bilgisine gore stok kilitleme islemi yapar.",
)
async def create_tour_booking(
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,  # JWT Guvenlik bariyeri (Depends(get_current_user))
    db: SessionDep,  # AsyncSession veritabani oturumu (Depends(get_session))
) -> BookingResponse:
    """Next.js'den gelen Pydantic BookingCreate verisi dogrulanir (orn: koltuk 10'dan kucuk mu?).

    Dogrulanan veri ve JWT'den okunan kullanici ID'si dogrudan servise aktarilir.
    """
    new_booking = await booking_service.create_booking(
        db=db,
        user_id=current_user.id,
        departure_id=booking_in.departure_id,
        seat_count=booking_in.seat_count,
        boarding_point_id=booking_in.boarding_point_id,
    )

    # Sepette kilitli kalan koltuklar icin 15 dakikalik zaman asimi gorevi
    background_tasks.add_task(booking_service.schedule_booking_timeout_release, new_booking.id, 900)

    return BookingResponse.model_validate(new_booking)


@router.get(
    "/me",
    response_model=list[BookingResponse],
    summary="Kullanicinin Rezervasyonlarini Listele",
)
async def list_my_bookings(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[BookingResponse]:
    """List all bookings for the authenticated user."""
    stmt = (
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .options(*BOOKING_JOINED_LOAD)
        .order_by(Booking.created_at.desc())
    )
    result = await session.execute(stmt)
    bookings = result.scalars().all()
    return [booking_to_response(b) for b in bookings]


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Rezervasyon Detaylarini Getir",
)
async def get_booking_details(
    booking_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> BookingResponse:
    """Get details for a specific booking owned by current user."""
    stmt = select(Booking).where(Booking.id == booking_id).options(*BOOKING_JOINED_LOAD)
    result = await session.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking or (booking.user_id != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadi.",
        )

    return booking_to_response(booking)


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Rezervasyonu Manuel Iptal Et ve Stogu Iade Et",
)
async def cancel_user_booking(
    booking_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> BookingResponse:
    """Cancel a booking manually and restore stock."""
    stmt = select(Booking).where(Booking.id == booking_id)
    result = await session.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking or (booking.user_id != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadi.",
        )

    await booking_service.cancel_expired_booking(booking_id=booking.id, db=session)
    await session.refresh(booking)
    return BookingResponse.model_validate(booking)
