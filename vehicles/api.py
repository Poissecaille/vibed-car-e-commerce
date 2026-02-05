"""API endpoints for vehicles."""
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja_jwt.authentication import JWTAuth

from .models import Vehicle, VehicleMedia
from .schemas import (
    VehicleCreateSchema,
    VehicleDetailSchema,
    VehicleFilterSchema,
    VehicleHistoryCreateSchema,
    VehicleHistorySchema,
    VehicleListSchema,
    VehicleMediaCreateSchema,
    VehicleMediaSchema,
    VehicleSchema,
    VehicleSpecificationCreateSchema,
    VehicleSpecificationSchema,
    VehicleUpdateSchema,
)
from .services import (
    VehicleHistoryService,
    VehicleMediaService,
    VehicleService,
    VehicleSpecificationService,
)

router = Router()


# Public endpoints (no auth required)
@router.get("/", response=VehicleListSchema, auth=None)
def list_vehicles(
    request,
    filters: VehicleFilterSchema = Query(...),
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    ordering: str = "-created_at"
):
    """List all active vehicles with filtering and pagination."""
    result = VehicleService.list_vehicles(
        filters=filters,
        search=search,
        page=page,
        page_size=min(page_size, 100),  # Max 100 per page
        ordering=ordering
    )
    return result


@router.get("/featured", response=list[VehicleSchema], auth=None)
def get_featured_vehicles(request, limit: int = 10):
    """Get featured vehicles."""
    return VehicleService.get_featured_vehicles(limit=min(limit, 20))


@router.get("/slug/{slug}", response=VehicleDetailSchema, auth=None)
def get_vehicle_by_slug(request, slug: str):
    """Get a vehicle by its slug."""
    vehicle = VehicleService.get_vehicle_by_slug(slug)
    if not vehicle:
        return router.create_response(request, {"detail": "Véhicule non trouvé"}, status=404)
    VehicleService.increment_view_count(vehicle)
    return _build_vehicle_detail(vehicle)


@router.get("/{vehicle_id}", response=VehicleDetailSchema, auth=None)
def get_vehicle(request, vehicle_id: UUID):
    """Get a vehicle by ID."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    VehicleService.increment_view_count(vehicle)
    return _build_vehicle_detail(vehicle)


@router.get("/{vehicle_id}/similar", response=list[VehicleSchema], auth=None)
def get_similar_vehicles(request, vehicle_id: UUID, limit: int = 5):
    """Get vehicles similar to the specified one."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    return VehicleService.get_similar_vehicles(vehicle, limit=min(limit, 10))


# Admin endpoints (auth required)
@router.post("/", response={201: VehicleSchema}, auth=JWTAuth())
def create_vehicle(request, data: VehicleCreateSchema):
    """Create a new vehicle (admin/seller only)."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = VehicleService.create_vehicle(data, actor=request.auth, request=request)
    return 201, vehicle


@router.patch("/{vehicle_id}", response=VehicleSchema, auth=JWTAuth())
def update_vehicle(request, vehicle_id: UUID, data: VehicleUpdateSchema):
    """Update a vehicle (admin/seller only)."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = get_object_or_404(Vehicle.all_objects, id=vehicle_id)
    vehicle = VehicleService.update_vehicle(vehicle, data, actor=request.auth, request=request)
    return vehicle


@router.delete("/{vehicle_id}", response={204: None}, auth=JWTAuth())
def delete_vehicle(request, vehicle_id: UUID):
    """Delete a vehicle (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = get_object_or_404(Vehicle.all_objects, id=vehicle_id)
    VehicleService.delete_vehicle(vehicle, actor=request.auth, request=request)
    return 204, None


# Media endpoints
@router.post("/{vehicle_id}/media", response={201: VehicleMediaSchema}, auth=JWTAuth())
def add_vehicle_media(request, vehicle_id: UUID, data: VehicleMediaCreateSchema):
    """Add media to a vehicle."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    media = VehicleMediaService.add_media(vehicle, data, actor=request.auth, request=request)
    return 201, media


@router.delete("/{vehicle_id}/media/{media_id}", response={204: None}, auth=JWTAuth())
def delete_vehicle_media(request, vehicle_id: UUID, media_id: int):
    """Delete vehicle media."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    media = get_object_or_404(VehicleMedia, id=media_id, vehicle_id=vehicle_id)
    VehicleMediaService.delete_media(media)
    return 204, None


# Specification endpoints
@router.post("/{vehicle_id}/specifications", response={201: VehicleSpecificationSchema}, auth=JWTAuth())
def add_vehicle_specification(request, vehicle_id: UUID, data: VehicleSpecificationCreateSchema):
    """Add a specification to a vehicle."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    spec = VehicleSpecificationService.add_specification(vehicle, data)
    return 201, spec


@router.delete("/{vehicle_id}/specifications/{key}", response={204: None}, auth=JWTAuth())
def delete_vehicle_specification(request, vehicle_id: UUID, key: str):
    """Delete a vehicle specification."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    VehicleSpecificationService.remove_specification(vehicle, key)
    return 204, None


# History endpoint
@router.put("/{vehicle_id}/history", response=VehicleHistorySchema, auth=JWTAuth())
def update_vehicle_history(request, vehicle_id: UUID, data: VehicleHistoryCreateSchema):
    """Update vehicle history."""
    if not (request.auth.is_admin() or request.auth.is_seller()):
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    history = VehicleHistoryService.create_or_update_history(
        vehicle, data, actor=request.auth, request=request
    )
    return history


def _build_vehicle_detail(vehicle: Vehicle) -> VehicleDetailSchema:
    """Build a detailed vehicle response."""
    return VehicleDetailSchema(
        id=vehicle.id,
        title=vehicle.title,
        slug=vehicle.slug,
        description=vehicle.description,
        category=vehicle.category,
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        mileage=vehicle.mileage,
        fuel_type=vehicle.fuel_type,
        transmission=vehicle.transmission,
        power_hp=vehicle.power_hp,
        power_kw=vehicle.power_kw,
        color=vehicle.color,
        interior_color=vehicle.interior_color,
        doors=vehicle.doors,
        seats=vehicle.seats,
        condition=vehicle.condition,
        vin=vehicle.vin,
        registration_number=vehicle.registration_number,
        first_registration_date=vehicle.first_registration_date,
        price=vehicle.price,
        currency=vehicle.currency,
        price_negotiable=vehicle.price_negotiable,
        is_active=vehicle.is_active,
        is_featured=vehicle.is_featured,
        view_count=vehicle.view_count,
        meta_description=vehicle.meta_description,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
        primary_image=vehicle.primary_image,
        media=list(vehicle.media.all()),
        specifications=list(vehicle.specifications.all()),
        history=vehicle.history if hasattr(vehicle, 'history') else None,
    )
