"""Business logic services for vehicles."""
from django.db import transaction
from django.db.models import Q

from core.services import AuditService, model_to_dict

from .models import Vehicle, VehicleHistory, VehicleMedia, VehicleSpecification
from .schemas import (
    VehicleCreateSchema,
    VehicleFilterSchema,
    VehicleHistoryCreateSchema,
    VehicleMediaCreateSchema,
    VehicleSpecificationCreateSchema,
    VehicleUpdateSchema,
)


class VehicleService:
    """Service for vehicle-related operations."""

    @staticmethod
    def list_vehicles(
        filters: VehicleFilterSchema | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        ordering: str = "-created_at"
    ):
        """List vehicles with filtering, search and pagination."""
        queryset = Vehicle.objects.filter(is_active=True)

        # Apply filters
        if filters:
            queryset = filters.filter(queryset)

        # Apply text search
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search) |
                Q(description__icontains=search)
            )

        # Apply ordering
        if ordering:
            queryset = queryset.order_by(ordering)

        # Calculate pagination
        total = queryset.count()
        pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        items = queryset[offset:offset + page_size]

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': pages,
        }

    @staticmethod
    def get_vehicle(vehicle_id) -> Vehicle | None:
        """Get a vehicle by ID."""
        try:
            return Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            return None

    @staticmethod
    def get_vehicle_by_slug(slug: str) -> Vehicle | None:
        """Get a vehicle by slug."""
        try:
            return Vehicle.objects.get(slug=slug, is_active=True)
        except Vehicle.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_vehicle(data: VehicleCreateSchema, actor=None, request=None) -> Vehicle:
        """Create a new vehicle."""
        vehicle = Vehicle.objects.create(**data.dict())
        AuditService.log_create(vehicle, actor=actor, request=request)
        return vehicle

    @staticmethod
    def update_vehicle(
        vehicle: Vehicle,
        data: VehicleUpdateSchema,
        actor=None,
        request=None
    ) -> Vehicle:
        """Update an existing vehicle."""
        before_state = model_to_dict(vehicle)
        update_fields = []

        for field, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(vehicle, field, value)
                update_fields.append(field)

        if update_fields:
            vehicle.save(update_fields=update_fields + ['updated_at'])
            AuditService.log_update(vehicle, before_state, actor=actor, request=request)

        return vehicle

    @staticmethod
    def delete_vehicle(vehicle: Vehicle, actor=None, request=None):
        """Soft delete a vehicle."""
        AuditService.log_delete(vehicle, actor=actor, request=request)
        vehicle.delete()

    @staticmethod
    def increment_view_count(vehicle: Vehicle):
        """Increment the view count for a vehicle."""
        Vehicle.objects.filter(pk=vehicle.pk).update(
            view_count=vehicle.view_count + 1
        )

    @staticmethod
    def get_featured_vehicles(limit: int = 10):
        """Get featured vehicles."""
        return Vehicle.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('-created_at')[:limit]

    @staticmethod
    def get_similar_vehicles(vehicle: Vehicle, limit: int = 5):
        """Get similar vehicles based on category, brand, and price range."""
        price_margin = vehicle.price * 0.2  # 20% margin
        return Vehicle.objects.filter(
            is_active=True,
            category=vehicle.category,
        ).filter(
            Q(brand=vehicle.brand) |
            Q(price__gte=vehicle.price - price_margin, price__lte=vehicle.price + price_margin)
        ).exclude(pk=vehicle.pk).order_by('-created_at')[:limit]


class VehicleMediaService:
    """Service for vehicle media operations."""

    @staticmethod
    def add_media(
        vehicle: Vehicle,
        data: VehicleMediaCreateSchema,
        actor=None,
        request=None
    ) -> VehicleMedia:
        """Add media to a vehicle."""
        media = VehicleMedia.objects.create(vehicle=vehicle, **data.dict())
        return media

    @staticmethod
    def update_media(media: VehicleMedia, data: dict) -> VehicleMedia:
        """Update vehicle media."""
        for field, value in data.items():
            if value is not None:
                setattr(media, field, value)
        media.save()
        return media

    @staticmethod
    def delete_media(media: VehicleMedia):
        """Delete vehicle media."""
        media.delete()

    @staticmethod
    def set_primary_media(media: VehicleMedia):
        """Set a media as primary."""
        media.is_primary = True
        media.save()


class VehicleSpecificationService:
    """Service for vehicle specification operations."""

    @staticmethod
    def add_specification(
        vehicle: Vehicle,
        data: VehicleSpecificationCreateSchema
    ) -> VehicleSpecification:
        """Add a specification to a vehicle."""
        spec, _ = VehicleSpecification.objects.update_or_create(
            vehicle=vehicle,
            key=data.key,
            defaults={'value': data.value, 'group': data.group}
        )
        return spec

    @staticmethod
    def remove_specification(vehicle: Vehicle, key: str):
        """Remove a specification from a vehicle."""
        VehicleSpecification.objects.filter(vehicle=vehicle, key=key).delete()

    @staticmethod
    def bulk_add_specifications(
        vehicle: Vehicle,
        specs: list[VehicleSpecificationCreateSchema]
    ):
        """Add multiple specifications to a vehicle."""
        for spec_data in specs:
            VehicleSpecificationService.add_specification(vehicle, spec_data)


class VehicleHistoryService:
    """Service for vehicle history operations."""

    @staticmethod
    def create_or_update_history(
        vehicle: Vehicle,
        data: VehicleHistoryCreateSchema,
        actor=None,
        request=None
    ) -> VehicleHistory:
        """Create or update vehicle history."""
        history, created = VehicleHistory.objects.update_or_create(
            vehicle=vehicle,
            defaults=data.dict()
        )
        if created:
            AuditService.log_create(history, actor=actor, request=request)
        else:
            AuditService.log_update(history, {}, actor=actor, request=request)
        return history
