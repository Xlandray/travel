import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentSuperuser, SessionDep
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelRead, HotelUpdate
from app.schemas.pagination import Page

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


@router.get("/{hotel_id}", response_model=HotelRead, summary="Otel Detayini Getir")
async def get_hotel(hotel_id: uuid.UUID, session: SessionDep) -> HotelRead:
    hotel = await session.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Otel bulunamadı.")
    return HotelRead.model_validate(hotel)


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
    hotel = Hotel(**hotel_in.model_dump())
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

    for field, value in hotel_in.model_dump(exclude_unset=True).items():
        setattr(hotel, field, value)

    await session.commit()
    await session.refresh(hotel)
    return HotelRead.model_validate(hotel)


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Otel Sil")
async def delete_hotel(hotel_id: uuid.UUID, session: SessionDep, _: CurrentSuperuser) -> None:
    hotel = await session.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Otel bulunamadı.")

    await session.delete(hotel)
    await session.commit()
