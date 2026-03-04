import uuid
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from .db import Base

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "project_service"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("auth_service.users.id", ondelete="CASCADE"), nullable=False)
    cpu_quota = Column(Integer, nullable=False, default=8)
    ram_quota = Column(Integer, nullable=False, default=16384)
    ssd_quota = Column(Integer, nullable=False, default=100)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
