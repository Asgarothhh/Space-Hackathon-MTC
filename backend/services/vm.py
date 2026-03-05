# backend/services/vm.py
import uuid
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from backend.models.compute import VirtualMachine
from backend.models.projects import Project, ProjectStatus
from backend.services.orchestrator import (
    enqueue_job,
    run_job_create_vm,
    run_job_delete_vm,
    run_job_create_ssh_for_vm,
    release_project_resources,
    _mark_job_failed,
    _mark_job_success, run_job_stop_vm,
)
from backend.services.network import allocate_ip_for_vm, release_ips_for_vm
from uuid import UUID

logger = logging.getLogger(__name__)

# ── Дефолтные квоты для авто-созданного проекта ─────────────────────────────
DEFAULT_CPU_QUOTA = 47
DEFAULT_RAM_QUOTA = 126
DEFAULT_SSD_QUOTA = 1536


def _sum_project_usage(db: Session, project_id: uuid.UUID):
    totals = db.query(
        func.coalesce(func.sum(VirtualMachine.cpu), 0),
        func.coalesce(func.sum(VirtualMachine.ram), 0),
        func.coalesce(func.sum(VirtualMachine.ssd), 0),
    ).filter(VirtualMachine.project_id == project_id).one()
    return totals  # (total_cpu, total_ram, total_ssd)


def _select_best_from_list(projects, cpu: int, ram: int, ssd: int) -> Optional[Project]:
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


def _auto_create_project_for_user(db: Session, user_id: uuid.UUID) -> Project:
    """
    Автоматически создаёт дефолтный проект для пользователя,
    если у него нет ни одного проекта и нет шаблонных проектов.
    """
    project = Project(
        id=uuid.uuid4(),
        name="default",
        owner_id=user_id,
        cpu_quota=DEFAULT_CPU_QUOTA,
        ram_quota=DEFAULT_RAM_QUOTA,
        ssd_quota=DEFAULT_SSD_QUOTA,
        cpu_used=0,
        ram_used=0,
        ssd_used=0,
        is_allocated=True,
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    db.flush()
    logger.info(
        "Auto-created default project %s for user %s (cpu=%s ram=%s ssd=%s)",
        project.id, user_id,
        DEFAULT_CPU_QUOTA, DEFAULT_RAM_QUOTA, DEFAULT_SSD_QUOTA,
    )
    return project


def find_and_reserve_project_for_vm(
    db: Session, user_id: uuid.UUID, cpu: int, ram: int, ssd: int
) -> Optional[Project]:
    # ── 1. Ищем существующие проекты пользователя ───────────────────────────
    user_projects = db.query(Project).filter(Project.owner_id == user_id).all()

    if user_projects:
        candidate = _select_best_from_list(user_projects, cpu, ram, ssd)
        if candidate is None:
            raise ValueError("Quota exceeded in user's projects")

        proj_locked = (
            db.query(Project)
            .filter(Project.id == candidate.id)
            .with_for_update()
            .one()
        )
        if (
            (proj_locked.cpu_used or 0) + cpu > proj_locked.cpu_quota
            or (proj_locked.ram_used or 0) + ram > proj_locked.ram_quota
            or (proj_locked.ssd_used or 0) + ssd > proj_locked.ssd_quota
        ):
            raise ValueError("Race: resources no longer available in user's project")

        proj_locked.cpu_used = (proj_locked.cpu_used or 0) + cpu
        proj_locked.ram_used = (proj_locked.ram_used or 0) + ram
        proj_locked.ssd_used = (proj_locked.ssd_used or 0) + ssd
        db.add(proj_locked)
        db.flush()
        logger.info(
            "Reserved resources in existing project %s for user %s: cpu=%s ram=%s ssd=%s",
            proj_locked.id, user_id, cpu, ram, ssd,
        )
        return proj_locked

    # ── 2. Пробуем выделить шаблонный проект (owner_id = None) ──────────────
    templates = (
        db.query(Project)
        .filter(Project.owner_id == None, Project.status == ProjectStatus.ACTIVE)
        .all()
    )

    if templates:
        candidate = _select_best_from_list(templates, cpu, ram, ssd)
        if candidate is not None:
            proj_locked = (
                db.query(Project)
                .filter(Project.id == candidate.id)
                .with_for_update()
                .one()
            )
            if (
                (proj_locked.cpu_used or 0) + cpu > proj_locked.cpu_quota
                or (proj_locked.ram_used or 0) + ram > proj_locked.ram_quota
                or (proj_locked.ssd_used or 0) + ssd > proj_locked.ssd_quota
            ):
                raise ValueError("Race: resources no longer available in template project")

            proj_locked.owner_id = user_id
            proj_locked.is_allocated = True
            proj_locked.cpu_used = (proj_locked.cpu_used or 0) + cpu
            proj_locked.ram_used = (proj_locked.ram_used or 0) + ram
            proj_locked.ssd_used = (proj_locked.ssd_used or 0) + ssd
            db.add(proj_locked)
            db.flush()
            logger.info(
                "Allocated template project %s to user %s: cpu=%s ram=%s ssd=%s",
                proj_locked.id, user_id, cpu, ram, ssd,
            )
            return proj_locked
        else:
            logger.info(
                "Template projects exist but none fit cpu=%s ram=%s ssd=%s — auto-creating",
                cpu, ram, ssd,
            )

    # ── 3. Нет ни своих, ни шаблонных проектов → авто-создаём дефолтный ────
    logger.info(
        "No projects found for user %s — auto-creating default project", user_id
    )
    project = _auto_create_project_for_user(db, user_id)

    # Убеждаемся, что запрошенные ресурсы вмещаются
    if cpu > project.cpu_quota or ram > project.ram_quota or ssd > project.ssd_quota:
        raise ValueError(
            f"Requested resources (cpu={cpu}, ram={ram}, ssd={ssd}) exceed "
            f"default project quota (cpu={DEFAULT_CPU_QUOTA}, ram={DEFAULT_RAM_QUOTA}, ssd={DEFAULT_SSD_QUOTA})"
        )

    project.cpu_used = cpu
    project.ram_used = ram
    project.ssd_used = ssd
    db.add(project)
    db.flush()
    return project


def _create_vm_in_tx(
    db: Session,
    owner_id: uuid.UUID,
    name: str,
    cpu: int,
    ram: int,
    ssd: int,
    network_speed: Optional[int] = None,
) -> VirtualMachine:
    """
    Создаёт запись VM внутри транзакции и пытается выделить IP.
    network_speed — необязательный параметр (int).
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
        network_speed=network_speed,
        status="CREATING",
        docker_container_id=None,
    )
    db.add(vm)
    db.flush()

    # Попытка выделить IP для VM (ipv4, ipv6)
    try:
        ipv4, ipv6 = allocate_ip_for_vm(db, project.id, vm.id)
        if ipv4:
            vm.network_ipv4 = ipv4
        if ipv6:
            vm.network_ipv6 = ipv6
        db.add(vm)
        db.flush()
        logger.info("Allocated IPs for vm %s: ipv4=%s ipv6=%s", vm.id, ipv4, ipv6)
    except Exception:
        logger.exception("Failed to allocate IPs for vm %s", vm.id)

    return vm


def create_server(
    db: Session,
    owner_id: uuid.UUID,
    name: str,
    cpu: int,
    ram: int,
    ssd: int,
    network_speed: Optional[int] = None,
) -> VirtualMachine:
    """
    Создать VM для пользователя. network_speed передаётся и сохраняется в VM.
    Если у пользователя нет проектов — авто-создаётся дефолтный проект.
    """
    vm = None
    project = None
    try:
        if getattr(db, "in_transaction", None) and db.in_transaction():
            vm = _create_vm_in_tx(db, owner_id, name, cpu, ram, ssd, network_speed)
            project = db.query(Project).filter(Project.id == vm.project_id).one_or_none()
            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to commit after VM creation in existing transaction for vm %s",
                    getattr(vm, "id", "<unknown>"),
                )
                raise
        else:
            with db.begin():
                vm = _create_vm_in_tx(db, owner_id, name, cpu, ram, ssd, network_speed)
                project = db.query(Project).filter(Project.id == vm.project_id).one_or_none()
            # with db.begin() уже сделал commit

        job = enqueue_job(db, "VM", vm.id, "CREATE_VM")
        try:
            run_job_create_vm(db, vm)
        except Exception:
            logger.exception("Provisioning deferred for vm %s", vm.id)

        try:
            db.refresh(vm)
        except Exception:
            logger.exception(
                "create_server: refresh failed for vm %s",
                getattr(vm, "id", "<unknown>"),
            )
        return vm

    except Exception as e:
        logger.exception("create_server failed: %s", e)
        try:
            if project is not None:
                release_project_resources(
                    db, project.id, cpu, ram, ssd, maybe_unassign_owner=False
                )
        except Exception:
            logger.exception("Failed to release project resources after create_server failure")
        raise


def delete_server(db: Session, owner_id, server_id) -> bool:
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
    if not vm:
        return False

    job = enqueue_job(db, "VM", vm.id, "DELETE_VM")

    try:
        if vm.docker_container_id:
            run_job_delete_vm(db, vm)
            try:
                release_ips_for_vm(db, vm.id)
            except Exception:
                logger.exception("Failed to release IPs for vm %s after docker delete", vm.id)
            return True
        else:
            project_id = vm.project_id
            cpu = vm.cpu or 0
            ram = vm.ram or 0
            ssd = vm.ssd or 0
            try:
                try:
                    release_ips_for_vm(db, vm.id)
                except Exception:
                    logger.exception("Failed to release IPs for vm %s before DB delete", vm.id)
                db.delete(vm)
                db.commit()
                try:
                    release_project_resources(
                        db, project_id, cpu, ram, ssd, maybe_unassign_owner=False
                    )
                except Exception:
                    logger.exception(
                        "Failed to release project resources after VM deletion %s", vm.id
                    )
                _mark_job_success(db, job)
                return True
            except Exception as e:
                db.rollback()
                _mark_job_failed(db, job, f"DB delete error: {e}")
                return True
    except Exception as e:
        _mark_job_failed(db, job, str(e))
        return True


def update_server(
    db: Session,
    owner_id: UUID,
    server_id: UUID,
    cpu: Optional[int] = None,
    ram: Optional[int] = None,
    ssd: Optional[int] = None,
    network_speed: Optional[int] = None,
) -> Optional[VirtualMachine]:
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
    if not vm:
        return None

    if cpu is not None:
        vm.cpu = cpu
    if ram is not None:
        vm.ram = ram
    if ssd is not None:
        vm.ssd = ssd
    if network_speed is not None:
        vm.network_speed = network_speed

    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def start_server(
    db: Session, owner_id: uuid.UUID, server_id: uuid.UUID
) -> Optional[VirtualMachine]:
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
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


def create_ssh_link_for_vm(db: Session, owner_id: uuid.UUID, server_id: uuid.UUID):
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
    if not vm:
        return None
    job = enqueue_job(db, "VM", vm.id, "CREATE_SSH")
    try:
        run_job_create_ssh_for_vm(db, vm)
    except Exception:
        logger.exception("Immediate run_job_create_ssh_for_vm failed for vm %s", vm.id)
    try:
        db.refresh(vm)
    except Exception:
        logger.exception("create_ssh_link_for_vm: refresh failed for vm %s", vm.id)
    return job


def disable_server(
    db: Session, owner_id: uuid.UUID, server_id: uuid.UUID
) -> Optional[VirtualMachine]:
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
    if not vm:
        return None
    vm.status = "DISABLED"
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def rename_server(
    db: Session, owner_id: uuid.UUID, server_id: uuid.UUID, new_name: str
) -> Optional[VirtualMachine]:
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
    if not vm:
        return None
    vm.name = new_name
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def get_vm_by_id(
    db: Session, owner_id: UUID, server_id: UUID
) -> Optional[VirtualMachine]:
    """
    Вернуть VM если она принадлежит owner_id (проверка через Project.owner_id).
    """
    return (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )


def stop_server(
    db: Session, owner_id: uuid.UUID, server_id: uuid.UUID
) -> Optional[VirtualMachine]:
    """
    Поставить задачу остановки VM и попытаться выполнить её немедленно.
    """
    vm = (
        db.query(VirtualMachine)
        .join(Project, VirtualMachine.project_id == Project.id)
        .filter(VirtualMachine.id == server_id, Project.owner_id == owner_id)
        .first()
    )
    if not vm:
        raise ValueError("VM not found or access denied")

    job = enqueue_job(db, "VM", vm.id, "STOP_VM")
    try:
        run_job_stop_vm(db, vm)
    except Exception:
        logger.exception("stop_server: immediate run_job_stop_vm failed for vm %s", vm.id)

    try:
        db.refresh(vm)
    except Exception:
        logger.exception("stop_server: refresh failed for vm %s", vm.id)
    return vm