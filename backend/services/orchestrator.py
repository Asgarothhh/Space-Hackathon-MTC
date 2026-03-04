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
from backend.models.compute import VirtualMachine
from backend.models.projects import Project
from sqlalchemy import func

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

def release_project_resources(db: Session, project_id: uuid.UUID, cpu: int, ram: int, ssd: int, maybe_unassign_owner: bool = True):
    """
    Уменьшить cpu_used/ram_used/ssd_used у проекта.
    Если maybe_unassign_owner=True и после уменьшения ресурсы равны нулю и в проекте нет VM — снять owner_id и is_allocated.
    Выполняется в транзакции.
    """
    try:
        proj = db.query(Project).filter(Project.id == project_id).with_for_update().one_or_none()
        if not proj:
            return
        # безопасное уменьшение (не уходим в отрицательные значения)
        proj.cpu_used = max(0, (proj.cpu_used or 0) - (cpu or 0))
        proj.ram_used = max(0, (proj.ram_used or 0) - (ram or 0))
        proj.ssd_used = max(0, (proj.ssd_used or 0) - (ssd or 0))
        db.add(proj)
        db.flush()

        if maybe_unassign_owner:
            # проверить, есть ли ещё VM в проекте
            vm_count = db.query(func.count(VirtualMachine.id)).filter(VirtualMachine.project_id == project_id).scalar() or 0
            if vm_count == 0:
                # если проект пуст и помечен как allocated — освободим
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

        container = client.containers.run(
            "alpine:latest",
            command="sleep 3600",
            detach=True,
            name=f"vm_{vm.id.hex[:12]}",
            labels={"project_id": str(vm.project_id), "vm_id": str(vm.id)}
        )
        vm.docker_container_id = container.id
        # try to extract network info and port binding
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

        vm.status = "RUNNING"
        db.add(vm)
        _mark_job_success(db, job)
        db.add(job)
        db.commit()
        db.refresh(vm)
        return job
    except Exception as e:
        logger.exception("Error while creating/starting container for VM %s: %s", vm.id, e)
        vm.status = "ERROR"
        # Сохраняем статус VM и пытаемся освободить ресурсы проекта
        try:
            # сохраняем vm (если объект привязан)
            db.add(vm)
            db.commit()
        except Exception:
            db.rollback()
        # Попытка освободить ресурсы, возможно проект был только что выделен
        try:
            release_project_resources(db, vm.project_id, vm.cpu or 0, vm.ram or 0, vm.ssd or 0, maybe_unassign_owner=True)
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

        # Сохраним параметры перед удалением, чтобы корректно уменьшить usage
        project_id = vm.project_id
        cpu = vm.cpu or 0
        ram = vm.ram or 0
        ssd = vm.ssd or 0

        try:
            db.delete(vm)
            db.commit()
            # После успешного удаления VM — уменьшить usage и, при необходимости, освободить проект
            try:
                release_project_resources(db, project_id, cpu, ram, ssd, maybe_unassign_owner=True)
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

# Project job handlers (create/start/stop/delete) — оставлены как в вашем файле
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

# run_job_create_ssh_for_project — формирует ssh_link и сохраняет в VM.ssh_link
def run_job_create_ssh_for_project(db: Session, project: Project, job: Optional[Job] = None) -> Optional[Job]:
    if job is None:
        job = enqueue_job(db, "PROJECT", project.id, "CREATE_SSH")
    try:
        client = get_docker_client()
        # 1) gateway VM
        vm = db.query(VirtualMachine).filter(VirtualMachine.project_id == project.id, VirtualMachine.is_gateway == True).first()
        # 2) VM с docker_container_id
        if not vm:
            vm = db.query(VirtualMachine).filter(VirtualMachine.project_id == project.id, VirtualMachine.docker_container_id != None).first()
        # 3) любая VM с IP
        if not vm:
            vm = db.query(VirtualMachine).filter(VirtualMachine.project_id == project.id, (VirtualMachine.network_ipv4 != None) | (VirtualMachine.network_ipv6 != None)).first()

        if not vm:
            _mark_job_failed(db, job, "No VM found to derive SSH link for project")
            return job

        ssh_link = None
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
            except Exception:
                logger.exception("Docker access failed for container %s", vm.docker_container_id)

        if not ssh_link:
            if vm.network_ipv4:
                ssh_link = f"ssh root@{vm.network_ipv4}"
            elif vm.network_ipv6:
                ssh_link = f"ssh root@[{vm.network_ipv6}]"

        if not ssh_link:
            _mark_job_failed(db, job, "Could not determine SSH endpoint from VM")
            return job

        vm_row = db.query(VirtualMachine).filter(VirtualMachine.id == vm.id).with_for_update().first()
        vm_row.ssh_link = ssh_link
        db.add(vm_row)
        _mark_job_success(db, job)
        return job
    except Exception as e:
        logger.exception("run_job_create_ssh_for_project failed for project %s: %s", getattr(project, "id", "<unknown>"), e)
        _mark_job_failed(db, job, str(e))
        return job


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

# --- остальной код (run_job_create_vm, run_job_delete_vm, project jobs, run_job_create_ssh_for_project)
# (оставляем без изменений, но в местах вызова release_project_resources используем maybe_unassign_owner=False)
# Ниже — примеры вызовов в обработчиках (фрагменты):
#
# при провале provisioning:
#     release_project_resources(db, vm.project_id, vm.cpu or 0, vm.ram or 0, vm.ssd or 0, maybe_unassign_owner=False)
#
# при удалении VM (после успешного удаления записи):
#     release_project_resources(db, project_id, cpu, ram, ssd, maybe_unassign_owner=False)
#
# Полный файл должен содержать остальные функции из вашей текущей версии (run_job_create_vm, run_job_delete_vm и т.д.)
