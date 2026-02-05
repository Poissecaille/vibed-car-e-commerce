"""Admin configuration for user models."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Address, Profile, User


class ProfileInline(admin.StackedInline):
    """Inline admin for user profile."""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profil'


class AddressInline(admin.TabularInline):
    """Inline admin for user addresses."""
    model = Address
    extra = 0
    readonly_fields = ['created_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
        ('Suppression', {'fields': ('is_deleted', 'deleted_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login', 'deleted_at']
    inlines = [ProfileInline, AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin interface for Address model."""

    list_display = ['user', 'label', 'city', 'postal_code', 'is_default_shipping', 'is_default_billing']
    list_filter = ['country', 'is_default_shipping', 'is_default_billing']
    search_fields = ['user__email', 'street', 'city', 'postal_code']
    raw_id_fields = ['user']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for Profile model."""

    list_display = ['user', 'shipping_address', 'billing_address']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'shipping_address', 'billing_address']
