# backend/services/user.py
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.auth import User
from backend.models.projects import Project
from backend.models.compute import VirtualMachine
from backend.services.orchestrator import enqueue_job

logger = logging.getLogger(__name__)


def get_projects_for_user(db: Session, user_id: UUID, search: Optional[str] = None) -> List[Project]:
    q = db.query(Project).filter(Project.owner_id == user_id)
    if search:
        q = q.filter(Project.name.ilike(f"%{search}%"))
    return q.all()


def get_server_by_id(db: Session, server_id: UUID) -> Optional[VirtualMachine]:
    return db.query(VirtualMachine).filter(VirtualMachine.id == server_id).first()


def _sum_project_usage(db: Session, project_id: UUID) -> Tuple[int, int, int]:
    """
    Возвращает кортеж (total_cpu, total_ram, total_ssd) текущего использования в проекте.
    """
    totals = db.query(
        func.coalesce(func.sum(VirtualMachine.cpu), 0),
        func.coalesce(func.sum(VirtualMachine.ram), 0),
        func.coalesce(func.sum(VirtualMachine.ssd), 0),
    ).filter(VirtualMachine.project_id == project_id).one()
    return int(totals[0]), int(totals[1]), int(totals[2])


def create_server(
    db: Session,
    *,
    owner_id: UUID,
    name: str,
    project_id: UUID,
    cpu: int,
    ram: int,
    ssd: int,
) -> VirtualMachine:
    """
    Создаёт запись VM в БД, проверяет, что проект принадлежит пользователю и что квоты позволяют создание.
    Ставит статус CREATING и создаёт задачу в orchestrator (PENDING).
    """
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner_id).first()
    if not project:
        raise ValueError("Project not found or does not belong to user")

    # Проверка квот: суммарное использование + запрошенное <= квота
    total_cpu, total_ram, total_ssd = _sum_project_usage(db, project_id)
    if total_cpu + cpu > project.cpu_quota:
        raise ValueError("CPU quota exceeded")
    if total_ram + ram > project.ram_quota:
        raise ValueError("RAM quota exceeded")
    if total_ssd + ssd > getattr(project, "ssd_quota", 100):  # если в проекте есть ssd_quota
        raise ValueError("SSD quota exceeded")

    vm = VirtualMachine(
        name=name,
        project_id=project_id,
        cpu=cpu,
        ram=ram,
        ssd=ssd,
        status="CREATING",
    )
    try:
        db.add(vm)
        db.commit()
        db.refresh(vm)
    except Exception as e:
        db.rollback()
        logger.exception("DB error while creating VM: %s", e)
        raise

    # Создаём задачу оркестрации — worker выполнит создание контейнера
    try:
        enqueue_job(db, resource_type="VM", resource_id=vm.id, action="CREATE_VM")
    except Exception:
        # enqueue_job сам логирует и/или бросает; не откатываем создание VM, просто логируем
        logger.exception("Failed to enqueue CREATE_VM job for VM %s", vm.id)

    return vm


def update_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
    cpu: Optional[int] = None,
    ram: Optional[int] = None,
    ssd: Optional[int] = None,
) -> Optional[VirtualMachine]:
    """
    Обновляет характеристики VM (cpu/ram/ssd). Проверяет принадлежность проекта пользователю и квоты.
    """
    vm = get_server_by_id(db, server_id)
    if not vm:
        return None

    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return None

    # Если меняем ресурсы, проверяем квоты (учитываем текущее использование без этой VM)
    if any(v is not None for v in (cpu, ram, ssd)):
        # вычислим текущее суммарное использование без этой VM
        total_cpu = db.query(func.coalesce(func.sum(VirtualMachine.cpu), 0)).filter(
            VirtualMachine.project_id == vm.project_id, VirtualMachine.id != vm.id
        ).scalar() or 0
        total_ram = db.query(func.coalesce(func.sum(VirtualMachine.ram), 0)).filter(
            VirtualMachine.project_id == vm.project_id, VirtualMachine.id != vm.id
        ).scalar() or 0
        total_ssd = db.query(func.coalesce(func.sum(VirtualMachine.ssd), 0)).filter(
            VirtualMachine.project_id == vm.project_id, VirtualMachine.id != vm.id
        ).scalar() or 0

        new_cpu = cpu if cpu is not None else vm.cpu
        new_ram = ram if ram is not None else vm.ram
        new_ssd = ssd if ssd is not None else vm.ssd

        if total_cpu + new_cpu > project.cpu_quota:
            raise ValueError("CPU quota exceeded")
        if total_ram + new_ram > project.ram_quota:
            raise ValueError("RAM quota exceeded")
        if total_ssd + new_ssd > getattr(project, "ssd_quota", 100):
            raise ValueError("SSD quota exceeded")

    if cpu is not None:
        vm.cpu = cpu
    if ram is not None:
        vm.ram = ram
    if ssd is not None:
        vm.ssd = ssd

    try:
        db.add(vm)
        db.commit()
        db.refresh(vm)
    except Exception as e:
        db.rollback()
        logger.exception("DB error while updating VM %s: %s", vm.id, e)
        raise

    return vm


def rename_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
    new_name: str,
) -> Optional[VirtualMachine]:
    """
    Переименовать сервер. Проверяет права владельца.
    """
    vm = get_server_by_id(db, server_id)
    if not vm:
        return None

    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return None

    vm.name = new_name
    try:
        db.add(vm)
        db.commit()
        db.refresh(vm)
    except Exception as e:
        db.rollback()
        logger.exception("DB error while renaming VM %s: %s", vm.id, e)
        raise

    return vm


def disable_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
) -> Optional[VirtualMachine]:
    """
    Выключить/задизейблить сервер — пометить статус STOPPED.
    (Фактическая остановка контейнера выполняется оркестратором через задачу STOP_VM, если нужно.)
    """
    vm = get_server_by_id(db, server_id)
    if not vm:
        return None

    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return None

    # Меняем статус локально и ставим задачу на остановку контейнера
    vm.status = "STOPPED"
    try:
        db.add(vm)
        db.commit()
        db.refresh(vm)
    except Exception as e:
        db.rollback()
        logger.exception("DB error while disabling VM %s: %s", vm.id, e)
        raise

    try:
        enqueue_job(db, resource_type="VM", resource_id=vm.id, action="STOP_VM")
    except Exception:
        logger.exception("Failed to enqueue STOP_VM job for VM %s", vm.id)

    return vm


def delete_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
) -> bool:
    """
    Удалить сервер: ставим задачу DELETE_VM. Worker выполнит удаление контейнера и удалит запись VM.
    """
    vm = get_server_by_id(db, server_id)
    if not vm:
        return False

    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return False

    try:
        enqueue_job(db, resource_type="VM", resource_id=vm.id, action="DELETE_VM")
    except Exception:
        logger.exception("Failed to enqueue DELETE_VM job for VM %s", vm.id)
        return False

    return True


def get_project_usage(db: Session, project_id: UUID) -> dict:
    """
    Возвращает статистику использования ресурсов по проекту:
    total_cpu, total_ram, total_ssd, vm_count, by_status (dict).
    """
    total_cpu, total_ram, total_ssd = _sum_project_usage(db, project_id)
    vm_count = db.query(func.count(VirtualMachine.id)).filter(VirtualMachine.project_id == project_id).scalar() or 0
    status_rows = db.query(VirtualMachine.status, func.count(VirtualMachine.id)).filter(
        VirtualMachine.project_id == project_id
    ).group_by(VirtualMachine.status).all()
    by_status = {row[0]: int(row[1]) for row in status_rows}
    return {
        "total_cpu": int(total_cpu),
        "total_ram": int(total_ram),
        "total_ssd": int(total_ssd),
        "vm_count": int(vm_count),
        "by_status": by_status,
    }
