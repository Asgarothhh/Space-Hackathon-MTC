from django.contrib import admin
from .models import Host

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "total_cpu", "total_ram", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address")
