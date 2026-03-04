from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "resource_type", "action", "status")  # ← БЕЗ created
    list_filter = ("resource_type", "action", "status")
    search_fields = ("id",)
