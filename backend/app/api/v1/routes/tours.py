import uuid
from datetime import date as date_type
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentSuperuser, OptionalUser, SessionDep
from app.core.slug import generate_slug
from app.models.booking import Booking
from app.models.hotel import TourHotel
from app.models.route import RouteStop
from app.models.tour import BoardingPoint, Tour, TourCategory, TourDeparture, TourImage
from app.schemas.hotel import TourHotelRead
from app.schemas.pagination import Page
from app.schemas.route import RouteStopRead
from app.schemas.tour import (
    BoardingPointResponse,
    TourCategoryResponse,
    TourCreate,
    TourDepartureResponse,
    TourImageResponse,
    TourResponse,
    TourUpdate,
)

router = APIRouter()

DEFAULT_BOARDING_POINTS: list[BoardingPointResponse] = [
    BoardingPointResponse(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        name="Çorlu Merkez",
        description="Heykel önü kalkış",
    ),
    BoardingPointResponse(
        id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        name="Orion AVM Önü",
        description="Durak karşısı",
    ),
]


@router.get(
    "", response_model=list[TourResponse] | Page[TourResponse], summary="Aktif Turlari Listele"
)
async def list_tours(
    session: SessionDep,
    viewer: OptionalUser,
    boarding_point: Annotated[str | None, Query(description="Kalkış noktası filtresi")] = None,
    search_date: Annotated[date_type | None, Query(description="Kalkış tarihi filtresi")] = None,
    category_id: Annotated[uuid.UUID | None, Query(description="Kategori filtresi")] = None,
    page: Annotated[int | None, Query(ge=1)] = None,
    page_size: Annotated[int | None, Query(ge=1, le=100)] = None,
    include_inactive: Annotated[bool, Query()] = False,
) -> list[TourResponse] | Page[TourResponse]:
    """List tours with pricing, departures, categories and gallery.

    When `page`/`page_size` are provided, returns a Refine-compatible
    `Page[TourResponse]` payload ({data: [...], total}); otherwise returns a
    plain array (customer-facing site contract).

    Only active tours are listed unless a superuser passes `include_inactive`.
    The admin panel reads this same endpoint, and without the flag an unpublished
    tour is invisible on the only screen that could publish it again. Unpublished
    tours stay out of public responses.
    """
    if include_inactive and not (viewer and viewer.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pasif turları listelemek için yönetici yetkisi gerekir.",
        )

    base_stmt = select(Tour)
    count_stmt = select(func.count()).select_from(Tour)
    if not include_inactive:
        base_stmt = base_stmt.where(Tour.is_active.is_(True))
        count_stmt = count_stmt.where(Tour.is_active.is_(True))

    if boarding_point:
        base_stmt = base_stmt.join(Tour.boarding_points).where(BoardingPoint.name == boarding_point)
        count_stmt = count_stmt.join(Tour.boarding_points).where(
            BoardingPoint.name == boarding_point
        )
    if search_date:
        base_stmt = base_stmt.join(Tour.departures).where(TourDeparture.start_date == search_date)
        count_stmt = count_stmt.join(Tour.departures).where(TourDeparture.start_date == search_date)
    if category_id:
        base_stmt = base_stmt.where(Tour.category_id == category_id)
        count_stmt = count_stmt.where(Tour.category_id == category_id)

    if page is not None and page_size is not None:
        total = (await session.execute(count_stmt)).scalar_one()
        stmt = (
            base_stmt.options(
                selectinload(Tour.departures),
                selectinload(Tour.boarding_points),
                selectinload(Tour.category),
                selectinload(Tour.images),
                selectinload(Tour.hotels).selectinload(TourHotel.hotel),
                selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
            )
            .order_by(Tour.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        tours = result.scalars().all()
        return Page[TourResponse](data=[build_tour_response(t) for t in tours], total=total)

    stmt = base_stmt.options(
        selectinload(Tour.departures),
        selectinload(Tour.boarding_points),
        selectinload(Tour.category),
        selectinload(Tour.images),
        selectinload(Tour.hotels).selectinload(TourHotel.hotel),
        selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
    )
    result = await session.execute(stmt)
    tours = result.scalars().all()
    return [build_tour_response(t) for t in tours]


@router.post(
    "", response_model=TourResponse, status_code=status.HTTP_201_CREATED, summary="Yeni Tur Olustur"
)
@router.post(
    "/",
    response_model=TourResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Tur Olustur",
)
async def create_tour(
    tour_in: TourCreate,
    session: SessionDep,
    _: CurrentSuperuser,
) -> TourResponse:
    """Creates a new tour in database."""
    slug = tour_in.slug or generate_slug(tour_in.title)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Tur başlığından slug üretilemedi; slug alanını elle doldurun.",
        )

    if tour_in.category_id:
        category = await session.get(TourCategory, tour_in.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kategori bulunamadı.",
            )

    images = [
        TourImage(url=img.url, sort_order=img.sort_order, is_active=True) for img in tour_in.images
    ]
    hotels = [
        TourHotel(hotel_id=h.hotel_id, night_order=h.night_order, is_active=True)
        for h in tour_in.hotels
    ]
    route_stops = [
        RouteStop(
            day_number=r.day_number,
            sort_order=r.sort_order,
            title=r.title,
            description=r.description,
            is_active=True,
            boarding_points=(await _load_boarding_points(session, r.boarding_point_ids)),
        )
        for r in tour_in.route_stops
    ]

    new_tour = Tour(
        title=tour_in.title,
        slug=slug,
        description=tour_in.description or "",
        days=tour_in.days,
        nights=tour_in.nights,
        image_url=tour_in.image_url,
        is_active=tour_in.is_active,
        category_id=tour_in.category_id,
        images=images,
        hotels=hotels,
        route_stops=route_stops,
    )
    session.add(new_tour)
    await session.commit()
    await session.refresh(new_tour)

    stmt = (
        select(Tour)
        .where(Tour.id == new_tour.id)
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
            selectinload(Tour.hotels).selectinload(TourHotel.hotel),
            selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
        )
    )
    result = await session.execute(stmt)
    loaded = result.scalar_one()
    return build_tour_response(loaded)


@router.get(
    "/boarding-points",
    response_model=list[BoardingPointResponse],
    summary="Binis Noktalarini Listele",
)
async def list_boarding_points(session: SessionDep) -> list[BoardingPointResponse]:
    """List all active boarding points."""
    stmt = select(BoardingPoint).where(BoardingPoint.is_active.is_(True))
    result = await session.execute(stmt)
    points = result.scalars().all()

    if not points:
        return [
            BoardingPointResponse(
                id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                name="Çorlu Merkez",
                description="Heykel önü kalkış",
            ),
            BoardingPointResponse(
                id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
                name="Orion AVM Önü",
                description="Durak karşısı",
            ),
        ]

    return [BoardingPointResponse.model_validate(p) for p in points]


@router.get("/{tour_id}", response_model=TourResponse, summary="Tur Detaylarini Getir")
async def get_tour_by_slug(tour_id: str, session: SessionDep) -> TourResponse:
    """Get details for a specific tour by id or slug."""
    is_uuid = None
    try:
        is_uuid = uuid.UUID(tour_id)
    except ValueError:
        is_uuid = None

    stmt = (
        select(Tour)
        .where(Tour.id == is_uuid if is_uuid else Tour.slug == tour_id)
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
            selectinload(Tour.hotels).selectinload(TourHotel.hotel),
            selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
        )
    )
    result = await session.execute(stmt)
    tour = result.scalar_one_or_none()

    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tur bulunamadı.")

    return build_tour_response(tour)


async def _load_boarding_points(session: SessionDep, ids: list[uuid.UUID]) -> list[BoardingPoint]:
    """Load boarding points by id, silently skipping unknown ones."""
    if not ids:
        return []
    stmt = select(BoardingPoint).where(BoardingPoint.id.in_(ids))
    result = await session.execute(stmt)
    return list(result.scalars())


def build_tour_response(tour: Tour) -> TourResponse:
    min_price = min((d.price for d in tour.departures if d.is_active), default=0.0)
    tour_slug = (tour.slug or "").lower()
    return TourResponse(
        id=tour.id,
        title=tour.title,
        slug=tour.slug,
        description=tour.description,
        days=tour.days,
        nights=tour.nights,
        is_active=tour.is_active,
        price=min_price,
        image_url=getattr(tour, "image_url", None)
        or (
            "https://images.unsplash.com/photo-1641128324972-af3212f0f6bd?auto=format&fit=crop&w=800&q=80"
            if "kapadokya" in tour_slug
            else "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80"
        ),
        category_id=tour.category_id,
        # Pydantic already validated these ORM rows into the response models at
        # runtime; converting explicitly makes the code say so.
        category=(TourCategoryResponse.model_validate(tour.category) if tour.category else None),
        images=[TourImageResponse.model_validate(i) for i in tour.images if i.is_active],
        hotels=[TourHotelRead.model_validate(h) for h in tour.hotels if h.is_active],
        route_stops=[RouteStopRead.model_validate(r) for r in tour.route_stops if r.is_active],
        departures=[
            TourDepartureResponse.model_validate(d) for d in tour.departures if d.is_active
        ],
        boarding_points=(
            [
                BoardingPointResponse.model_validate(bp)
                for bp in tour.boarding_points
                if bp.is_active
            ]
            or DEFAULT_BOARDING_POINTS
        ),
    )


@router.patch("/{tour_id}", response_model=TourResponse, summary="Tur Guncelle")
async def update_tour(
    tour_id: uuid.UUID,
    tour_in: TourUpdate,
    session: SessionDep,
    _: CurrentSuperuser,
) -> TourResponse:
    """Partially update a tour by its id."""
    stmt = (
        select(Tour)
        .where(Tour.id == tour_id)
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
            selectinload(Tour.hotels).selectinload(TourHotel.hotel),
            selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
        )
    )
    result = await session.execute(stmt)
    tour = result.scalar_one_or_none()
    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tur bulunamadı.")

    data = tour_in.model_dump(exclude_unset=True)
    slug = data.pop("slug", None)
    data.pop("price", None)  # price inheritance is derived from departures, not a Tour column
    data.pop("images", None)  # images handled via tour_in.images (nested models)
    data.pop("hotels", None)  # hotels handled via tour_in.hotels (nested models)
    data.pop("route_stops", None)  # route stops handled via tour_in.route_stops
    if slug and slug != tour.slug:
        existing = await session.execute(select(Tour).where(Tour.slug == slug))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu slug zaten kullanımda.",
            )
        tour.slug = slug
    for field, value in data.items():
        setattr(tour, field, value)

    if tour_in.images is not None:
        tour.images.clear()
        await session.flush()
        tour.images = [
            TourImage(url=img.url, sort_order=img.sort_order, is_active=True)
            for img in tour_in.images
        ]

    if tour_in.hotels is not None:
        tour.hotels.clear()
        await session.flush()
        tour.hotels = [
            TourHotel(hotel_id=h.hotel_id, night_order=h.night_order, is_active=True)
            for h in tour_in.hotels
        ]

    if tour_in.route_stops is not None:
        tour.route_stops.clear()
        await session.flush()
        tour.route_stops = [
            RouteStop(
                day_number=r.day_number,
                sort_order=r.sort_order,
                title=r.title,
                description=r.description,
                is_active=True,
                boarding_points=await _load_boarding_points(session, r.boarding_point_ids),
            )
            for r in tour_in.route_stops
        ]

    await session.commit()
    await session.refresh(tour)

    stmt = (
        select(Tour)
        .where(Tour.id == tour_id)
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
            selectinload(Tour.hotels).selectinload(TourHotel.hotel),
            selectinload(Tour.route_stops).selectinload(RouteStop.boarding_points),
        )
    )
    result = await session.execute(stmt)
    loaded = result.scalar_one()
    return build_tour_response(loaded)


@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Turu Sil")
async def delete_tour(tour_id: uuid.UUID, session: SessionDep, _: CurrentSuperuser) -> None:
    """Delete a tour that has no active bookings on its departures."""
    stmt = (
        select(Tour)
        .where(Tour.id == tour_id)
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.images),
        )
    )
    result = await session.execute(stmt)
    tour = result.scalar_one_or_none()
    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tur bulunamadı.")

    departure_ids = [d.id for d in tour.departures]
    if departure_ids:
        booking_stmt = select(Booking.id).where(Booking.departure_id.in_(departure_ids)).limit(1)
        result = await session.execute(booking_stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu turun çıkışlarına ait rezervasyonlar var; silinemez.",
            )

    await session.delete(tour)
    await session.commit()
