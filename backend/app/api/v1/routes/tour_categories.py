import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.tour import TourCategory
from app.schemas.tour import (
    TourCategoryCreate,
    TourCategoryResponse,
    TourCategoryUpdate,
)

router = APIRouter()


def _generate_slug(name: str) -> str:
    tbl = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    clean = name.translate(tbl).lower()
    return "-".join(clean.split())


@router.get("", response_model=list[TourCategoryResponse], summary="Kategorileri Listele")
@router.get("/", response_model=list[TourCategoryResponse], summary="Kategorileri Listele")
async def list_categories(session: SessionDep) -> list[TourCategoryResponse]:
    """List all active tour categories."""
    stmt = select(TourCategory).where(TourCategory.is_active.is_(True))
    result = await session.execute(stmt)
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
) -> TourCategoryResponse:
    """Create a new tour category."""
    slug = category_in.slug or _generate_slug(category_in.name)
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
async def delete_category(category_id: uuid.UUID, session: SessionDep) -> None:
    """Delete a tour category (tours keep existing; category_id becomes NULL)."""
    category = await session.get(TourCategory, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori bulunamadı.",
        )

    await session.delete(category)
    await session.commit()
