# backend/services/vm.py
import uuid
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from backend.models.compute import VirtualMachine
from backend.models.projects import Project, ProjectStatus
from backend.services.orchestrator import (
    enqueue_job,
    run_job_create_vm,
    run_job_delete_vm,
    release_project_resources,
    _mark_job_failed,
    _mark_job_success,
)

logger = logging.getLogger(__name__)


def _sum_project_usage(db: Session, project_id: uuid.UUID):
    totals = db.query(
        func.coalesce(func.sum(VirtualMachine.cpu), 0),
        func.coalesce(func.sum(VirtualMachine.ram), 0),
        func.coalesce(func.sum(VirtualMachine.ssd), 0),
    ).filter(VirtualMachine.project_id == project_id).one()
    return totals  # (total_cpu, total_ram, total_ssd)


def _select_best_from_list(projects: List[Project], cpu: int, ram: int, ssd: int) -> Optional[Project]:
    """
    Выбрать best-fit проект из списка (минимизировать остаток после размещения).
    Не выполняет блокировок/изменений.
    """
    best = None
    best_score = None
    for p in projects:
        free_cpu = (p.cpu_quota or 0) - (p.cpu_used or 0)
        free_ram = (p.ram_quota or 0) - (p.ram_used or 0)
        free_ssd = (p.ssd_quota or 0) - (p.ssd_used or 0)
        if free_cpu < cpu or free_ram < ram or free_ssd < ssd:
            continue
        score = (free_cpu - cpu) + (free_ram - ram) + (free_ssd - ssd)
        if best is None or score < best_score:
            best = p
            best_score = score
    return best


def find_and_reserve_project_for_vm(db: Session, user_id: uuid.UUID, cpu: int, ram: int, ssd: int) -> Optional[Project]:
    """
    Найти наиболее подходящий проект и зарезервировать ресурсы.
    Поведение:
      - Если у пользователя есть один или несколько проектов (owner_id == user_id) — выбрать best-fit среди них.
      - Иначе — выбрать best-fit среди шаблонов (owner_id IS NULL, status == ACTIVE).
    Резервация выполняется транзакционно: после выбора проекта выполняется SELECT ... FOR UPDATE
    и повторная проверка квот перед изменением *_used и, при необходимости, установкой owner_id/is_allocated.
    """
    # 1) Попробовать найти проекты пользователя (может быть несколько)
    user_projects = db.query(Project).filter(Project.owner_id == user_id).all()
    if user_projects:
        # выбрать best-fit среди проектов пользователя
        candidate = _select_best_from_list(user_projects, cpu, ram, ssd)
        if candidate is None:
            raise ValueError("Quota exceeded in user's projects")
        # заблокировать выбранный проект и повторно проверить квоты
        proj_locked = db.query(Project).filter(Project.id == candidate.id).with_for_update().one()
        if (proj_locked.cpu_used or 0) + cpu > proj_locked.cpu_quota or (proj_locked.ram_used or 0) + ram > proj_locked.ram_quota or (proj_locked.ssd_used or 0) + ssd > proj_locked.ssd_quota:
            raise ValueError("Race: resources no longer available in user's project")
        proj_locked.cpu_used = (proj_locked.cpu_used or 0) + cpu
        proj_locked.ram_used = (proj_locked.ram_used or 0) + ram
        proj_locked.ssd_used = (proj_locked.ssd_used or 0) + ssd
        db.add(proj_locked)
        db.flush()
        logger.info("Reserved resources in existing project %s for user %s: cpu=%s ram=%s ssd=%s", proj_locked.id, user_id, cpu, ram, ssd)
        return proj_locked

    # 2) Иначе — искать шаблоны (owner_id IS NULL, ACTIVE)
    templates = db.query(Project).filter(Project.owner_id == None, Project.status == ProjectStatus.ACTIVE).all()
    if not templates:
        logger.info("No template projects available for allocation")
        return None

    candidate = _select_best_from_list(templates, cpu, ram, ssd)
    if candidate is None:
        logger.info("No suitable template project found for request cpu=%s ram=%s ssd=%s", cpu, ram, ssd)
        return None

    # Блокируем выбранный шаблон и повторно проверяем квоты
    proj_locked = db.query(Project).filter(Project.id == candidate.id).with_for_update().one()
    if (proj_locked.cpu_used or 0) + cpu > proj_locked.cpu_quota or (proj_locked.ram_used or 0) + ram > proj_locked.ram_quota or (proj_locked.ssd_used or 0) + ssd > proj_locked.ssd_quota:
        raise ValueError("Race: resources no longer available in template project")

    # Привязываем проект к пользователю и резервируем ресурсы
    proj_locked.owner_id = user_id
    proj_locked.is_allocated = True
    proj_locked.cpu_used = (proj_locked.cpu_used or 0) + cpu
    proj_locked.ram_used = (proj_locked.ram_used or 0) + ram
    proj_locked.ssd_used = (proj_locked.ssd_used or 0) + ssd
    db.add(proj_locked)
    db.flush()
    logger.info("Allocated template project %s to user %s and reserved cpu=%s ram=%s ssd=%s", proj_locked.id, user_id, cpu, ram, ssd)
    return proj_locked


def _create_vm_in_tx(db: Session, owner_id: uuid.UUID, name: str, cpu: int, ram: int, ssd: int) -> VirtualMachine:
    """
    Вспомогательная функция, выполняемая внутри транзакции: резервирует проект и создаёт запись VM.
    """
    project = find_and_reserve_project_for_vm(db, owner_id, cpu, ram, ssd)
    if project is None:
        raise ValueError("No suitable project found")
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=name,
        project_id=project.id,
        owner_id=owner_id,
        cpu=cpu,
        ram=ram,
        ssd=ssd,
        status="CREATING",
        docker_container_id=None,
    )
    db.add(vm)
    db.flush()
    logger.info("Created VM record %s in DB (project=%s owner=%s)", vm.id, project.id, owner_id)
    return vm


def create_server(db: Session, owner_id: uuid.UUID, name: str, cpu: int, ram: int, ssd: int) -> VirtualMachine:
    """
    Создать VM для пользователя:
      - найти и зарезервировать проект (best-fit);
      - создать запись VM (в транзакции, если сессия не в транзакции);
      - enqueue provisioning job и попытаться запустить синхронно;
      - при ошибке provisioning — откат usage (keep: не снимаем owner).
    """
    vm = None
    project = None
    try:
        # Если сессия уже в транзакции, выполняем в текущем контексте; иначе создаём новую транзакцию.
        if getattr(db, "in_transaction", None) and db.in_transaction():
            vm = _create_vm_in_tx(db, owner_id, name, cpu, ram, ssd)
            project = db.query(Project).filter(Project.id == vm.project_id).one_or_none()
        else:
            with db.begin():
                vm = _create_vm_in_tx(db, owner_id, name, cpu, ram, ssd)
                project = db.query(Project).filter(Project.id == vm.project_id).one_or_none()

        # Вне транзакции: enqueue provisioning job
        job = enqueue_job(db, "VM", vm.id, "CREATE_VM")
        try:
            run_job_create_vm(db, vm)
        except Exception:
            logger.exception("Provisioning deferred for vm %s", vm.id)
        try:
            db.refresh(vm)
        except Exception:
            logger.exception("create_server: refresh failed for vm %s", getattr(vm, "id", "<unknown>"))
        return vm

    except Exception as e:
        logger.exception("create_server failed: %s", e)
        # Если проект был зарезервирован, попытаться откатить usage (keep: не снимаем owner)
        try:
            if project is not None:
                release_project_resources(db, project.id, cpu, ram, ssd, maybe_unassign_owner=False)
        except Exception:
            logger.exception("Failed to release project resources after create_server failure")
        raise


def delete_server(db: Session, owner_id, server_id) -> bool:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        return False

    job = enqueue_job(db, "VM", vm.id, "DELETE_VM")

    try:
        if vm.docker_container_id:
            run_job_delete_vm(db, vm)
            return True
        else:
            project_id = vm.project_id
            cpu = vm.cpu or 0
            ram = vm.ram or 0
            ssd = vm.ssd or 0
            try:
                db.delete(vm)
                db.commit()
                try:
                    # уменьшаем usage, но НЕ снимаем привязку проекта (keep)
                    release_project_resources(db, project_id, cpu, ram, ssd, maybe_unassign_owner=False)
                except Exception:
                    logger.exception("Failed to release project resources after VM deletion %s", vm.id)
                _mark_job_success(db, job)
                return True
            except Exception as e:
                db.rollback()
                _mark_job_failed(db, job, f"DB delete error: {e}")
                return True
    except Exception as e:
        _mark_job_failed(db, job, str(e))
        return True


def update_server(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID, cpu: int, ram: int, ssd: int) -> Optional[VirtualMachine]:
    """
    Обновление ресурсов VM (простая версия).
    В продакшене нужно: проверить квоты проекта, скорректировать project.*_used транзакционно.
    """
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        return None

    vm.cpu = cpu
    vm.ram = ram
    vm.ssd = ssd
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def start_server(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID) -> Optional[VirtualMachine]:
    vm = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id)\
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id).first()
    if not vm:
        raise ValueError("VM not found or access denied")

    allowed_to_start = {"STOPPED", "ERROR", "CREATING", "DISABLED"}
    if vm.status not in allowed_to_start:
        raise ValueError(f"VM status '{vm.status}' does not allow start")

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
    """
    Перевести VM в статус DISABLED (пользовательская операция).
    """
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
