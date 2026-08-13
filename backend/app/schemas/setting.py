import uuid
from datetime import datetime

from pydantic import Field, JsonValue

from app.schemas.base import Schema

# Dot-separated lowercase segments: `site`, `site.iletisim`, `site.iletisim.adres`.
# The pattern used to forbid the dot, which put it at odds with every setting the
# application actually reads — the customer footer looks up `site.iletisim.adres`,
# and no admin could create it, so that line was stuck on its hard-coded fallback
# forever. Leading/trailing/doubled dots and uppercase are still refused.
SETTING_KEY_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$"


class SettingCreate(Schema):
    key: str = Field(min_length=1, max_length=100, pattern=SETTING_KEY_PATTERN)
    value: dict[str, JsonValue]
    description: str | None = Field(default=None, min_length=1, max_length=255)


class SettingUpdate(Schema):
    value: dict[str, JsonValue] | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)


class SettingRead(Schema):
    id: uuid.UUID
    key: str
    value: dict[str, JsonValue]
    description: str | None
    created_at: datetime
    updated_at: datetime
