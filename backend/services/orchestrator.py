import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Импорты моделей (предполагается, что модели находятся в backend.models)
from backend.models.orchestrator import Job
from backend.models.compute import VirtualMachine

# Импорт docker делаем локально внутри функций, чтобы модуль не падал при отсутствии Docker
try:
    import docker
    from docker.errors import DockerException, NotFound as DockerNotFound
except Exception:
    docker = None
    DockerException = Exception
    DockerNotFound = Exception

logger = logging.getLogger(__name__)


def get_docker_client():
    """
    Попытаться создать docker client и проверить соединение.
    Возвращает docker.DockerClient или None, если Docker недоступен.
    """
    if docker is None:
        logger.debug("docker SDK not installed in environment")
        return None

    try:
        client = docker.from_env()
        # ping проверяет доступность демона
        client.ping()
        return client
    except DockerException as e:
        logger.warning("Docker unavailable: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error while creating docker client: %s", e)
        return None


def enqueue_job(db: Session, resource_type: str, resource_id: uuid.UUID, action: str) -> Job:
    """
    Создаёт запись задачи в таблице orchestrator.jobs со статусом PENDING.
    Возвращает ORM-объект Job.
    """
    job = Job(resource_type=resource_type, resource_id=resource_id, action=action, status="PENDING")
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Enqueued job %s for resource %s action %s", job.id, resource_id, action)
        return job
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("DB error while enqueueing job: %s", e)
        raise


def _mark_job_failed(db: Session, job: Job, error_message: str):
    job.status = "FAILED"
    job.error_message = error_message
    try:
        db.add(job)
        db.commit()
        logger.error("Job %s marked FAILED: %s", job.id, error_message)
    except Exception:
        db.rollback()
        logger.exception("Failed to mark job as FAILED")


def _mark_job_success(db: Session, job: Job):
    job.status = "SUCCESS"
    try:
        db.add(job)
        db.commit()
        logger.info("Job %s marked SUCCESS", job.id)
    except Exception:
        db.rollback()
        logger.exception("Failed to mark job as SUCCESS")


def run_job_create_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    """
    Создаёт задачу CREATE_VM и пытается создать контейнер Docker (mock VM).
    Если Docker недоступен — задача остаётся в PENDING и возвращается объект job.
    При успешном создании контейнера обновляет vm.docker_container_id и vm.status.
    """
    job = enqueue_job(db, "VM", vm.id, "CREATE_VM")

    client = get_docker_client()
    if client is None:
        # Docker недоступен — оставляем задачу в PENDING, добавим пояснение
        job.error_message = "Docker unavailable; job queued"
        try:
            db.add(job)
            db.commit()
            logger.info("Docker unavailable — job %s queued", job.id)
        except Exception:
            db.rollback()
            logger.exception("Failed to update job queued state")
        return job

    try:
        # Пример: запускаем лёгкий контейнер как mock VM
        container = client.containers.run(
            "alpine:latest",
            command="sleep 3600",
            detach=True,
            name=f"vm_{vm.id.hex[:12]}",
            labels={"project_id": str(vm.project_id), "vm_id": str(vm.id)}
        )

        vm.docker_container_id = container.id
        vm.status = "RUNNING"

        db.add(vm)
        _mark_job_success(db, job)
        db.add(job)
        db.commit()
        db.refresh(vm)
        logger.info("VM %s created container %s", vm.id, container.id)
        return job
    except Exception as e:
        # В случае ошибки помечаем задачу как FAILED и VM как ERROR
        logger.exception("Error while creating container for VM %s: %s", vm.id, e)
        vm.status = "ERROR"
        try:
            db.add(vm)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to update VM status to ERROR")
        _mark_job_failed(db, job, str(e))
        return job


def run_job_delete_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    """
    Создаёт задачу DELETE_VM и пытается удалить контейнер Docker и запись VM.
    Если Docker недоступен — задача остаётся в PENDING.
    """
    job = enqueue_job(db, "VM", vm.id, "DELETE_VM")

    client = get_docker_client()
    if client is None:
        job.error_message = "Docker unavailable; delete queued"
        try:
            db.add(job)
            db.commit()
            logger.info("Docker unavailable — delete job %s queued", job.id)
        except Exception:
            db.rollback()
            logger.exception("Failed to update delete job queued state")
        return job

    try:
        if vm.docker_container_id:
            try:
                container = client.containers.get(vm.docker_container_id)
                container.remove(force=True)
                logger.info("Removed container %s for VM %s", vm.docker_container_id, vm.id)
            except DockerNotFound:
                logger.warning("Container %s not found for VM %s; continuing delete", vm.docker_container_id, vm.id)
            except Exception as e:
                logger.exception("Error removing container %s: %s", vm.docker_container_id, e)
                # не прерываем удаление записи VM, но фиксируем ошибку
        # Удаляем запись VM из БД
        try:
            db.delete(vm)
            db.commit()
            _mark_job_success(db, job)
            logger.info("VM %s deleted from DB", vm.id)
            return job
        except Exception as e:
            db.rollback()
            logger.exception("DB error while deleting VM %s: %s", vm.id, e)
            _mark_job_failed(db, job, f"DB delete error: {e}")
            return job
    except Exception as e:
        logger.exception("Unexpected error during delete job for VM %s: %s", vm.id, e)
        _mark_job_failed(db, job, str(e))
        return job


def get_job(db: Session, job_id: uuid.UUID) -> Optional[Job]:
    """Вернуть задачу по id."""
    try:
        return db.query(Job).filter(Job.id == job_id).first()
    except Exception:
        logger.exception("Failed to fetch job %s", job_id)
        return None


def list_pending_jobs(db: Session):
    """Список задач со статусом PENDING (для worker)."""
    try:
        return db.query(Job).filter(Job.status == "PENDING").all()
    except Exception:
        logger.exception("Failed to list pending jobs")
        return []


def retry_failed_job(db: Session, job: Job):
    """
    Пометить FAILED -> PENDING для повторной попытки.
    Используется worker'ом при необходимости.
    """
    try:
        job.status = "PENDING"
        job.error_message = None
        db.add(job)
        db.commit()
        logger.info("Job %s set to PENDING for retry", job.id)
    except Exception:
        db.rollback()
        logger.exception("Failed to retry job %s", job.id)
