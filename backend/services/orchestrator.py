# backend/services/orchestrator.py
import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.models.orchestrator import Job
try:
    import docker
    from docker.errors import DockerException, NotFound as DockerNotFound
except Exception:
    docker = None
    DockerException = Exception
    DockerNotFound = Exception

logger = logging.getLogger(__name__)

def get_docker_client():
    if docker is None:
        return None
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        return None

def enqueue_job(db: Session, resource_type: str, resource_id: uuid.UUID, action: str) -> Job:
    job = Job(resource_type=resource_type, resource_id=resource_id, action=action, status="PENDING")
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError:
        db.rollback()
        raise

def _mark_job_failed(db: Session, job: Job, error_message: str):
    job.status = "FAILED"
    job.error_message = error_message
    try:
        db.add(job)
        db.commit()
    except Exception:
        db.rollback()

def _mark_job_success(db: Session, job: Job):
    job.status = "SUCCESS"
    try:
        db.add(job)
        db.commit()
    except Exception:
        db.rollback()

from backend.models.compute import VirtualMachine
from backend.models.projects import Project
from sqlalchemy import func

def release_project_resources(db: Session, project_id: uuid.UUID, cpu: int, ram: int, ssd: int, maybe_unassign_owner: bool = False):
    """
    Уменьшить cpu_used/ram_used/ssd_used у проекта.
    По умолчанию НЕ снимает owner_id/is_allocated (поведение 'keep').
    Если maybe_unassign_owner=True — снимет привязку только при явном требовании.
    """
    try:
        proj = db.query(Project).filter(Project.id == project_id).with_for_update().one_or_none()
        if not proj:
            return
        proj.cpu_used = max(0, (proj.cpu_used or 0) - (cpu or 0))
        proj.ram_used = max(0, (proj.ram_used or 0) - (ram or 0))
        proj.ssd_used = max(0, (proj.ssd_used or 0) - (ssd or 0))
        db.add(proj)
        db.flush()

        if maybe_unassign_owner:
            vm_count = db.query(func.count(VirtualMachine.id)).filter(VirtualMachine.project_id == project_id).scalar() or 0
            if vm_count == 0:
                if proj.is_allocated:
                    proj.owner_id = None
                    proj.is_allocated = False
                    db.add(proj)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("Failed to release resources for project %s", project_id)

def run_job_create_ssh_for_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    """
    Попытаться сформировать ssh_link для VM.
    Логика:
      1) Если есть docker_container_id и docker доступен — инспектируем контейнер (ports / networks).
      2) Если не удалось — используем vm.network_ipv4 / vm.network_ipv6.
      3) Если найден endpoint — сохраняем vm.ssh_link и помечаем job SUCCESS.
      4) Иначе — помечаем job FAILED с понятной ошибкой.
    """
    job = enqueue_job(db, "VM", vm.id, "CREATE_SSH")
    client = get_docker_client()
    try:
        ssh_link = None

        # 1) Попытка через docker container
        if vm.docker_container_id and client is not None:
            try:
                container = client.containers.get(vm.docker_container_id)
                ports = container.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
                binding = ports.get("22/tcp")
                if binding and isinstance(binding, list) and binding:
                    host_ip = binding[0].get("HostIp", "127.0.0.1")
                    host_port = binding[0].get("HostPort")
                    ssh_link = f"ssh root@{host_ip} -p {host_port}"
                else:
                    networks = container.attrs.get("NetworkSettings", {}).get("Networks", {}) or {}
                    if networks:
                        ip = next(iter(networks.values())).get("IPAddress")
                        if ip:
                            ssh_link = f"ssh root@{ip}"
            except DockerNotFound:
                pass
            except Exception:
                logger.exception("Docker inspection failed for container %s (vm %s)", vm.docker_container_id, vm.id)

        # 2) Fallback на сетевые поля VM
        if not ssh_link:
            try:
                db.refresh(vm)
            except Exception:
                logger.exception("Failed to refresh vm %s before SSH creation", vm.id)
            if getattr(vm, "network_ipv4", None):
                ssh_link = f"ssh root@{vm.network_ipv4}"
            elif getattr(vm, "network_ipv6", None):
                ssh_link = f"ssh root@[{vm.network_ipv6}]"

        # 3) Если ничего не найдено — FAIL
        if not ssh_link:
            _mark_job_failed(db, job, "Could not determine SSH endpoint for VM")
            return job

        # 4) Сохранить ssh_link в VM (с блокировкой строки)
        vm_row = db.query(VirtualMachine).filter(VirtualMachine.id == vm.id).with_for_update().first()
        if not vm_row:
            _mark_job_failed(db, job, "VM not found when saving SSH link")
            return job

        vm_row.ssh_link = ssh_link
        db.add(vm_row)
        _mark_job_success(db, job)
        try:
            db.add(job)
            db.commit()
        except Exception:
            db.rollback()
        return job

    except Exception as e:
        logger.exception("run_job_create_ssh_for_vm failed for vm %s: %s", getattr(vm, "id", "<unknown>"), e)
        _mark_job_failed(db, job, str(e))
        return job

def run_job_create_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    job = enqueue_job(db, "VM", vm.id, "CREATE_VM")
    client = get_docker_client()
    if client is None:
        job.error_message = "Docker unavailable; job queued"
        try:
            db.add(job)
            db.commit()
        except Exception:
            db.rollback()
        return job

    try:
        # Если у VM уже есть контейнер — попытаться его запустить/проверить
        if vm.docker_container_id:
            try:
                container = client.containers.get(vm.docker_container_id)
                if getattr(container, "status", None) != "running":
                    try:
                        container.start()
                    except Exception:
                        raise
                vm.status = "RUNNING"
                db.add(vm)
                _mark_job_success(db, job)
                db.add(job)
                db.commit()
                db.refresh(vm)
                # После commit/refresh — попытка сформировать ssh (fallback на network_* будет виден)
                try:
                    run_job_create_ssh_for_vm(db, vm)
                except Exception:
                    logger.exception("Immediate run_job_create_ssh_for_vm failed for vm %s", vm.id)
                return job
            except DockerNotFound:
                vm.docker_container_id = None
                try:
                    db.add(vm)
                    db.commit()
                except Exception:
                    db.rollback()
            except Exception as e:
                logger.exception("Error while starting existing container %s for vm %s: %s", vm.docker_container_id, vm.id, e)
                vm.docker_container_id = None
                try:
                    db.add(vm)
                    db.commit()
                except Exception:
                    db.rollback()

        # Создаём контейнер
        container = client.containers.run(
            "alpine:latest",
            command="sleep 3600",
            detach=True,
            name=f"vm_{vm.id.hex[:12]}",
            labels={"project_id": str(vm.project_id), "vm_id": str(vm.id)}
        )
        vm.docker_container_id = container.id

        # Попытка извлечь сетевую информацию и проброс порта 22
        try:
            ports = container.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
            binding = ports.get("22/tcp")
            if binding and isinstance(binding, list) and binding:
                host_ip = binding[0].get("HostIp", "127.0.0.1")
                host_port = binding[0].get("HostPort")
                vm.ssh_link = f"ssh root@{host_ip} -p {host_port}"
            else:
                networks = container.attrs.get("NetworkSettings", {}).get("Networks", {}) or {}
                if networks:
                    ip = next(iter(networks.values())).get("IPAddress")
                    if ip:
                        vm.ssh_link = f"ssh root@{ip}"
        except Exception:
            logger.exception("Failed to inspect container network for vm %s", vm.id)

        # Сохраняем VM и финализируем статус
        vm.status = "RUNNING"
        db.add(vm)
        _mark_job_success(db, job)
        db.add(job)
        db.commit()
        db.refresh(vm)

        # После commit/refresh — попытка сформировать ssh_link (fallback на network_* будет виден)
        try:
            run_job_create_ssh_for_vm(db, vm)
        except Exception:
            logger.exception("Immediate run_job_create_ssh_for_vm failed for vm %s", vm.id)

        return job
    except Exception as e:
        logger.exception("Error while creating/starting container for VM %s: %s", vm.id, e)
        vm.status = "ERROR"
        try:
            db.add(vm)
            db.commit()
        except Exception:
            db.rollback()
        # Попытка освободить ресурсы проекта (не снимая привязку по умолчанию)
        try:
            release_project_resources(db, vm.project_id, vm.cpu or 0, vm.ram or 0, vm.ssd or 0, maybe_unassign_owner=False)
        except Exception:
            logger.exception("Failed to release project resources after provisioning failure for vm %s", vm.id)
        _mark_job_failed(db, job, str(e))
        return job

def run_job_delete_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    job = enqueue_job(db, "VM", vm.id, "DELETE_VM")
    client = get_docker_client()
    if client is None:
        job.error_message = "Docker unavailable; delete queued"
        try:
            db.add(job)
            db.commit()
        except Exception:
            db.rollback()
        return job

    try:
        if vm.docker_container_id:
            try:
                container = client.containers.get(vm.docker_container_id)
                try:
                    container.remove(force=True)
                except Exception:
                    logger.exception("Error removing container %s for VM %s", vm.docker_container_id, vm.id)
            except DockerNotFound:
                pass
            except Exception:
                logger.exception("Unexpected docker error while removing container %s for VM %s", vm.docker_container_id, vm.id)

        project_id = vm.project_id
        cpu = vm.cpu or 0
        ram = vm.ram or 0
        ssd = vm.ssd or 0

        try:
            db.delete(vm)
            db.commit()
            try:
                release_project_resources(db, project_id, cpu, ram, ssd, maybe_unassign_owner=False)
            except Exception:
                logger.exception("Failed to release project resources after VM deletion %s", vm.id)
            _mark_job_success(db, job)
            return job
        except Exception as e:
            db.rollback()
            _mark_job_failed(db, job, f"DB delete error: {e}")
            return job
    except Exception as e:
        _mark_job_failed(db, job, str(e))
        return job

# Project job handlers (create/start/stop/delete)
def run_job_create_project(db: Session, project) -> Optional[Job]:
    job = enqueue_job(db, "PROJECT", project.id, "PROJECT_CREATE")
    try:
        logger.info("run_job_create_project: performing post-create actions for project %s", project.id)
        _mark_job_success(db, job)
        return job
    except Exception as e:
        logger.exception("run_job_create_project failed for project %s: %s", project.id, e)
        _mark_job_failed(db, job, str(e))
        return job

def run_job_start_project(db: Session, project: Project, job: Optional[Job] = None) -> Optional[Job]:
    if job is None:
        job = enqueue_job(db, "PROJECT", project.id, "START_PROJECT")
    try:
        project.status = "ACTIVE"
        db.add(project)
        db.commit()
        _mark_job_success(db, job)
        return job
    except Exception as e:
        logger.exception("run_job_start_project failed for project %s: %s", project.id, e)
        _mark_job_failed(db, job, str(e))
        return job

def run_job_stop_project(db: Session, project: Project, job: Optional[Job] = None) -> Optional[Job]:
    if job is None:
        job = enqueue_job(db, "PROJECT", project.id, "STOP_PROJECT")
    try:
        project.status = "INACTIVE"
        db.add(project)
        db.commit()
        _mark_job_success(db, job)
        return job
    except Exception as e:
        logger.exception("run_job_stop_project failed for project %s: %s", project.id, e)
        _mark_job_failed(db, job, str(e))
        return job

def run_job_delete_project(db: Session, project: Project, job: Optional[Job] = None) -> Optional[Job]:
    if job is None:
        job = enqueue_job(db, "PROJECT", project.id, "DELETE_PROJECT")
    try:
        db.delete(project)
        db.commit()
        _mark_job_success(db, job)
        return job
    except Exception as e:
        logger.exception("run_job_delete_project failed for project %s: %s", project.id, e)
        _mark_job_failed(db, job, str(e))
        return job


def run_job_stop_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    """
    Остановить VM: если есть docker_container_id — попытаться остановить контейнер,
    затем обновить статус VM на STOPPED и пометить job как SUCCESS.
    Возвращает Job.
    """
    job = enqueue_job(db, "VM", vm.id, "STOP_VM")
    client = get_docker_client()
    if client is None:
        job.error_message = "Docker unavailable; stop queued"
        try:
            db.add(job)
            db.commit()
        except Exception:
            db.rollback()
        return job

    try:
        if vm.docker_container_id:
            try:
                container = client.containers.get(vm.docker_container_id)
                # Попытка корректно остановить контейнер
                try:
                    container.stop(timeout=10)
                except Exception:
                    # если не удалось корректно остановить — принудительно
                    try:
                        container.kill()
                    except Exception:
                        logger.exception("Failed to kill container %s for vm %s", vm.docker_container_id, vm.id)
                # После остановки контейнера можно оставить docker_container_id или очистить — здесь очищаем
                vm.docker_container_id = None
            except DockerNotFound:
                # контейнера нет — просто очистим поле
                vm.docker_container_id = None
            except Exception:
                logger.exception("Unexpected docker error while stopping container %s for VM %s", vm.docker_container_id, vm.id)
                # не прерываем: попробуем всё равно обновить статус VM

        # Обновляем статус VM и сохраняем
        vm.status = "STOPPED"
        db.add(vm)
        _mark_job_success(db, job)
        try:
            db.add(job)
            db.commit()
            db.refresh(vm)
        except Exception:
            db.rollback()
            logger.exception("DB commit failed in run_job_stop_vm for vm %s", vm.id)
            _mark_job_failed(db, job, "DB commit failed after stopping VM")
        return job

    except Exception as e:
        logger.exception("run_job_stop_vm failed for vm %s: %s", getattr(vm, "id", "<unknown>"), e)
        try:
            vm.status = "ERROR"
            db.add(vm)
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
        _mark_job_failed(db, job, str(e))
        return job
