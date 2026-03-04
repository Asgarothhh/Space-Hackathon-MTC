from django.db import models
import uuid

class VirtualMachine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    project_id = models.UUIDField()
    cpu = models.IntegerField()
    ram = models.IntegerField()
    status = models.CharField(max_length=20)
    docker_container_id = models.CharField(max_length=255, null=True, blank=True)
    host_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compute_service.virtual_machines'
