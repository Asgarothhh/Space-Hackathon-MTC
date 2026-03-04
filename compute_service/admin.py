from django.contrib import admin
from .models import VirtualMachine

@admin.register(VirtualMachine)
class VMAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "cpu", "ram", "status", "docker_container_id")
    list_filter = ("status",)
    search_fields = ("name", "id")
