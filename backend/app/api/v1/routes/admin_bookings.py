import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep, get_current_superuser
from app.models.booking import Booking, BookingStatus
from app.models.tour import TourDeparture
from app.schemas.booking import BookingResponse, booking_to_response
from app.schemas.pagination import Page
from app.services.booking_service import cancel_booking

router = APIRouter(dependencies=[Depends(get_current_superuser)])

PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]

BOOKING_JOINED_LOAD = (
    selectinload(Booking.departure).selectinload(TourDeparture.tour),
    selectinload(Booking.user),
    selectinload(Booking.boarding_point),
    selectinload(Booking.payments),
)


class BookingStatusUpdate(BaseModel):
    """Admin can only confirm bookings; cancellation uses the POST cancel route."""

    status: BookingStatus


@router.get("/bookings", response_model=Page[BookingResponse])
async def list_admin_bookings(
    session: SessionDep,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    booking_status: Annotated[BookingStatus | None, Query(alias="status")] = None,
) -> Page[BookingResponse]:
    """List all bookings across the platform (paginated, optional status filter)."""
    stmt = select(Booking).options(*BOOKING_JOINED_LOAD)
    if booking_status:
        stmt = stmt.where(Booking.status == booking_status)

    total_stmt = select(Booking.id)
    if booking_status:
        total_stmt = total_stmt.where(Booking.status == booking_status)
    total = len((await session.execute(total_stmt)).scalars().all())

    stmt = stmt.order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    bookings = result.scalars().all()

    return Page(data=[booking_to_response(b) for b in bookings], total=total)


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_admin_booking(booking_id: uuid.UUID, session: SessionDep) -> BookingResponse:
    """Get a single booking with joined tour/user details."""
    stmt = select(Booking).options(*BOOKING_JOINED_LOAD).where(Booking.id == booking_id)
    result = await session.execute(stmt)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı.",
        )
    return booking_to_response(booking)


@router.patch("/bookings/{booking_id}", response_model=BookingResponse)
async def update_admin_booking_status(
    booking_id: uuid.UUID, payload: BookingStatusUpdate, session: SessionDep
) -> BookingResponse:
    """Confirm a pending booking. Cancellation goes through POST .../cancel."""
    stmt = select(Booking).options(*BOOKING_JOINED_LOAD).where(Booking.id == booking_id)
    result = await session.execute(stmt)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı.",
        )

    if payload.status != BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Bu endpoint sadece 'confirmed' durumuna geçiş için kullanılır; iptal için cancel uç noktasını kullanın.",
        )

    booking.status = BookingStatus.CONFIRMED
    await session.commit()
    await session.refresh(booking)
    return booking_to_response(booking)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_admin_booking(booking_id: uuid.UUID, session: SessionDep) -> BookingResponse:
    """Cancel a booking (any status) and release the reserved seats back."""
    booking = await cancel_booking(booking_id, session)
    stmt = select(Booking).options(*BOOKING_JOINED_LOAD).where(Booking.id == booking.id)
    result = await session.execute(stmt)
    return booking_to_response(result.scalar_one())
