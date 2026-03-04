# backend/models/projects.py
import uuid
import enum
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, text, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from backend.models.db import Base

class ProjectStatus(enum.Enum):
    CREATING = "CREATING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETING = "DELETING"
    ERROR = "ERROR"

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "project_service"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    # owner_id может быть NULL — шаблон проекта, админ создаёт без привязки
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("auth_service.users.id", ondelete="CASCADE"), nullable=True)
    cpu_quota = Column(Integer, nullable=False, default=8)
    ram_quota = Column(Integer, nullable=False, default=16384)
    ssd_quota = Column(Integer, nullable=False, default=100)
    # динамические поля использования
    cpu_used = Column(Integer, nullable=False, server_default=text("0"))
    ram_used = Column(Integer, nullable=False, server_default=text("0"))
    ssd_used = Column(Integer, nullable=False, server_default=text("0"))
    # пометка, что проект уже выделен (allocated) пользователю
    is_allocated = Column(Boolean, nullable=False, server_default=text("false"))
    status = Column(Enum(ProjectStatus, name="project_status"), nullable=False, server_default=ProjectStatus.INACTIVE.value)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
