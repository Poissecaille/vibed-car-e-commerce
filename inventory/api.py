"""API endpoints for inventory."""
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from vehicles.models import Vehicle

from .models import InventoryItem
from .schemas import (
    InventoryItemSchema,
    InventoryItemUpdateSchema,
    InventoryLogSchema,
    InventoryStatusUpdateSchema,
)
from .services import InventoryService

router = Router()


@router.get("/{vehicle_id}", response=InventoryItemSchema, auth=None)
def get_inventory(request, vehicle_id: UUID):
    """Get inventory status for a vehicle."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    inventory = InventoryService.get_or_create_inventory(vehicle)
    return _build_inventory_response(inventory)


@router.patch("/{vehicle_id}", response=InventoryItemSchema, auth=JWTAuth())
def update_inventory(request, vehicle_id: UUID, data: InventoryItemUpdateSchema):
    """Update inventory item (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    inventory = InventoryService.get_or_create_inventory(vehicle)

    for field, value in data.dict(exclude_unset=True).items():
        if value is not None and field != 'status':
            setattr(inventory, field, value)

    inventory.save()
    return _build_inventory_response(inventory)


@router.post("/{vehicle_id}/status", response=InventoryItemSchema, auth=JWTAuth())
def update_inventory_status(request, vehicle_id: UUID, data: InventoryStatusUpdateSchema):
    """Update inventory status with logging (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    inventory = InventoryService.get_or_create_inventory(vehicle)

    inventory = InventoryService.update_status(
        inventory,
        data.status,
        actor=request.auth,
        reason=data.reason,
        request=request
    )
    return _build_inventory_response(inventory)


@router.post("/{vehicle_id}/reserve", response=InventoryItemSchema, auth=JWTAuth())
def reserve_vehicle(request, vehicle_id: UUID, duration_hours: int = 24):
    """Reserve a vehicle for the current user."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    inventory = InventoryService.get_or_create_inventory(vehicle)

    success, message = InventoryService.reserve_vehicle(
        inventory,
        request.auth,
        duration_hours=min(duration_hours, 72),  # Max 72 hours
        request=request
    )

    if not success:
        return router.create_response(request, {"detail": message}, status=400)

    # Refresh from DB
    inventory.refresh_from_db()
    return _build_inventory_response(inventory)


@router.post("/{vehicle_id}/release", response=InventoryItemSchema, auth=JWTAuth())
def release_reservation(request, vehicle_id: UUID):
    """Release a vehicle reservation (owner or admin)."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    inventory = get_object_or_404(InventoryItem, vehicle=vehicle)

    # Check permission
    if inventory.reserved_by != request.auth and not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    inventory = InventoryService.release_reservation(
        inventory,
        actor=request.auth,
        reason="Annulé par l'utilisateur",
        request=request
    )
    return _build_inventory_response(inventory)


@router.get("/{vehicle_id}/logs", response=list[InventoryLogSchema], auth=JWTAuth())
def get_inventory_logs(request, vehicle_id: UUID, limit: int = 50):
    """Get inventory change logs (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    inventory = get_object_or_404(InventoryItem, vehicle=vehicle)

    logs = InventoryService.get_inventory_logs(inventory, limit=min(limit, 100))
    return [
        InventoryLogSchema(
            id=log.id,
            vehicle_id=inventory.vehicle_id,
            previous_status=log.previous_status,
            new_status=log.new_status,
            changed_by_id=log.changed_by_id,
            reason=log.reason,
            timestamp=log.timestamp
        )
        for log in logs
    ]


def _build_inventory_response(inventory: InventoryItem) -> InventoryItemSchema:
    """Build inventory response schema."""
    return InventoryItemSchema(
        vehicle_id=inventory.vehicle_id,
        quantity=inventory.quantity,
        location=inventory.location,
        status=inventory.status,
        reserved_by_id=inventory.reserved_by_id,
        reserved_until=inventory.reserved_until,
        notes=inventory.notes,
        is_available=inventory.is_available,
        updated_at=inventory.updated_at
    )
