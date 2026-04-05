from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'ip_address')
    search_fields = ('action', 'user__username')
    readonly_fields = ('timestamp', 'user', 'action', 'details', 'ip_address')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False
