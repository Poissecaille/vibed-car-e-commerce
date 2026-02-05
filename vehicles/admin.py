"""Admin configuration for vehicle models."""
from django.contrib import admin

from .models import Vehicle, VehicleHistory, VehicleMedia, VehicleSpecification


class VehicleMediaInline(admin.TabularInline):
    """Inline admin for vehicle media."""
    model = VehicleMedia
    extra = 1
    fields = ['media_type', 'url', 'alt_text', 'is_primary', 'sort_order']


class VehicleSpecificationInline(admin.TabularInline):
    """Inline admin for vehicle specifications."""
    model = VehicleSpecification
    extra = 3
    fields = ['key', 'value', 'group']


class VehicleHistoryInline(admin.StackedInline):
    """Inline admin for vehicle history."""
    model = VehicleHistory
    can_delete = False


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin interface for Vehicle model."""

    list_display = [
        'title', 'brand', 'model', 'year', 'price', 'condition',
        'is_active', 'is_featured', 'view_count', 'created_at'
    ]
    list_filter = [
        'category', 'brand', 'fuel_type', 'transmission',
        'condition', 'is_active', 'is_featured', 'created_at'
    ]
    search_fields = ['title', 'brand', 'model', 'vin', 'description']
    prepopulated_fields = {'slug': ('brand', 'model', 'year', 'title')}
    readonly_fields = ['view_count', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Caractéristiques', {
            'fields': (
                ('brand', 'model'),
                ('year', 'mileage'),
                ('fuel_type', 'transmission'),
                ('power_hp', 'power_kw'),
                ('color', 'interior_color'),
                ('doors', 'seats'),
                'condition',
            )
        }),
        ('Identification', {
            'fields': ('vin', 'registration_number', 'first_registration_date')
        }),
        ('Prix', {
            'fields': (('price', 'currency'), 'price_negotiable')
        }),
        ('Statut', {
            'fields': ('is_active', 'is_featured', 'view_count')
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
        ('Suppression', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [VehicleMediaInline, VehicleSpecificationInline, VehicleHistoryInline]

    def get_queryset(self, request):
        """Include soft-deleted vehicles in admin."""
        return Vehicle.all_objects.all()


@admin.register(VehicleMedia)
class VehicleMediaAdmin(admin.ModelAdmin):
    """Admin interface for VehicleMedia model."""

    list_display = ['vehicle', 'media_type', 'is_primary', 'sort_order', 'created_at']
    list_filter = ['media_type', 'is_primary']
    search_fields = ['vehicle__title', 'alt_text']
    raw_id_fields = ['vehicle']


@admin.register(VehicleSpecification)
class VehicleSpecificationAdmin(admin.ModelAdmin):
    """Admin interface for VehicleSpecification model."""

    list_display = ['vehicle', 'key', 'value', 'group']
    list_filter = ['group', 'key']
    search_fields = ['vehicle__title', 'key', 'value']
    raw_id_fields = ['vehicle']


@admin.register(VehicleHistory)
class VehicleHistoryAdmin(admin.ModelAdmin):
    """Admin interface for VehicleHistory model."""

    list_display = [
        'vehicle', 'number_of_previous_owners', 'is_imported',
        'last_inspection_date', 'service_book_available'
    ]
    list_filter = ['is_imported', 'service_book_available']
    search_fields = ['vehicle__title']
    raw_id_fields = ['vehicle']
