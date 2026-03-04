from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.auth import User
from backend.models.compute import VirtualMachine
from backend.models.projects import Project


# ── Users ───────────────────────────────────────────────────────────

def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def soft_delete_user(db: Session, user_id: UUID) -> User | None:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Helpers ─────────────────────────────────────────────────────────

def _vm_ids_for_project(db: Session, project_id: UUID) -> List[UUID]:
    rows = (
        db.query(VirtualMachine.id)
        .filter(VirtualMachine.project_id == project_id)
        .all()
    )
    return [r[0] for r in rows]


def _project_with_server_ids(db: Session, project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "owner_id": project.owner_id,
        "cpu_quota": project.cpu_quota,
        "ram_quota": project.ram_quota,
        "ssd_quota": project.ssd_quota,
        "status": project.status,
        "created_at": project.created_at,
        "server_ids": _vm_ids_for_project(db, project.id),
    }


# ── "Servers" (= Projects) ─────────────────────────────────────────

def get_servers_for_user(db: Session, user_id: UUID) -> List[dict]:
    projects = db.query(Project).filter(Project.owner_id == user_id).all()
    return [_project_with_server_ids(db, p) for p in projects]


def get_server_by_id(db: Session, server_id: UUID) -> dict | None:
    project = db.query(Project).filter(Project.id == server_id).first()
    if not project:
        return None
    return _project_with_server_ids(db, project)


def create_server(
    db: Session,
    *,
    name: str,
    owner_id: UUID,
    cpu_quota: int,
    ram_quota: int,
    ssd_quota: int,
) -> Project:
    project = Project(
        name=name,
        owner_id=owner_id,
        cpu_quota=cpu_quota,
        ram_quota=ram_quota,
        ssd_quota=ssd_quota,
        status="active",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def change_server_status(
    db: Session,
    *,
    server_id: UUID,
    new_status: str,
) -> dict | None:
    project = db.query(Project).filter(Project.id == server_id).first()
    if not project:
        return None
    project.status = new_status
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_with_server_ids(db, project)


def delete_server(db: Session, server_id: UUID) -> dict | None:
    project = db.query(Project).filter(Project.id == server_id).first()
    if not project:
        return None
    result = _project_with_server_ids(db, project)
    db.delete(project)
    db.commit()
    return result


def get_disabled_servers(db: Session) -> List[dict]:
    projects = db.query(Project).filter(Project.status == "disabled").all()
    return [_project_with_server_ids(db, p) for p in projects]


def get_disabled_servers_for_user(db: Session, user_id: UUID) -> List[dict]:
    projects = (
        db.query(Project)
        .filter(Project.owner_id == user_id, Project.status == "disabled")
        .all()
    )
    return [_project_with_server_ids(db, p) for p in projects]
