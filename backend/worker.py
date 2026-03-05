# backend/worker.py
import time
import signal
import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models.db import SessionLocal
from backend.models.orchestrator import Job
from backend.models.compute import VirtualMachine
from backend.services.orchestrator import (
    list_pending_jobs,
    get_job,
    run_job_create_vm,
    run_job_delete_vm,
    retry_failed_job,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

# Параметры worker-а
POLL_INTERVAL_SECONDS = 5
MAX_RETRY_ATTEMPTS = 5
RETRY_BASE_SECONDS = 5  # базовый интервал для экспоненциального бэкоффа

_shutdown = False


def handle_signal(signum, frame):
    global _shutdown
    logger.info("Received signal %s, shutting down worker...", signum)
    _shutdown = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def compute_backoff(attempt: int) -> int:
    """
    Экспоненциальный бэкофф: base * 2^(attempt-1)
    attempt начинается с 1.
    """
    return RETRY_BASE_SECONDS * (2 ** (max(0, attempt - 1)))


def process_job(db: Session, job: Job):
    """
    Выполнить одну задачу в зависимости от action.
    Логика:
      - если CREATE_VM: найти VM и вызвать run_job_create_vm
      - если DELETE_VM: найти VM и вызвать run_job_delete_vm
      - иначе: логировать и пометить FAILED
    """
    logger.info("Processing job %s action=%s status=%s", job.id, job.action, job.status)
    try:
        if job.action == "CREATE_VM":
            vm = db.query(VirtualMachine).filter(VirtualMachine.id == job.resource_id).first()
            if not vm:
                logger.warning("VM %s not found for job %s; marking job FAILED", job.resource_id, job.id)
                job.status = "FAILED"
                job.error_message = "VM not found"
                db.add(job); db.commit()
                return
            run_job_create_vm(db, vm)

        elif job.action == "DELETE_VM":
            vm = db.query(VirtualMachine).filter(VirtualMachine.id == job.resource_id).first()
            if not vm:
                # Если VM уже удалена, считаем задачу успешной
                logger.info("VM %s not found for delete job %s — marking SUCCESS", job.resource_id, job.id)
                job.status = "SUCCESS"
                db.add(job); db.commit()
                return
            run_job_delete_vm(db, vm)

        else:
            logger.warning("Unknown job action %s for job %s", job.action, job.id)
            job.status = "FAILED"
            job.error_message = f"Unknown action {job.action}"
            db.add(job); db.commit()

    except Exception as e:
        logger.exception("Unhandled exception while processing job %s: %s", job.id, e)
        # Помечаем задачу как FAILED, но не удаляем — worker может повторить позже
        try:
            job.status = "FAILED"
            job.error_message = str(e)
            db.add(job); db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to mark job %s as FAILED", job.id)


def main_loop():
    logger.info("Worker started, polling every %s seconds", POLL_INTERVAL_SECONDS)
    db: Optional[Session] = None

    while not _shutdown:
        try:
            db = SessionLocal()
            # Берём задачи, которые PENDING или FAILED (для повторных попыток)
            jobs = db.query(Job).filter(Job.status.in_(["PENDING", "FAILED"])).all()

            if not jobs:
                # нет задач — ждём
                db.close()
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            for job in jobs:
                if _shutdown:
                    break

                # Если задача FAILED — проверяем количество попыток и время последней попытки
                if job.status == "FAILED":
                    # используем поля started_at/finished_at как ориентир; если их нет, пробуем retry
                    # Для простоты: считаем, что job имеет поле error_message и started_at; если попыток нет, пробуем
                    attempts = 0
                    # попытки можно хранить в error_message или в отдельном поле; здесь простая эвристика:
                    # если в error_message есть "attempts=N" — извлечь, иначе считать 0.
                    if job.error_message and "attempts=" in (job.error_message or ""):
                        try:
                            # ожидаем формат "... attempts=N"
                            part = job.error_message.split("attempts=")[-1]
                            attempts = int(part.split()[0])
                        except Exception:
                            attempts = 0

                    if attempts >= MAX_RETRY_ATTEMPTS:
                        logger.warning("Job %s reached max retry attempts (%s); skipping", job.id, attempts)
                        continue

                    # вычисляем задержку
                    backoff = compute_backoff(attempts + 1)
                    # если finished_at есть и прошло меньше backoff секунд — пропускаем
                    if job.finished_at:
                        next_try = job.finished_at + timedelta(seconds=backoff)
                        if datetime.utcnow() < next_try:
                            logger.debug("Job %s will be retried at %s (backoff %s s)", job.id, next_try, backoff)
                            continue

                    # обновляем error_message, увеличивая attempts
                    job.error_message = (job.error_message or "") + f" attempts={attempts+1}"
                    db.add(job); db.commit()

                # Обрабатываем задачу
                process_job(db, job)

            db.close()
            time.sleep(POLL_INTERVAL_SECONDS)

        except Exception as e:
            logger.exception("Worker loop error: %s", e)
            if db:
                try:
                    db.close()
                except Exception:
                    pass
            # при ошибке ждём немного дольше
            time.sleep(POLL_INTERVAL_SECONDS * 2)

    logger.info("Worker shutting down gracefully.")


if __name__ == "__main__":
    main_loop()
