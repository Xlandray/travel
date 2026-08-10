from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep, get_current_superuser
from app.models.booking import Booking, BookingStatus
from app.models.tour import Tour, TourDeparture
from app.schemas.base import Schema

router = APIRouter(dependencies=[Depends(get_current_superuser)])

PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


class BookingSummary(Schema):
    id: str
    tour_title: str
    user_email: str
    seat_count: int
    total_price: float
    status: BookingStatus
    created_at: datetime


class UpcomingDeparture(Schema):
    departure_id: str
    tour_title: str
    start_date: date
    end_date: date
    price: float
    total_quota: int
    available_seats: int
    sold_seats: int
    occupancy_percent: float


class DashboardResponse(Schema):
    total_tours: int
    total_departures: int
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    sold_seats_total: int
    confirmed_revenue: float
    upcoming_departures: list[UpcomingDeparture]
    recent_bookings: list[BookingSummary]


@router.get("/dashboard", response_model=DashboardResponse)
async def get_admin_dashboard(
    session: SessionDep,
    upcomings_page_size: PageSize = 8,
    upcomings_page: PageNumber = 1,
) -> DashboardResponse:
    """High-level operational KPIs for the admin panel."""
    total_tours = await session.scalar(select(func.count(Tour.id)))
    total_departures = await session.scalar(select(func.count(TourDeparture.id)))

    total_bookings = await session.scalar(select(func.count(Booking.id)))
    pending_bookings = await session.scalar(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.PENDING)
    )
    confirmed_bookings = await session.scalar(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.CONFIRMED)
    )
    cancelled_bookings = await session.scalar(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.CANCELLED)
    )
    sold_seats_total = await session.scalar(
        select(func.coalesce(func.sum(Booking.seat_count), 0)).where(
            Booking.status != BookingStatus.CANCELLED
        )
    )
    confirmed_revenue = float(
        await session.scalar(
            select(func.coalesce(func.sum(Booking.total_price), 0)).where(
                Booking.status == BookingStatus.CONFIRMED
            )
        )
    )

    dep_stmt = (
        select(TourDeparture, Tour.title)
        .join(Tour, Tour.id == TourDeparture.tour_id)
        .where(TourDeparture.start_date >= date.today(), TourDeparture.is_active.is_(True))
        .order_by(TourDeparture.start_date.asc())
        .offset((upcomings_page - 1) * upcomings_page_size)
        .limit(upcomings_page_size)
    )
    dep_result = await session.execute(dep_stmt)
    rows = dep_result.all()

    upcoming_departures: list[UpcomingDeparture] = []
    for departure, tour_title in rows:
        sold = departure.total_quota - departure.available_seats
        occupancy = (sold / departure.total_quota * 100) if departure.total_quota else 0.0
        upcoming_departures.append(
            UpcomingDeparture(
                departure_id=str(departure.id),
                tour_title=tour_title,
                start_date=departure.start_date,
                end_date=departure.end_date,
                price=float(departure.price),
                total_quota=departure.total_quota,
                available_seats=departure.available_seats,
                sold_seats=sold,
                occupancy_percent=round(occupancy, 1),
            )
        )

    recent_stmt = (
        select(Booking)
        .options(
            selectinload(Booking.departure).selectinload(TourDeparture.tour),
            selectinload(Booking.user),
        )
        .order_by(Booking.created_at.desc())
        .limit(6)
    )
    recent_result = await session.execute(recent_stmt)
    recent_bookings = [
        BookingSummary(
            id=str(b.id),
            tour_title=b.departure.tour.title if b.departure and b.departure.tour else "-",
            user_email=b.user.email if b.user else "-",
            seat_count=b.seat_count,
            total_price=float(b.total_price),
            status=b.status,
            created_at=b.created_at,
        )
        for b in recent_result.scalars().all()
    ]

    return DashboardResponse(
        total_tours=total_tours or 0,
        total_departures=total_departures or 0,
        total_bookings=total_bookings or 0,
        pending_bookings=pending_bookings or 0,
        confirmed_bookings=confirmed_bookings or 0,
        cancelled_bookings=cancelled_bookings or 0,
        sold_seats_total=int(sold_seats_total or 0),
        confirmed_revenue=confirmed_revenue or 0.0,
        upcoming_departures=upcoming_departures,
        recent_bookings=recent_bookings,
    )
