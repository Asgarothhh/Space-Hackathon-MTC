# backend/schemas/auth.py
from typing import Optional

from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    is_2fa_enabled: bool = False

    class Config:
        orm_mode = True

# LoginRequest
class LoginRequest(BaseModel):
    email: str
    password: str
    totp: Optional[str] = None

# TokenResponse
class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    two_fa_required: Optional[bool] = False
    two_fa_token: Optional[str] = None
