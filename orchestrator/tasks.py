from celery import shared_task
from .models import Job
from django.utils import timezone
from infrastructure.scheduler import select_host
from compute_service.services import create_vm_record, provision_on_host, update_vm_running

@shared_task(bind=True)
def run_job(self, job_id):
    job = Job.objects.get(id=job_id)
    job.status = 'RUNNING'
    job.started_at = timezone.now()
    job.attempts += 1
    job.save()
    try:
        if job.action == 'CREATE_VM':
            spec = job.payload
            # 1. проверка квот (реализовать в project_service)
            # 2. выбор host
            host = select_host(spec['cpu'], spec['ram'])
            if not host:
                raise Exception('no capacity')
            # 3. создать запись VM идемпотентно
            create_vm_record(job.resource_id, spec, host['id'])
            # 4. вызвать agent на host
            container_id = provision_on_host(host, job.resource_id, spec)
            # 5. обновить VM
            update_vm_running(job.resource_id, container_id)
        job.status = 'SUCCESS'
    except Exception as e:
        job.status = 'FAILED'
        job.error_message = str(e)
        # TODO: компенсация
    finally:
        job.finished_at = timezone.now()
        job.save()
