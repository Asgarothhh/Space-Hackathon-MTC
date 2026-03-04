from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProject(BaseModel):
    id: UUID
    name: str
    cpu_quota: int
    ram_quota: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserServerBase(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    cpu: int
    ram: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserServerCreate(BaseModel):
    name: str
    project_id: UUID
    cpu: int
    ram: int


class UserServerUpdate(BaseModel):
    server_id: UUID
    cpu: Optional[int] = None
    ram: Optional[int] = None


class UserServerRename(BaseModel):
    server_id: UUID
    new_name: str


class UserServerDisable(BaseModel):
    server_id: UUID


class UserServerDelete(BaseModel):
    server_id: UUID


class UserProjectsSearchResponse(BaseModel):
    projects: List[UserProject]

