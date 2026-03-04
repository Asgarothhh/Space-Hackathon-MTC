# backend/services/project.py
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import uuid
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.models.projects import Project
from backend.models.network import Network
from backend.services.orchestrator import (
    enqueue_job,
    run_job_create_project,
    run_job_start_project,
    run_job_stop_project,
    run_job_delete_project,
)

logger = logging.getLogger(__name__)

# Ограничения (вынести в env при необходимости)
MAX_CPU_PER_PROJECT = 1000
MAX_RAM_PER_PROJECT = 1024 * 1024  # MB
MAX_SSD_PER_PROJECT = 10000  # GB

# Дефолтный CIDR для автоматически создаваемой сети (dev / тест)
DEFAULT_PROJECT_NETWORK_CIDR = "10.10.0.0/24"
DEFAULT_PROJECT_NETWORK_NAME = "default"


def _validate_quotas(cpu: int, ram: int, ssd: int):
    if cpu > MAX_CPU_PER_PROJECT:
        raise ValueError(f"cpu_quota exceeds maximum {MAX_CPU_PER_PROJECT}")
    if ram > MAX_RAM_PER_PROJECT:
        raise ValueError(f"ram_quota exceeds maximum {MAX_RAM_PER_PROJECT}")
    if ssd > MAX_SSD_PER_PROJECT:
        raise ValueError(f"ssd_quota exceeds maximum {MAX_SSD_PER_PROJECT}")


def create_project(db: Session, owner_id: Optional[UUID], name: str, cpu_quota: int, ram_quota: int, ssd_quota: int) -> Project:
    _validate_quotas(cpu_quota, ram_quota, ssd_quota)

    existing = db.query(Project).filter(Project.owner_id == owner_id, Project.name == name).first()
    if existing:
        return existing

    project = Project(name=name, owner_id=owner_id, cpu_quota=cpu_quota, ram_quota=ram_quota, ssd_quota=ssd_quota)
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
        logger.info("Created project %s owner=%s", project.id, str(owner_id))
    except IntegrityError:
        db.rollback()
        existing = db.query(Project).filter(Project.owner_id == owner_id, Project.name == name).first()
        if existing:
            return existing
        raise
    except Exception:
        db.rollback()
        raise

    # Создать дефолтную сеть для проекта (dev-поведение).
    # Ошибки при создании сети логируем, но не откатываем создание проекта.
    try:
        default_net = Network(
            id=uuid.uuid4(),
            name=DEFAULT_PROJECT_NETWORK_NAME,
            project_id=project.id,
            cidr=DEFAULT_PROJECT_NETWORK_CIDR
        )
        db.add(default_net)
        db.commit()
        logger.info("Created default network %s for project %s (cidr=%s)", default_net.id, project.id, DEFAULT_PROJECT_NETWORK_CIDR)
    except IntegrityError:
        db.rollback()
        # Если сеть с таким именем/ид уже существует — просто логируем и продолжаем
        logger.warning("Default network creation conflict for project %s; skipping creation", project.id)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("Failed to create default network for project %s", project.id)

    try:
        run_job_create_project(db, project)
    except Exception:
        logger.exception("Immediate run_job_create_project failed for project %s", project.id)

    return project


def _get_project_for_owner_check(db: Session, project_id: UUID, owner_id: UUID, is_admin: bool):
    if is_admin:
        return db.query(Project).filter(Project.id == project_id).first()
    return db.query(Project).filter(Project.id == project_id, Project.owner_id == owner_id).first()


def start_project(db: Session, owner_id: UUID, project_id: UUID, is_admin: bool = False):
    project = _get_project_for_owner_check(db, project_id, owner_id, is_admin)
    if not project:
        return None
    job = enqueue_job(db, "PROJECT", project.id, "START_PROJECT")
    try:
        run_job_start_project(db, project, job=job)
    except Exception:
        logger.exception("start_project: immediate run_job_start_project failed for project %s", project.id)
    return job


def stop_project(db: Session, owner_id: UUID, project_id: UUID, is_admin: bool = False):
    project = _get_project_for_owner_check(db, project_id, owner_id, is_admin)
    if not project:
        return None
    job = enqueue_job(db, "PROJECT", project.id, "STOP_PROJECT")
    try:
        run_job_stop_project(db, project, job=job)
    except Exception:
        logger.exception("stop_project: immediate run_job_stop_project failed for project %s", project.id)
    return job


def delete_project(db: Session, owner_id: UUID, project_id: UUID, is_admin: bool = False):
    project = _get_project_for_owner_check(db, project_id, owner_id, is_admin)
    if not project:
        return None
    job = enqueue_job(db, "PROJECT", project.id, "DELETE_PROJECT")
    try:
        run_job_delete_project(db, project, job=job)
    except Exception:
        logger.exception("delete_project: immediate run_job_delete_project failed for project %s", project.id)
    return job


def update_project(db: Session, owner_id: UUID, project_id: UUID, cpu_quota: int, ram_quota: int, ssd_quota: int, is_admin: bool = False) -> Optional[Project]:
    project = _get_project_for_owner_check(db, project_id, owner_id, is_admin)
    if not project:
        return None
    _validate_quotas(cpu_quota, ram_quota, ssd_quota)
    project.cpu_quota = cpu_quota
    project.ram_quota = ram_quota
    project.ssd_quota = ssd_quota
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_projects_for_admin(db: Session, search: Optional[str] = None) -> List[Project]:
    """
    Возвращает список проектов для админа. Если указан search — фильтрует по имени (ILIKE).
    """
    q = db.query(Project)
    if search:
        q = q.filter(Project.name.ilike(f"%{search}%"))
    return q.order_by(Project.created_at.desc()).all()
