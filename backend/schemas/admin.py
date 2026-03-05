from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, field_serializer, ConfigDict, Field

from backend.schemas.auth import UserResponse
from backend.schemas.project import ProjectResponse
from backend.schemas.user import UserServerBase, UserServerCreate


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ── User ─────────────────────────────────────────────────────────────

class AdminUserInfo(UserResponse):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, dt: datetime) -> str:
        return _ensure_utc(dt).isoformat()


# ── Project ──────────────────────────────────────────────────────────

class AdminProjectCreateRequest(BaseModel):
    name: str
    cpu_quota: int = Field(8, ge=1, le=2147483647)
    ram_quota: int = Field(16384, ge=1, le=2147483647)
    ssd_quota: int = Field(100, ge=1, le=2147483647)


class AdminProjectResponse(ProjectResponse):
    model_config = ConfigDict(from_attributes=True)

    status: str
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, dt: datetime) -> str:
        return _ensure_utc(dt).isoformat()


# ── Server (VM) ──────────────────────────────────────────────────────

class AdminVMCreateRequest(UserServerCreate):
    project_id: UUID


class AdminVMResponse(UserServerBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, dt: datetime) -> str:
        return _ensure_utc(dt).isoformat()


class AdminVMInfoResponse(AdminVMResponse):
    """Расширенный ответ с нагрузкой (заглушка)."""
    cpu_usage_percent: float = 0.0
    ram_usage_percent: float = 0.0
    ssd_usage_percent: float = 0.0
    network_in_bytes: int = 0
    network_out_bytes: int = 0


# ── List wrappers ────────────────────────────────────────────────────

class AdminServersListResponse(BaseModel):
    servers: List[AdminVMResponse]


class AdminProjectsListResponse(BaseModel):
    projects: List[AdminProjectResponse]
