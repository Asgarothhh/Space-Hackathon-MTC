# backend/schemas/vm.py
from typing import Optional
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from uuid import UUID
from datetime import datetime, timezone


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class VMCreate(BaseModel):
    name: str = Field(..., max_length=255)
    cpu: int = Field(..., ge=1, le=2147483647)
    ram: int = Field(..., ge=1, le=2147483647)
    ssd: int = Field(..., ge=1, le=2147483647)
    network_speed: Optional[int] = None

class VMUpdate(BaseModel):
    cpu: int = Field(..., ge=1, le=2147483647)
    ram: int = Field(..., ge=1, le=2147483647)
    ssd: int = Field(..., ge=1, le=2147483647)
    network_speed: Optional[int] = None

class VMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

    @field_serializer("created_at")
    def _serialize_created_at(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        return _ensure_utc(dt).isoformat()
