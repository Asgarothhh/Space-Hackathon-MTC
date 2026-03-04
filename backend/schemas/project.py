# backend/schemas/project.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class ProjectCreateRequest(BaseModel):
    name: str
    cpu_quota: int
    ram_quota: int
    ssd_quota: int

class ProjectUpdateRequest(BaseModel):
    cpu_quota: int
    ram_quota: int
    ssd_quota: int

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    # owner_id может быть NULL для шаблонов проектов, поэтому Optional
    owner_id: Optional[UUID] = None
    cpu_quota: int
    ram_quota: int
    ssd_quota: int
    cpu_used: int
    ram_used: int
    ssd_used: int
    is_allocated: bool
    status: str

    class Config:
        from_attributes = True

class ProjectActionResponse(BaseModel):
    job_id: UUID
    status: str
