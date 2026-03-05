import uuid
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, INET
from .db import Base

class Network(Base):
    __tablename__ = "networks"
    __table_args__ = {"schema": "network_service"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project_service.projects.id", ondelete="CASCADE"), nullable=False)
    cidr = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class IPAllocation(Base):
    __tablename__ = "ip_allocations"
    __table_args__ = {"schema": "network_service"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id = Column(UUID(as_uuid=True), ForeignKey("network_service.networks.id", ondelete="CASCADE"), nullable=False)
    vm_id = Column(UUID(as_uuid=True), nullable=False)
    ip_address = Column(INET, nullable=False)
    allocated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
