from .models import VirtualMachine
from django.db import transaction

def create_vm_record(vm_id, spec, host_id):
    # идемпотентно создать запись
    vm, created = VirtualMachine.objects.get_or_create(
        id=vm_id,
        defaults={
            'name': spec.get('name'),
            'project_id': spec.get('project_id'),
            'cpu': spec.get('cpu'),
            'ram': spec.get('ram'),
            'status': 'CREATING',
            'host_id': host_id
        }
    )
    return vm

def provision_on_host(host, vm_id, spec):
    # Здесь вызывается agent на host.address.
    # Для MVP можно имитировать запуск и вернуть строку container_id.
    # В реале — HTTP запрос к agent и обработка ответа.
    return f"mock-container-{vm_id}"

def update_vm_running(vm_id, container_id):
    VirtualMachine.objects.filter(id=vm_id).update(status='RUNNING', docker_container_id=container_id)
