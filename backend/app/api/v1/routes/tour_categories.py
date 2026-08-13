import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentSuperuser, SessionDep
from app.core.slug import generate_slug
from app.models.tour import TourCategory
from app.schemas.pagination import Page
from app.schemas.tour import (
    TourCategoryCreate,
    TourCategoryResponse,
    TourCategoryUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=list[TourCategoryResponse] | Page[TourCategoryResponse],
    summary="Kategorileri Listele",
)
@router.get(
    "/",
    response_model=list[TourCategoryResponse] | Page[TourCategoryResponse],
    summary="Kategorileri Listele",
)
async def list_categories(
    session: SessionDep,
    page: Annotated[int | None, Query(ge=1)] = None,
    page_size: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> list[TourCategoryResponse] | Page[TourCategoryResponse]:
    """List all active tour categories.

    When `page`/`page_size` are provided, returns a Refine-compatible
    `Page[TourCategoryResponse]` payload ({data: [...], total}); otherwise
    returns a plain array.
    """
    base_stmt = select(TourCategory).where(TourCategory.is_active.is_(True))
    count_stmt = (
        select(func.count()).select_from(TourCategory).where(TourCategory.is_active.is_(True))
    )

    if page is not None and page_size is not None:
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(
            base_stmt.order_by(TourCategory.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        categories = result.scalars().all()
        return Page[TourCategoryResponse](
            data=[TourCategoryResponse.model_validate(c) for c in categories],
            total=total,
        )

    result = await session.execute(base_stmt)
    categories = result.scalars().all()
    return [TourCategoryResponse.model_validate(c) for c in categories]


@router.post(
    "",
    response_model=TourCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Kategori Olustur",
)
@router.post(
    "/",
    response_model=TourCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Kategori Olustur",
)
async def create_category(
    category_in: TourCategoryCreate,
    session: SessionDep,
    _: CurrentSuperuser,
) -> TourCategoryResponse:
    """Create a new tour category."""
    slug = category_in.slug or generate_slug(category_in.name)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Kategori adından slug üretilemedi; slug alanını elle doldurun.",
        )
    existing = await session.execute(select(TourCategory).where(TourCategory.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu slug zaten kullanımda.",
        )

    category = TourCategory(
        name=category_in.name,
        slug=slug,
        is_active=category_in.is_active,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return TourCategoryResponse.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=TourCategoryResponse,
    summary="Kategori Guncelle",
)
async def update_category(
    category_id: uuid.UUID,
    category_in: TourCategoryUpdate,
    session: SessionDep,
    _: CurrentSuperuser,
) -> TourCategoryResponse:
    """Partially update a tour category."""
    category = await session.get(TourCategory, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori bulunamadı.",
        )

    data = category_in.model_dump(exclude_unset=True)
    slug = data.pop("slug", None)
    if slug and slug != category.slug:
        existing = await session.execute(select(TourCategory).where(TourCategory.slug == slug))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu slug zaten kullanımda.",
            )
        category.slug = slug
    for field, value in data.items():
        setattr(category, field, value)

    await session.commit()
    await session.refresh(category)
    return TourCategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Kategoriyi Sil")
async def delete_category(category_id: uuid.UUID, session: SessionDep, _: CurrentSuperuser) -> None:
    """Delete a tour category (tours keep existing; category_id becomes NULL)."""
    category = await session.get(TourCategory, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori bulunamadı.",
        )

    await session.delete(category)
    await session.commit()
