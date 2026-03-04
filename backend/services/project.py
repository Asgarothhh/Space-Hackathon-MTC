import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.models.projects import Project
from uuid import UUID
from backend.services.orchestrator import enqueue_job, run_job_create_project, _mark_job_failed, _mark_job_success


logger = logging.getLogger(__name__)

# Ограничения (вынести в env при необходимости)
MAX_CPU_PER_PROJECT = 1000
MAX_RAM_PER_PROJECT = 1024 * 1024  # MB
MAX_SSD_PER_PROJECT = 10000  # GB

def _validate_quotas(cpu: int, ram: int, ssd: int):
    if cpu > MAX_CPU_PER_PROJECT:
        raise ValueError(f"cpu_quota exceeds maximum {MAX_CPU_PER_PROJECT}")
    if ram > MAX_RAM_PER_PROJECT:
        raise ValueError(f"ram_quota exceeds maximum {MAX_RAM_PER_PROJECT}")
    if ssd > MAX_SSD_PER_PROJECT:
        raise ValueError(f"ssd_quota exceeds maximum {MAX_SSD_PER_PROJECT}")


def create_project(db: Session, owner_id: UUID, name: str, cpu_quota: int, ram_quota: int, ssd_quota: int) -> Project:
    _validate_quotas(cpu_quota, ram_quota, ssd_quota)

    existing = db.query(Project).filter(Project.owner_id == owner_id, Project.name == name).first()
    if existing:
        return existing

    project = Project(name=name, owner_id=owner_id, cpu_quota=cpu_quota, ram_quota=ram_quota, ssd_quota=ssd_quota)
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
        logger.info("Created project %s for user %s", project.id, owner_id)
    except IntegrityError:
        db.rollback()
        existing = db.query(Project).filter(Project.owner_id == owner_id, Project.name == name).first()
        if existing:
            return existing
        raise
    except Exception:
        db.rollback()
        raise

    # --- orchestration: enqueue and try to run post-create job immediately ---
    try:
        # enqueue_job уже вызывается внутри run_job_create_project, но можно явно создать намерение:
        run_job_create_project(db, project)
    except Exception:
        # Если немедленное выполнение упало — задача уже создана или будет создана worker'ом.
        logger.exception("Immediate run_job_create_project failed for project %s", project.id)

    return project

