import uuid
from datetime import date as date_type
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.models.booking import Booking
from app.models.tour import BoardingPoint, Tour, TourCategory, TourDeparture, TourImage
from app.schemas.tour import (
    BoardingPointResponse,
    TourCreate,
    TourResponse,
    TourUpdate,
)

router = APIRouter()

# Default fallback tour data if database is initial
DEFAULT_TOURS: list[dict] = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "title": "Kapadokya Turu",
        "slug": "kapadokya-turu",
        "description": "Sicak hava balonlari, peribacalari ve yeralti sehirleriyle dolu unutulmaz bir deneyim.",
        "days": 3,
        "nights": 2,
        "is_active": True,
        "price": 6500.0,
        "image_url": "https://images.unsplash.com/photo-1641128324972-af3212f0f6bd?auto=format&fit=crop&w=800&q=80",
        "departures": [],
        "boarding_points": [
            {
                "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
                "name": "Çorlu Merkez",
                "description": "Heykel önü kalkış",
            },
            {
                "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
                "name": "Orion AVM Önü",
                "description": "Durak karşısı",
            },
        ],
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "title": "Salda Gölü ve Pamukkale",
        "slug": "salda-golu-ve-pamukkale",
        "description": "Türkiye'nin Maldivleri Salda Gölü'nün turkuaz sularinda ve bembeyaz travertenlerde harika bir gün.",
        "days": 1,
        "nights": 0,
        "is_active": True,
        "price": 2100.0,
        "image_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
        "departures": [],
        "boarding_points": [
            {
                "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
                "name": "Çorlu Merkez",
                "description": "Heykel önü kalkış",
            },
            {
                "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
                "name": "Orion AVM Önü",
                "description": "Durak karşısı",
            },
        ],
    },
]


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


def generate_slug(title: str) -> str:
    tbl = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    clean = title.translate(tbl).lower()
    return "-".join(clean.split())


@router.get("", response_model=list[TourResponse], summary="Aktif Turlari Listele")
async def list_tours(
    session: SessionDep,
    boarding_point: Annotated[str | None, Query(description="Kalkış noktası filtresi")] = None,
    search_date: Annotated[date_type | None, Query(description="Kalkış tarihi filtresi")] = None,
    category_id: Annotated[uuid.UUID | None, Query(description="Kategori filtresi")] = None,
) -> list[TourResponse]:
    """List all active tours with pricing, departures, categories, and gallery."""
    stmt = (
        select(Tour)
        .where(Tour.is_active.is_(True))
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
        )
    )
    if boarding_point:
        stmt = stmt.join(Tour.boarding_points).where(BoardingPoint.name == boarding_point)
    if search_date:
        stmt = stmt.join(Tour.departures).where(TourDeparture.start_date == search_date)
    if category_id:
        stmt = stmt.where(Tour.category_id == category_id)
    result = await session.execute(stmt)
    tours = result.scalars().all()

    if not tours:
        return [TourResponse.model_validate(t, from_attributes=False) for t in DEFAULT_TOURS]

    return [_build_tour_response(t) for t in tours]


@router.post(
    "", response_model=TourResponse, status_code=status.HTTP_201_CREATED, summary="Yeni Tur Olustur"
)
@router.post(
    "/",
    response_model=TourResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Tur Olustur",
)
async def create_tour(tour_in: TourCreate, session: SessionDep) -> TourResponse:
    """Creates a new tour in database."""
    slug = tour_in.slug or generate_slug(tour_in.title)

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
        )
    )
    result = await session.execute(stmt)
    loaded = result.scalar_one()
    return _build_tour_response(loaded)


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


@router.get("/{slug}", response_model=TourResponse, summary="Tur Detaylarini Getir")
async def get_tour_by_slug(slug: str, session: SessionDep) -> TourResponse:
    """Get details for a specific tour by slug."""
    stmt = (
        select(Tour)
        .where(Tour.slug == slug, Tour.is_active.is_(True))
        .options(
            selectinload(Tour.departures),
            selectinload(Tour.boarding_points),
            selectinload(Tour.category),
            selectinload(Tour.images),
        )
    )
    result = await session.execute(stmt)
    tour = result.scalar_one_or_none()

    if not tour:
        for t in DEFAULT_TOURS:
            if t["slug"] == slug:
                return TourResponse.model_validate(t)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tur bulunamadı.")

    return _build_tour_response(tour)


def _build_tour_response(tour: Tour) -> TourResponse:
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
        category=tour.category,
        images=[img for img in tour.images if img.is_active],
        departures=[d for d in tour.departures if d.is_active],
        boarding_points=(
            [bp for bp in tour.boarding_points if bp.is_active] or DEFAULT_BOARDING_POINTS
        ),
    )


@router.patch("/{tour_id}", response_model=TourResponse, summary="Tur Guncelle")
async def update_tour(
    tour_id: uuid.UUID,
    tour_in: TourUpdate,
    session: SessionDep,
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
        )
    )
    result = await session.execute(stmt)
    loaded = result.scalar_one()
    return _build_tour_response(loaded)


@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Turu Sil")
async def delete_tour(tour_id: uuid.UUID, session: SessionDep) -> None:
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
