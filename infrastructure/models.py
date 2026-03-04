from django.db import models
import uuid

class Host(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    total_cpu = models.IntegerField()
    total_ram = models.IntegerField()
    total_disk = models.BigIntegerField()
    labels = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'infrastructure.hosts'

class HostSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    used_cpu = models.FloatField()
    used_ram = models.IntegerField()
    used_disk = models.BigIntegerField()

    class Meta:
        db_table = 'infrastructure.host_snapshots'
