# backend/schemas/vm.py
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class VMCreate(BaseModel):
    name: str = Field(..., max_length=255)
    cpu: int
    ram: int
    ssd: int
    network_speed: Optional[int] = None

class VMUpdate(BaseModel):
    cpu: int
    ram: int
    ssd: int
    network_speed: Optional[int] = None

class VMResponse(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    owner_id: Optional[UUID]
    cpu: int
    ram: int
    ssd: int
    network_speed: Optional[int] = None
    network_ipv4: Optional[str] = None
    network_ipv6: Optional[str] = None
    status: str
    docker_container_id: Optional[str] = None
    ssh_link: Optional[str] = None
    is_gateway: bool
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
