from fastapi import APIRouter

from app.api.deps import SessionDep
from app.services.setting_service import SettingService

router = APIRouter()


@router.get("/settings", response_model=dict[str, dict])
async def get_public_settings(session: SessionDep) -> dict[str, dict]:
    """Return all application settings as a key -> value map.

    Intended for the customer-facing site (footer contact info, social links, etc.).
    No authentication required; only values are exposed, not ids or timestamps.
    """
    return await SettingService(session).get_public()
