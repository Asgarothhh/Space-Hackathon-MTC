import uuid
from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from .db import Base

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = {"schema": "orchestrator"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    action = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    error_message = Column(String)
    started_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    finished_at = Column(TIMESTAMP)
