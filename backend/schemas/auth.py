# backend/schemas/auth.py
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
