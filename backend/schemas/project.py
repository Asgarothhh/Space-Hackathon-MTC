# backend/schemas/project.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from pydantic import Field, ConfigDict

class ProjectCreateRequest(BaseModel):
    name: str
    cpu_quota: int = Field(..., ge=1, le=2147483647)
    ram_quota: int = Field(..., ge=1, le=2147483647)
    ssd_quota: int = Field(..., ge=1, le=2147483647)

class ProjectUpdateRequest(BaseModel):
    cpu_quota: int = Field(..., ge=1, le=2147483647)
    ram_quota: int = Field(..., ge=1, le=2147483647)
    ssd_quota: int = Field(..., ge=1, le=2147483647)

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

class ProjectActionResponse(BaseModel):
    job_id: UUID
    status: str
