import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.compute import VirtualMachine
from backend.models.projects import Project
from backend.services.orchestrator import enqueue_job, run_job_delete_vm, run_job_create_vm, _mark_job_failed, \
    _mark_job_success

logger = logging.getLogger(__name__)


def create_server(db: Session, owner_id: uuid.UUID, name: str, project_id: uuid.UUID, cpu: int, ram: int, ssd: int) -> VirtualMachine:
    # Проверка проекта и квот
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner_id).first()
    if not project:
        raise ValueError("Project not found or access denied")

    # Суммирование текущего использования (cpu/ram/ssd) — предполагается, что модель и БД синхронизированы
    total_cpu, total_ram, total_ssd = _sum_project_usage(db, project_id)
    if total_cpu + cpu > project.cpu_quota:
        raise ValueError("CPU quota exceeded")
    if total_ram + ram > project.ram_quota:
        raise ValueError("RAM quota exceeded")
    if total_ssd + ssd > project.ssd_quota:
        raise ValueError("SSD quota exceeded")

    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=name,
        project_id=project_id,
        cpu=cpu,
        ram=ram,
        ssd=ssd,
        status="CREATING",
        docker_container_id=None
    )
    db.add(vm)
    db.commit()
    db.refresh(vm)

    # Создаём задачу и пытаемся немедленно выполнить (если Docker доступен)
    enqueue_job(db, "VM", vm.id, "CREATE_VM")
    try:
        run_job_create_vm(db, vm)
    except Exception:
        # Если немедленный запуск не удался — задача остаётся в PENDING
        logger.exception("create_server: immediate run_job_create_vm failed for vm %s", vm.id)
    return vm


def _sum_project_usage(db: Session, project_id: uuid.UUID):
    # Суммирование ресурсов по проекту; предполагается, что VirtualMachine имеет поля cpu, ram, ssd
    totals = db.query(
        func.coalesce(func.sum(VirtualMachine.cpu), 0),
        func.coalesce(func.sum(VirtualMachine.ram), 0),
        func.coalesce(func.sum(VirtualMachine.ssd), 0),
    ).filter(VirtualMachine.project_id == project_id).one()
    return totals  # (total_cpu, total_ram, total_ssd)


def update_server(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID, cpu: int, ram: int, ssd: int) -> Optional[VirtualMachine]:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        return None

    # Простейшая проверка квот (можно расширить)
    vm.cpu = cpu
    vm.ram = ram
    vm.ssd = ssd
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def delete_server(db: Session, owner_id, server_id) -> bool:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        return False

    job = enqueue_job(db, "VM", vm.id, "DELETE_VM")

    # Попытка немедленного удаления через оркестратор
    try:
        if vm.docker_container_id:
            # run_job_delete_vm удалит контейнер (если есть) и запись VM
            run_job_delete_vm(db, vm)
            return True
        else:
            # Нет контейнера — удаляем запись и помечаем задачу SUCCESS
            try:
                db.delete(vm)
                db.commit()
                _mark_job_success(db, job)
                return True
            except Exception as e:
                db.rollback()
                _mark_job_failed(db, job, f"DB delete error: {e}")
                return True
    except Exception as e:
        _mark_job_failed(db, job, str(e))
        return True



def start_server(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID) -> Optional[VirtualMachine]:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        raise ValueError("VM not found or access denied")

    # Разрешаем запуск из этих состояний, добавили DISABLED
    allowed_to_start = {"STOPPED", "ERROR", "CREATING", "DISABLED"}
    if vm.status not in allowed_to_start:
        raise ValueError(f"VM status '{vm.status}' does not allow start")

    # Переводим в промежуточный статус и сохраняем намерение
    vm.status = "CREATING"
    db.add(vm)
    db.commit()
    db.refresh(vm)

    job = enqueue_job(db, "VM", vm.id, "START_VM")

    try:
        run_job_create_vm(db, vm)
    except Exception:
        logger.exception("start_server: immediate run_job_create_vm failed for vm %s", vm.id)

    try:
        db.refresh(vm)
    except Exception:
        logger.exception("start_server: refresh failed for vm %s", vm.id)
    return vm



def disable_server(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID) -> Optional[VirtualMachine]:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        return None
    vm.status = "DISABLED"
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def rename_server(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID, new_name: str) -> Optional[VirtualMachine]:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        return None
    vm.name = new_name
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def get_projects_for_user(db: Session, user_id: uuid.UUID, search: Optional[str] = None):
    q = db.query(Project).filter(Project.owner_id == user_id)
    if search:
        q = q.filter(Project.name.ilike(f"%{search}%"))
    return q.all()



