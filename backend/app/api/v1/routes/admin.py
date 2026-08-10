import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentSuperuser, SessionDep, get_current_superuser
from app.domain.exceptions import ResourceConflictError, ResourceNotFoundError
from app.schemas import (
    AdminUserUpdate,
    ContentCreate,
    ContentRead,
    ContentUpdate,
    Page,
    SettingCreate,
    SettingRead,
    SettingUpdate,
    UserRead,
)
from app.services.admin_user_service import AdminUserService
from app.services.content_service import ContentService
from app.services.setting_service import SettingService

router = APIRouter(dependencies=[Depends(get_current_superuser)])
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def not_found(error: ResourceNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


def conflict(error: ResourceConflictError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get("/users", response_model=Page[UserRead])
async def list_users(
    session: SessionDep, page: PageNumber = 1, page_size: PageSize = 25
) -> Page[UserRead]:
    data, total = await AdminUserService(session).list(page, page_size)
    return Page(data=[UserRead.model_validate(u) for u in data], total=total)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID, user_in: AdminUserUpdate, session: SessionDep
) -> UserRead:
    try:
        user = await AdminUserService(session).update(user_id, user_in)
        return UserRead.model_validate(user)
    except ResourceNotFoundError as error:
        raise not_found(error) from error


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, session: SessionDep) -> UserRead:
    try:
        user = await AdminUserService(session).get(user_id)
        return UserRead.model_validate(user)
    except ResourceNotFoundError as error:
        raise not_found(error) from error


@router.get("/contents", response_model=Page[ContentRead])
async def list_contents(
    session: SessionDep, page: PageNumber = 1, page_size: PageSize = 25
) -> Page[ContentRead]:
    data, total = await ContentService(session).list(page, page_size)
    return Page(data=[ContentRead.model_validate(c) for c in data], total=total)


@router.post("/contents", response_model=ContentRead, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_in: ContentCreate, session: SessionDep, current_user: CurrentSuperuser
) -> ContentRead:
    try:
        content = await ContentService(session).create(content_in, current_user.id)
        return ContentRead.model_validate(content)
    except ResourceConflictError as error:
        raise conflict(error) from error


@router.get("/contents/{content_id}", response_model=ContentRead)
async def get_content(content_id: uuid.UUID, session: SessionDep) -> ContentRead:
    try:
        content = await ContentService(session).get(content_id)
        return ContentRead.model_validate(content)
    except ResourceNotFoundError as error:
        raise not_found(error) from error


@router.patch("/contents/{content_id}", response_model=ContentRead)
async def update_content(
    content_id: uuid.UUID, content_in: ContentUpdate, session: SessionDep
) -> ContentRead:
    try:
        content = await ContentService(session).update(content_id, content_in)
        return ContentRead.model_validate(content)
    except ResourceNotFoundError as error:
        raise not_found(error) from error
    except ResourceConflictError as error:
        raise conflict(error) from error


@router.delete("/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(content_id: uuid.UUID, session: SessionDep) -> None:
    try:
        await ContentService(session).delete(content_id)
    except ResourceNotFoundError as error:
        raise not_found(error) from error


@router.get("/settings", response_model=Page[SettingRead])
async def list_settings(
    session: SessionDep, page: PageNumber = 1, page_size: PageSize = 25
) -> Page[SettingRead]:
    data, total = await SettingService(session).list(page, page_size)
    return Page(data=[SettingRead.model_validate(s) for s in data], total=total)


@router.post("/settings", response_model=SettingRead, status_code=status.HTTP_201_CREATED)
async def create_setting(setting_in: SettingCreate, session: SessionDep) -> SettingRead:
    try:
        setting = await SettingService(session).create(setting_in)
        return SettingRead.model_validate(setting)
    except ResourceConflictError as error:
        raise conflict(error) from error


@router.get("/settings/{setting_id}", response_model=SettingRead)
async def get_setting(setting_id: uuid.UUID, session: SessionDep) -> SettingRead:
    try:
        setting = await SettingService(session).get(setting_id)
        return SettingRead.model_validate(setting)
    except ResourceNotFoundError as error:
        raise not_found(error) from error


@router.patch("/settings/{setting_id}", response_model=SettingRead)
async def update_setting(
    setting_id: uuid.UUID, setting_in: SettingUpdate, session: SessionDep
) -> SettingRead:
    try:
        setting = await SettingService(session).update(setting_id, setting_in)
        return SettingRead.model_validate(setting)
    except ResourceNotFoundError as error:
        raise not_found(error) from error
    except ResourceConflictError as error:
        raise conflict(error) from error


@router.delete("/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(setting_id: uuid.UUID, session: SessionDep) -> None:
    try:
        await SettingService(session).delete(setting_id)
    except ResourceNotFoundError as error:
        raise not_found(error) from error
