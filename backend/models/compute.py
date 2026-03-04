import uuid

from sqlalchemy import Column, String, Integer, UUID, TIMESTAMP, text, ForeignKey

from backend.models.db import Base


class VirtualMachine(Base):
    __tablename__ = "virtual_machines"
    __table_args__ = {"schema": "compute_service"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project_service.projects.id", ondelete="CASCADE"), nullable=False)
    cpu = Column(Integer, nullable=False)
    ram = Column(Integer, nullable=False)
    ssd = Column(Integer, nullable=False)
    network_speed = Column(Integer, nullable=True)
    network_ipv4 = Column(String(50), nullable=True)
    network_ipv6 = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False)
    docker_container_id = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
