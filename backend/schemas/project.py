from pydantic import BaseModel, Field, constr, conint
from uuid import UUID

class ProjectCreateRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255)
    cpu_quota: conint(ge=1) = Field(..., description="vCPU quota")
    ram_quota: conint(ge=1) = Field(..., description="RAM quota in MB")
    ssd_quota: conint(ge=1) = Field(..., description="SSD quota in GB")

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    cpu_quota: int
    ram_quota: int
    ssd_quota: int

    class Config:
        from_attributes = True
