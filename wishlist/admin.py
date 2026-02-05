"""Admin configuration for wishlist models."""
from django.contrib import admin

from .models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    """Inline admin for wishlist items."""
    model = WishlistItem
    extra = 0
    raw_id_fields = ['vehicle']
    readonly_fields = ['added_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Admin interface for Wishlist model."""

    list_display = ['user', 'items_count', 'created_at', 'updated_at']
    search_fields = ['user__email']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WishlistItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    """Admin interface for WishlistItem model."""

    list_display = ['wishlist', 'vehicle', 'added_at']
    list_filter = ['added_at']
    search_fields = ['wishlist__user__email', 'vehicle__title']
    raw_id_fields = ['wishlist', 'vehicle']
    readonly_fields = ['added_at']
