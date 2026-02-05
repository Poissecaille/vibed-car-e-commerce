"""Admin configuration for inventory models."""
from django.contrib import admin

from .models import InventoryItem, InventoryLog


class InventoryLogInline(admin.TabularInline):
    """Inline admin for inventory logs."""
    model = InventoryLog
    extra = 0
    readonly_fields = ['previous_status', 'new_status', 'changed_by', 'reason', 'timestamp']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    """Admin interface for InventoryItem model."""

    list_display = [
        'vehicle', 'status', 'quantity', 'location',
        'reserved_by', 'reserved_until', 'updated_at'
    ]
    list_filter = ['status', 'location']
    search_fields = ['vehicle__title', 'vehicle__brand', 'vehicle__model', 'notes']
    raw_id_fields = ['vehicle', 'reserved_by']
    readonly_fields = ['updated_at', 'created_at']

    fieldsets = (
        ('Véhicule', {
            'fields': ('vehicle',)
        }),
        ('Stock', {
            'fields': ('quantity', 'location', 'status', 'notes')
        }),
        ('Réservation', {
            'fields': ('reserved_by', 'reserved_until')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [InventoryLogInline]


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    """Admin interface for InventoryLog model."""

    list_display = [
        'inventory_item', 'previous_status', 'new_status',
        'changed_by', 'reason', 'timestamp'
    ]
    list_filter = ['previous_status', 'new_status', 'timestamp']
    search_fields = ['inventory_item__vehicle__title', 'reason']
    raw_id_fields = ['inventory_item', 'changed_by']
    readonly_fields = [
        'inventory_item', 'previous_status', 'new_status',
        'changed_by', 'reason', 'timestamp'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
