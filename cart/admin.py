"""Admin configuration for cart models."""
from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline admin for cart items."""
    model = CartItem
    extra = 0
    raw_id_fields = ['vehicle']
    readonly_fields = ['price_snapshot', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model."""

    list_display = [
        'user', 'status', 'items_count', 'total_amount',
        'created_at', 'expires_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'converted_to_order']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'items_count', 'total_amount']
    inlines = [CartItemInline]

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Statut', {
            'fields': ('status', 'expires_at', 'converted_to_order')
        }),
        ('Résumé', {
            'fields': ('items_count', 'total_amount'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Suppression', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Include soft-deleted carts in admin."""
        return Cart.all_objects.all()


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model."""

    list_display = ['cart', 'vehicle', 'price_snapshot', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__email', 'vehicle__title']
    raw_id_fields = ['cart', 'vehicle']
    readonly_fields = ['price_snapshot', 'added_at']
