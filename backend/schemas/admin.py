from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class AdminUserBase(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class AdminUserInfo(AdminUserBase):
    class Config:
        from_attributes = True


class AdminSoftDeleteUserResponse(BaseModel):
    id: UUID
    is_active: bool


class AdminServerBase(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    cpu: int
    ram: int
    ssd: int
    status: str
    created_at: datetime


class AdminServerInfo(AdminServerBase):
    docker_container_id: Optional[str] = None

    class Config:
        from_attributes = True


class AdminServerCreate(BaseModel):
    name: str
    project_id: UUID
    cpu: int
    ram: int
    ssd: int


class AdminServerStatusChange(BaseModel):
    server_id: UUID


class AdminServerCreatedResponse(BaseModel):
    id: UUID
    name: str
    status: str


class AdminDisabledServerSearchResult(AdminServerInfo):
    pass

