from pydantic import EmailStr, Field, field_validator

from app.schemas.base import Schema


class ContactCreate(Schema):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    message: str = Field(min_length=1)

    @field_validator("full_name")
    @classmethod
    def _single_line(cls, value: str) -> str:
        """Refuse control characters in the name.

        It is interpolated into the notification email's Subject header. Python's
        email layer rejects a header value containing CR or LF — that is what
        stops header injection — but it rejects it by raising, and the contact
        route does not catch it, so a newline in the name turned a public form
        into a 500. Bad input belongs in a 422.
        """
        if any(character < " " for character in value):
            raise ValueError("Ad alanı satır sonu veya kontrol karakteri içeremez.")
        return value


class ContactResponse(Schema):
    status: str
    message: str
