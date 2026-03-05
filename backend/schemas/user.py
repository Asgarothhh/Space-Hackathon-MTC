# backend/schemas/user.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserServerCreate(BaseModel):
    name: str
    cpu: int
    ram: int
    ssd: int

class UserServerBase(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    cpu: int
    ram: int
    ssd: int
    status: str
    docker_container_id: Optional[str] = None

    class Config:
        from_attributes = True

class UserServerUpdate(BaseModel):
    server_id: UUID
    cpu: Optional[int] = None
    ram: Optional[int] = None
    ssd: Optional[int] = None

class UserServerRename(BaseModel):
    server_id: UUID
    new_name: str

class UserServerDisable(BaseModel):
    server_id: UUID

class UserServerDelete(BaseModel):
    server_id: UUID

class UserProjectsSearchResponse(BaseModel):
    projects: List[dict]
