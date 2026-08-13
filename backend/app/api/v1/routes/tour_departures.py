import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import Field, model_validator
from sqlalchemy import func, select

from app.api.deps import CurrentSuperuser, SessionDep
from app.models.booking import Booking
from app.models.tour import Tour, TourDeparture
from app.schemas.base import Schema
from app.schemas.pagination import Page
from app.schemas.tour import TourDepartureResponse, TourDepartureUpdate

router = APIRouter()


class TourDepartureCreate(Schema):
    tour_id: uuid.UUID
    start_date: date
    end_date: date
    price: float = Field(..., ge=0)
    total_quota: int = Field(..., ge=1)
    available_seats: int | None = Field(default=None, ge=0)
    is_active: bool = True

    @model_validator(mode="after")
    def _coherent(self) -> "TourDepartureCreate":
        if self.end_date < self.start_date:
            raise ValueError("Sefer bitiş tarihi başlangıç tarihinden önce olamaz.")
        if self.available_seats is not None and self.available_seats > self.total_quota:
            raise ValueError("Satıştaki koltuk sayısı otobüs kapasitesinden büyük olamaz.")
        return self


@router.get("", response_model=list[TourDepartureResponse] | Page[TourDepartureResponse])
@router.get("/", response_model=list[TourDepartureResponse] | Page[TourDepartureResponse])
async def list_tour_departures(
    session: SessionDep,
    tour_id: Annotated[uuid.UUID | None, Query()] = None,
    page: Annotated[int | None, Query(ge=1)] = None,
    page_size: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> list[TourDepartureResponse] | Page[TourDepartureResponse]:
    """Lists tour departures.

    When `page`/`page_size` are provided, returns a Refine-compatible
    `Page[TourDepartureResponse]` payload ({data: [...], total}); otherwise
    returns a plain array.
    """
    base_stmt = select(TourDeparture)
    count_stmt = select(func.count()).select_from(TourDeparture)
    if tour_id:
        base_stmt = base_stmt.where(TourDeparture.tour_id == tour_id)
        count_stmt = count_stmt.where(TourDeparture.tour_id == tour_id)

    if page is not None and page_size is not None:
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(
            base_stmt.order_by(TourDeparture.start_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        departures = result.scalars().all()
        return Page[TourDepartureResponse](
            data=[TourDepartureResponse.model_validate(d) for d in departures],
            total=total,
        )

    result = await session.execute(base_stmt)
    departures = result.scalars().all()
    return [TourDepartureResponse.model_validate(d) for d in departures]


@router.post("", response_model=TourDepartureResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TourDepartureResponse, status_code=status.HTTP_201_CREATED)
async def create_tour_departure(
    departure_in: TourDepartureCreate,
    session: SessionDep,
    _: CurrentSuperuser,
) -> TourDepartureResponse:
    """Creates a new tour departure / bus quota stock."""
    # Check if tour exists
    tour = await session.get(Tour, departure_in.tour_id)
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belirtilen tur bulunamadı.",
        )

    available = (
        departure_in.available_seats
        if departure_in.available_seats is not None
        else departure_in.total_quota
    )

    new_departure = TourDeparture(
        tour_id=departure_in.tour_id,
        start_date=departure_in.start_date,
        end_date=departure_in.end_date,
        price=departure_in.price,
        total_quota=departure_in.total_quota,
        available_seats=available,
        is_active=departure_in.is_active,
    )
    session.add(new_departure)
    await session.commit()
    await session.refresh(new_departure)

    return TourDepartureResponse.model_validate(new_departure)


@router.get(
    "/{departure_id}",
    response_model=TourDepartureResponse,
    summary="Sefer Detaylarini Getir",
)
async def get_tour_departure(
    departure_id: uuid.UUID,
    session: SessionDep,
) -> TourDepartureResponse:
    """Get a single tour departure by id."""
    departure = await session.get(TourDeparture, departure_id)
    if not departure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sefer bulunamadı.",
        )
    return TourDepartureResponse.model_validate(departure)


@router.patch(
    "/{departure_id}",
    response_model=TourDepartureResponse,
    summary="Sefer Guncelle",
)
async def update_tour_departure(
    departure_id: uuid.UUID,
    departure_in: TourDepartureUpdate,
    session: SessionDep,
    _: CurrentSuperuser,
) -> TourDepartureResponse:
    """Partially update a tour departure (dates, price, quota, active flag).

    Resizing the bus keeps the seats that are already sold. `total_quota` and
    `available_seats` are two halves of one ledger — the difference between them
    is what passengers are holding — so writing either one blindly is how a
    departure ends up with more confirmed passengers than seats.
    """
    departure = await session.get(TourDeparture, departure_id)
    if not departure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sefer bulunamadı.",
        )

    data = departure_in.model_dump(exclude_unset=True)

    start = data.get("start_date", departure.start_date)
    end = data.get("end_date", departure.end_date)
    if end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Sefer bitiş tarihi başlangıç tarihinden önce olamaz.",
        )

    held = departure.total_quota - departure.available_seats

    if "total_quota" in data:
        if data["total_quota"] < held:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Kapasite satılmış koltuk sayısının altına indirilemez (satılan: {held})."
                ),
            )
        # Kapasite degisiminde satilan koltuklar yerinde kalir, fark satisa acilir.
        data.setdefault("available_seats", data["total_quota"] - held)

    quota = data.get("total_quota", departure.total_quota)
    if data.get("available_seats", departure.available_seats) > quota:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Satıştaki koltuk sayısı otobüs kapasitesinden büyük olamaz.",
        )

    for field, value in data.items():
        setattr(departure, field, value)

    await session.commit()
    await session.refresh(departure)
    return TourDepartureResponse.model_validate(departure)


@router.delete(
    "/{departure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Seferi Sil",
)
async def delete_tour_departure(
    departure_id: uuid.UUID,
    session: SessionDep,
    _: CurrentSuperuser,
) -> None:
    """Delete a tour departure if it has no bookings."""
    departure = await session.get(TourDeparture, departure_id)
    if not departure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sefer bulunamadı.",
        )

    booking_stmt = select(Booking.id).where(Booking.departure_id == departure_id).limit(1)
    result = await session.execute(booking_stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu sefere bağlı rezervasyonlar var; silinemez.",
        )

    await session.delete(departure)
    await session.commit()
