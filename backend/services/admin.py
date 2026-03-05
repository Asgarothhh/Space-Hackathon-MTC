import logging
from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.models.auth import User
from backend.models.compute import VirtualMachine
from backend.models.projects import Project, ProjectStatus
from backend.services.orchestrator import (
    enqueue_job,
    run_job_create_vm,
    run_job_delete_vm,
    run_job_create_project,
    run_job_stop_vm,
    run_job_delete_project,
    _mark_job_success,
    _mark_job_failed,
)

logger = logging.getLogger(__name__)


# ── Users ────────────────────────────────────────────────────────────

def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def admin_disable_user(db: Session, user_id: UUID) -> User | None:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    job = enqueue_job(db, "USER", user.id, "DISABLE_USER")
    try:
        user.is_active = False
        db.add(user)
        db.commit()
        db.refresh(user)
        _mark_job_success(db, job)
        return user
    except Exception as e:
        db.rollback()
        _mark_job_failed(db, job, str(e))
        return None


def admin_activate_user(db: Session, user_id: UUID) -> User | None:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    job = enqueue_job(db, "USER", user.id, "ACTIVATE_USER")
    try:
        user.is_active = True
        db.add(user)
        db.commit()
        db.refresh(user)
        _mark_job_success(db, job)
        return user
    except Exception as e:
        db.rollback()
        _mark_job_failed(db, job, str(e))
        return None


def admin_delete_user(db: Session, user_id: UUID) -> dict | None:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    job = enqueue_job(db, "USER", user.id, "DELETE_USER")
    data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }
    try:
        db.delete(user)
        db.commit()
        _mark_job_success(db, job)
        return data
    except Exception as e:
        db.rollback()
        _mark_job_failed(db, job, str(e))
        return None


# ── Projects ─────────────────────────────────────────────────────────

def admin_create_project(
    db: Session,
    *,
    owner_id: UUID,
    name: str,
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
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    try:
        run_job_create_project(db, project)
    except Exception:
        logger.exception(
            "Immediate run_job_create_project failed for project %s", project.id
        )
    return project


def admin_change_project_status(
    db: Session, *, project_id: UUID, new_status: str
) -> Project | None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    status_map = {
        "disabled": ProjectStatus.INACTIVE,
        "active": ProjectStatus.ACTIVE,
    }
    mapped_status = status_map.get(new_status, new_status)
    action = "DISABLE_PROJECT" if new_status == "disabled" else "ACTIVATE_PROJECT"
    job = enqueue_job(db, "PROJECT", project.id, action)
    try:
        project.status = mapped_status
        db.add(project)
        db.commit()
        db.refresh(project)
        _mark_job_success(db, job)
        return project
    except Exception as e:
        db.rollback()
        _mark_job_failed(db, job, str(e))
        return None


def admin_delete_project(db: Session, project_id: UUID) -> dict | None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    data = {
        "id": project.id,
        "name": project.name,
        "owner_id": project.owner_id,
        "cpu_quota": project.cpu_quota,
        "ram_quota": project.ram_quota,
        "ssd_quota": project.ssd_quota,
        "cpu_used": project.cpu_used,
        "ram_used": project.ram_used,
        "ssd_used": project.ssd_used,
        "is_allocated": project.is_allocated,
        "status": project.status,
        "created_at": project.created_at,
    }
    try:
        run_job_delete_project(db, project)
        return data
    except Exception as e:
        logger.exception(
            "admin_delete_project failed for project %s: %s", project_id, e
        )
        return None


def admin_get_project_info(db: Session, project_id: UUID) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()


def admin_list_projects_by_user(
    db: Session, user_id: UUID
) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.owner_id == user_id)
        .all()
    )


def admin_list_disabled_projects(db: Session) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.status == ProjectStatus.INACTIVE)
        .all()
    )


# ── Servers (VMs) ────────────────────────────────────────────────────

def admin_create_vm(
    db: Session,
    *,
    owner_id: UUID,
    name: str,
    project_id: UUID,
    cpu: int,
    ram: int,
    ssd: int,
) -> VirtualMachine:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == owner_id)
        .first()
    )
    if not project:
        raise ValueError("Project not found or user does not own it")

    vm = VirtualMachine(
        name=name,
        project_id=project_id,
        cpu=cpu,
        ram=ram,
        ssd=ssd,
        status="CREATING",
    )
    db.add(vm)
    db.commit()
    db.refresh(vm)
    try:
        run_job_create_vm(db, vm)
    except Exception:
        logger.exception("Immediate run_job_create_vm failed for VM %s", vm.id)
    return vm


def admin_change_vm_status(
    db: Session, *, server_id: UUID, new_status: str
) -> VirtualMachine | None:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == server_id).first()
    if not vm:
        return None

    if new_status == "DISABLED":
        try:
            run_job_stop_vm(db, vm)
        except Exception:
            logger.exception("run_job_stop_vm failed for VM %s", vm.id)
        db.refresh(vm)
        return vm

    if new_status == "RUNNING":
        vm.status = "CREATING"
        db.add(vm)
        db.commit()
        db.refresh(vm)
        try:
            run_job_create_vm(db, vm)
        except Exception:
            logger.exception("run_job_create_vm failed for VM %s", vm.id)
        db.refresh(vm)
        return vm

    job = enqueue_job(db, "VM", vm.id, f"CHANGE_STATUS_{new_status}")
    try:
        vm.status = new_status
        db.add(vm)
        db.commit()
        db.refresh(vm)
        _mark_job_success(db, job)
        return vm
    except Exception as e:
        db.rollback()
        _mark_job_failed(db, job, str(e))
        return None


def admin_delete_vm(db: Session, server_id: UUID) -> dict | None:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == server_id).first()
    if not vm:
        return None
    data = {
        "id": vm.id,
        "name": vm.name,
        "project_id": vm.project_id,
        "cpu": vm.cpu,
        "ram": vm.ram,
        "ssd": vm.ssd,
        "status": vm.status,
        "docker_container_id": vm.docker_container_id,
        "created_at": vm.created_at,
    }
    try:
        run_job_delete_vm(db, vm)
    except Exception:
        logger.exception("admin_delete_vm failed for VM %s", server_id)
    return data


def admin_get_server_info(
    db: Session, server_id: UUID
) -> VirtualMachine | None:
    return (
        db.query(VirtualMachine).filter(VirtualMachine.id == server_id).first()
    )


def admin_list_servers_by_user(
    db: Session, user_id: UUID
) -> List[VirtualMachine]:
    return (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(Project.owner_id == user_id)
        .all()
    )


def admin_list_servers_by_project(
    db: Session, project_id: UUID
) -> List[VirtualMachine]:
    return (
        db.query(VirtualMachine)
        .filter(VirtualMachine.project_id == project_id)
        .all()
    )


def admin_list_disabled_servers(db: Session) -> List[VirtualMachine]:
    return (
        db.query(VirtualMachine)
        .filter(VirtualMachine.status == "DISABLED")
        .all()
    )


def get_server_load(server_id: UUID) -> dict:
    """Заглушка: возвращает нулевую нагрузку. Заменить на реальный сбор метрик."""
    return {
        "cpu_usage_percent": 0.0,
        "ram_usage_percent": 0.0,
        "ssd_usage_percent": 0.0,
        "network_in_bytes": 0,
        "network_out_bytes": 0,
    }
