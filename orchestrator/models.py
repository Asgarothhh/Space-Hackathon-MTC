from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_type = models.CharField(max_length=50)
    resource_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='PENDING')
    payload = models.JSONField(default=dict)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  # ← добавили

    class Meta:
        db_table = 'orchestrator.jobs'

