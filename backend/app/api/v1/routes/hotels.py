import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentSuperuser, SessionDep
from app.core.slug import generate_slug
from app.models.hotel import Hotel, TourHotel
from app.models.route import RouteStop
from app.models.tour import Tour
from app.schemas.hotel import HotelCreate, HotelRead, HotelUpdate
from app.schemas.pagination import Page
from app.schemas.tour import TourResponse

router = APIRouter()


@router.get(
    "",
    response_model=list[HotelRead] | Page[HotelRead],
    summary="Otelleri Listele",
)
@router.get(
    "/",
    response_model=list[HotelRead] | Page[HotelRead],
    summary="Otelleri Listele",
)
async def list_hotels(
    session: SessionDep,
    page: Annotated[int | None, Query(ge=1)] = None,
    page_size: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> list[HotelRead] | Page[HotelRead]:
    """List hotels.

    When `page`/`page_size` are provided, returns a Refine-compatible
    `Page[HotelRead]` payload ({data: [...], total}); otherwise returns a
    plain array.
    """
    base_stmt = select(Hotel).where(Hotel.is_active.is_(True))
    count_stmt = select(func.count()).select_from(Hotel).where(Hotel.is_active.is_(True))

    if page is not None and page_size is not None:
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(
            base_stmt.order_by(Hotel.name.asc()).offset((page - 1) * page_size).limit(page_size)
        )
        hotels = result.scalars().all()
        return Page[HotelRead](data=[HotelRead.model_validate(h) for h in hotels], total=total)

    result = await session.execute(base_stmt.order_by(Hotel.name.asc()))
    hotels = result.scalars().all()
    return [HotelRead.model_validate(h) for h in hotels]


@router.get("/{hotel_id}/tours", response_model=list[TourResponse], summary="Oteli Kullanan Turlar")
async def list_hotel_tours(hotel_id: str, session: SessionDep) -> list[TourResponse]:
    """List active tours that use this hotel (matched by id or slug)."""
    hotel = await _get_hotel(session, hotel_id)
    stmt = (
        select(Tour)
        .join(Tour.hotels)
        .where(TourHotel.hotel_id == hotel.id, Tour.is_active.is_(True))
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
            selectinload(Tour.hotels).selectinload(TourHotel.hotel),
            selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
        )
        .order_by(Tour.created_at.desc())
    )
    result = await session.execute(stmt)
    tours = result.scalars().all()
    from app.api.v1.routes.tours import _build_tour_response

    return [_build_tour_response(t) for t in tours]


@router.get("/{hotel_id}", response_model=HotelRead, summary="Otel Detayini Getir")
async def get_hotel(hotel_id: str, session: SessionDep) -> HotelRead:
    hotel = await _get_hotel(session, hotel_id)
    return HotelRead.model_validate(hotel)


async def _get_hotel(session: SessionDep, hotel_id: str) -> Hotel:
    is_uuid = None
    try:
        is_uuid = uuid.UUID(hotel_id)
    except ValueError:
        is_uuid = None

    stmt = select(Hotel).where(Hotel.id == is_uuid if is_uuid else Hotel.slug == hotel_id)
    result = await session.execute(stmt)
    hotel = result.scalar_one_or_none()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Otel bulunamadı.")
    return hotel


@router.post(
    "",
    response_model=HotelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Otel Olustur",
)
@router.post(
    "/",
    response_model=HotelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Otel Olustur",
)
async def create_hotel(
    hotel_in: HotelCreate, session: SessionDep, _: CurrentSuperuser
) -> HotelRead:
    data = hotel_in.model_dump()
    slug = _require_slug(data.get("slug") or generate_slug(data["name"]))
    await _ensure_slug_available(session, slug)
    data["slug"] = slug
    hotel = Hotel(**data)
    session.add(hotel)
    await session.commit()
    await session.refresh(hotel)
    return HotelRead.model_validate(hotel)


@router.patch("/{hotel_id}", response_model=HotelRead, summary="Otel Guncelle")
async def update_hotel(
    hotel_id: uuid.UUID, hotel_in: HotelUpdate, session: SessionDep, _: CurrentSuperuser
) -> HotelRead:
    hotel = await session.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Otel bulunamadı.")

    data = hotel_in.model_dump(exclude_unset=True)
    if "slug" in data:
        slug = _require_slug(data["slug"] or generate_slug(data.get("name") or hotel.name))
        await _ensure_slug_available(session, slug, exclude_id=hotel.id)
        data["slug"] = slug

    for field, value in data.items():
        setattr(hotel, field, value)

    await session.commit()
    await session.refresh(hotel)
    return HotelRead.model_validate(hotel)


def _require_slug(slug: str) -> str:
    """Slug'a çevrilebilir karakter içermeyen adlar için 422 döndür."""
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Otel adından slug üretilemedi; slug alanını elle doldurun.",
        )
    return slug


async def _ensure_slug_available(
    session: SessionDep, slug: str, exclude_id: uuid.UUID | None = None
):
    stmt = select(Hotel).where(Hotel.slug == slug)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing and existing.id != exclude_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu slug zaten kullanımda.",
        )


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Otel Sil")
async def delete_hotel(hotel_id: uuid.UUID, session: SessionDep, _: CurrentSuperuser) -> None:
    hotel = await session.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Otel bulunamadı.")

    await session.delete(hotel)
    await session.commit()
