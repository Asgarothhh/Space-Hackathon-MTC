from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic import EmailStr, field_validator
from uuid import UUID


_email_adapter = TypeAdapter(EmailStr)


def _normalize_email_to_ascii(value: str) -> str:
    validated = _email_adapter.validate_python(value)
    email = str(validated)

    if "@" not in email:
        raise ValueError("Invalid email")

    local, domain = email.rsplit("@", 1)
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except Exception as exc:  # pragma: no cover
        raise ValueError("Invalid email") from exc

    normalized = f"{local}@{ascii_domain}"
    if not normalized.isascii():
        raise ValueError("Invalid email")
    return normalized


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    password: str = Field(..., min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def _email_normalize_ascii(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("Invalid email")
        return _normalize_email_to_ascii(v)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str
    is_active: bool

    @field_validator("email", mode="before")
    @classmethod
    def _email_normalize_ascii(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("Invalid email")
        return _normalize_email_to_ascii(v)
