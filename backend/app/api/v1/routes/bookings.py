import uuid

from fastapi import APIRouter, HTTPException, status
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
    current_user: CurrentUser,  # JWT Guvenlik bariyeri (Depends(get_current_user))
    db: SessionDep,  # AsyncSession veritabani oturumu (Depends(get_session))
) -> BookingResponse:
    """Next.js'den gelen Pydantic BookingCreate verisi dogrulanir (orn: koltuk 10'dan kucuk mu?).

    Dogrulanan veri ve JWT'den okunan kullanici ID'si dogrudan servise aktarilir.

    Sepette kilitli kalan koltuklarin 15 dakika sonunda iadesi burada degil,
    lifespan'daki supurucude yapilir (`core/tasks.start_booking_sweeper`). Bu
    endpoint eskiden ayrica bir BackgroundTask ile 900 saniye uyuyup ayni isi
    tekrar ediyordu; o gorev sunucu yeniden baslayinca kayboluyor, her
    rezervasyon icin 15 dakika bir asyncio task'i mesgul tutuyor ve yanitin
    tamamlanmasini bekleyen istemcileri bloke ediyordu.
    """
    new_booking = await booking_service.create_booking(
        db=db,
        actor=current_user,
        departure_id=booking_in.departure_id,
        seat_count=booking_in.seat_count,
        boarding_point_id=booking_in.boarding_point_id,
    )

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
    """Cancel a booking manually and restore stock.

    Only ownership is checked here — it cannot change under us. Everything that
    can (the status, the seat count on the departure) is decided by the service
    while it holds the row lock, so two clicks on "cancel" release the seats
    once. Cancelling an already-cancelled booking is a no-op 200; a CONFIRMED
    one is a 409, because it has money against it and the refund route is its
    only exit.
    """
    stmt = select(Booking).where(Booking.id == booking_id)
    result = await session.execute(stmt)
    booking = result.scalar_one_or_none()

    if not booking or (booking.user_id != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadi.",
        )

    cancelled = await booking_service.cancel_pending_booking(
        db=session, booking_id=booking.id, actor=current_user
    )
    return BookingResponse.model_validate(cancelled)
