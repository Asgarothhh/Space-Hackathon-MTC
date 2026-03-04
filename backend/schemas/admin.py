from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class AdminUserInfo(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminSoftDeleteUserResponse(BaseModel):
    id: UUID
    is_active: bool


class AdminServerInfo(BaseModel):
    """'Server' in admin context = Project + list of VM ids."""
    id: UUID
    name: str
    owner_id: UUID
    cpu_quota: int
    ram_quota: int
    ssd_quota: int
    status: str
    created_at: datetime
    server_ids: list[UUID] = []

    class Config:
        from_attributes = True


class AdminServerCreate(BaseModel):
    name: str
    owner_id: UUID
    cpu_quota: int = 8
    ram_quota: int = 16384
    ssd_quota: int = 100


class AdminServerStatusChange(BaseModel):
    server_id: UUID


class AdminServerCreatedResponse(BaseModel):
    id: UUID
    name: str
    status: str


class AdminDisabledServerSearchResult(AdminServerInfo):
    pass
