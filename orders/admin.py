"""Admin configuration for order models."""
from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items."""
    model = OrderItem
    extra = 0
    raw_id_fields = ['vehicle']
    readonly_fields = ['price_snapshot', 'vehicle_snapshot']


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin for order status history."""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['previous_status', 'new_status', 'changed_by', 'reason', 'timestamp']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""

    list_display = [
        'order_number', 'user', 'status', 'total_amount',
        'currency', 'items_count', 'created_at', 'paid_at'
    ]
    list_filter = ['status', 'currency', 'created_at', 'paid_at']
    search_fields = ['order_number', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = [
        'order_number', 'subtotal', 'tax_amount', 'total_amount',
        'created_at', 'updated_at', 'confirmed_at', 'paid_at',
        'shipped_at', 'delivered_at', 'cancelled_at', 'deleted_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Commande', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Montants', {
            'fields': (
                ('subtotal', 'tax_rate', 'tax_amount'),
                ('total_amount', 'currency')
            )
        }),
        ('Adresses', {
            'fields': ('shipping_address', 'billing_address'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': (
                'created_at', 'confirmed_at', 'paid_at',
                'shipped_at', 'delivered_at', 'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
        ('Suppression', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [OrderItemInline, OrderStatusHistoryInline]

    def get_queryset(self, request):
        """Include soft-deleted orders in admin."""
        return Order.all_objects.all()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model."""

    list_display = ['order', 'vehicle', 'price_snapshot']
    search_fields = ['order__order_number', 'vehicle__title']
    raw_id_fields = ['order', 'vehicle']
    readonly_fields = ['price_snapshot', 'vehicle_snapshot']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for OrderStatusHistory model."""

    list_display = ['order', 'previous_status', 'new_status', 'changed_by', 'timestamp']
    list_filter = ['previous_status', 'new_status', 'timestamp']
    search_fields = ['order__order_number']
    raw_id_fields = ['order', 'changed_by']
    readonly_fields = ['order', 'previous_status', 'new_status', 'changed_by', 'reason', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
