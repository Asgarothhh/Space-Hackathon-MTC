import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.orchestrator import Job
from backend.models.compute import VirtualMachine

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
        return None
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
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


def run_job_create_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    """
    Безопасный старт/создание контейнера для VM (вариант A).
    - Если vm.docker_container_id задан, пытаемся найти контейнер и запустить его.
    - Если контейнера нет или старт не удался — очищаем docker_container_id и создаём новый контейнер.
    - При отсутствии Docker оставляем задачу в PENDING.
    """
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
        # Если уже есть docker_container_id — попробуем использовать существующий контейнер
        if vm.docker_container_id:
            try:
                container = client.containers.get(vm.docker_container_id)
                # Попытаться запустить, если контейнер не запущен
                if getattr(container, "status", None) != "running":
                    try:
                        container.start()
                    except Exception:
                        # Если не удалось стартовать — пересоздадим ниже
                        raise
                vm.status = "RUNNING"
                db.add(vm)
                _mark_job_success(db, job)
                db.add(job)
                db.commit()
                db.refresh(vm)
                return job
            except DockerNotFound:
                # контейнера нет — очистим поле и продолжим создание нового
                vm.docker_container_id = None
                try:
                    db.add(vm)
                    db.commit()
                except Exception:
                    db.rollback()
            except Exception as e:
                # Не удалось стартовать существующий контейнер — очистим поле и продолжим создание нового
                logger.exception("Error while starting existing container %s for vm %s: %s", vm.docker_container_id, vm.id, e)
                vm.docker_container_id = None
                try:
                    db.add(vm)
                    db.commit()
                except Exception:
                    db.rollback()

        # Создаём новый контейнер
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
        return job
    except Exception as e:
        logger.exception("Error while creating/starting container for VM %s: %s", vm.id, e)
        vm.status = "ERROR"
        try:
            db.add(vm)
            db.commit()
        except Exception:
            db.rollback()
        _mark_job_failed(db, job, str(e))
        return job


def run_job_delete_vm(db: Session, vm: VirtualMachine) -> Optional[Job]:
    """
    Удаление контейнера и записи VM.
    - Если Docker недоступен — задача остаётся в PENDING.
    - Ошибки при удалении контейнера логируются, но не блокируют удаление записи VM.
    """
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
                    # логируем, но не прерываем удаление записи VM
                    logger.exception("Error removing container %s for VM %s", vm.docker_container_id, vm.id)
            except DockerNotFound:
                # контейнер уже отсутствует — продолжаем
                pass
            except Exception:
                # любые другие ошибки с Docker не должны блокировать удаление записи
                logger.exception("Unexpected docker error while removing container %s for VM %s", vm.docker_container_id, vm.id)

        # Удаляем запись VM из БД
        try:
            db.delete(vm)
            db.commit()
            _mark_job_success(db, job)
            return job
        except Exception as e:
            db.rollback()
            _mark_job_failed(db, job, f"DB delete error: {e}")
            return job
    except Exception as e:
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
    except Exception:
        db.rollback()
        logger.exception("Failed to retry job %s", job.id)

def run_job_create_project(db: Session, project) -> Optional[Job]:
    """
    Создаёт/обрабатывает задачу PROJECT_CREATE.
    Если есть внешние шаги (provisioning, уведомления) — выполняет их здесь.
    Если внешние сервисы недоступны — оставляет задачу в PENDING для worker'а.
    """
    job = enqueue_job(db, "PROJECT", project.id, "PROJECT_CREATE")
    try:
        # Пример синхронной работы: логирование, аудит, подготовка метаданных.
        # Здесь можно вызывать внешние API, создавать записи в других сервисах и т.д.
        # Если всё прошло успешно — помечаем задачу SUCCESS.
        logger.info("run_job_create_project: performing post-create actions for project %s", project.id)

        # (placeholders for real actions)
        # do_provision_network(db, project)
        # notify_team(project)

        _mark_job_success(db, job)
        return job
    except Exception as e:
        logger.exception("run_job_create_project failed for project %s: %s", project.id, e)
        _mark_job_failed(db, job, str(e))
        return job
