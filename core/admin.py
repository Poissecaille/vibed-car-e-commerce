"""Admin configuration for core models."""
from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs."""

    list_display = ['created_at', 'actor', 'action', 'entity_type', 'entity_id', 'ip_address']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['entity_id', 'actor__email', 'ip_address']
    readonly_fields = [
        'actor', 'action', 'entity_type', 'entity_id',
        'before_state', 'after_state', 'ip_address', 'user_agent',
        'extra_data', 'created_at'
    ]
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
