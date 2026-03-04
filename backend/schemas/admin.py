from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from backend.schemas.auth import UserResponse
from backend.schemas.project import ProjectResponse
from backend.schemas.user import UserServerBase, UserServerCreate


# ── User ─────────────────────────────────────────────────────────────

class AdminUserInfo(UserResponse):
    created_at: datetime


# ── Project ──────────────────────────────────────────────────────────

class AdminProjectCreateRequest(BaseModel):
    name: str
    cpu_quota: int = 8
    ram_quota: int = 16384
    ssd_quota: int = 100


class AdminProjectResponse(ProjectResponse):
    status: str
    created_at: datetime


# ── Server (VM) ──────────────────────────────────────────────────────

class AdminVMCreateRequest(UserServerCreate):
    pass


class AdminVMResponse(UserServerBase):
    created_at: datetime


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
