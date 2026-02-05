"""Business logic services for inventory."""
from django.db import transaction
from django.utils import timezone

from core.services import AuditService

from .models import InventoryItem, InventoryLog, InventoryStatus


class InventoryService:
    """Service for inventory operations."""

    @staticmethod
    def get_or_create_inventory(vehicle) -> InventoryItem:
        """Get or create inventory item for a vehicle."""
        inventory, created = InventoryItem.objects.get_or_create(vehicle=vehicle)
        return inventory

    @staticmethod
    def get_inventory(vehicle_id) -> InventoryItem | None:
        """Get inventory item by vehicle ID."""
        try:
            return InventoryItem.objects.get(vehicle_id=vehicle_id)
        except InventoryItem.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def update_status(
        inventory: InventoryItem,
        new_status: str,
        actor=None,
        reason: str = "",
        request=None
    ) -> InventoryItem:
        """Update inventory status with logging."""
        old_status = inventory.status

        if old_status == new_status:
            return inventory

        # Create log entry
        InventoryLog.objects.create(
            inventory_item=inventory,
            previous_status=old_status,
            new_status=new_status,
            changed_by=actor,
            reason=reason
        )

        # Update status
        inventory.status = new_status

        # Clear reservation if status changes from RESERVED
        if old_status == InventoryStatus.RESERVED and new_status != InventoryStatus.RESERVED:
            inventory.reserved_by = None
            inventory.reserved_until = None

        inventory.save()

        AuditService.log_status_change(
            inventory,
            old_status,
            new_status,
            actor=actor,
            request=request,
            extra_data={'reason': reason}
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def reserve_vehicle(
        inventory: InventoryItem,
        user,
        duration_hours: int = 24,
        actor=None,
        request=None
    ) -> tuple[bool, str]:
        """Reserve a vehicle for a user."""
        if not inventory.is_available:
            return False, "Ce véhicule n'est pas disponible"

        inventory.status = InventoryStatus.RESERVED
        inventory.reserved_by = user
        inventory.reserved_until = timezone.now() + timezone.timedelta(hours=duration_hours)
        inventory.save()

        InventoryLog.objects.create(
            inventory_item=inventory,
            previous_status=InventoryStatus.AVAILABLE,
            new_status=InventoryStatus.RESERVED,
            changed_by=actor or user,
            reason=f"Réservé pour {user.email}"
        )

        return True, "Véhicule réservé avec succès"

    @staticmethod
    @transaction.atomic
    def release_reservation(
        inventory: InventoryItem,
        actor=None,
        reason: str = "Réservation expirée ou annulée",
        request=None
    ) -> InventoryItem:
        """Release a vehicle reservation."""
        if inventory.status != InventoryStatus.RESERVED:
            return inventory

        old_status = inventory.status
        inventory.status = InventoryStatus.AVAILABLE
        inventory.reserved_by = None
        inventory.reserved_until = None
        inventory.save()

        InventoryLog.objects.create(
            inventory_item=inventory,
            previous_status=old_status,
            new_status=InventoryStatus.AVAILABLE,
            changed_by=actor,
            reason=reason
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def mark_as_sold(
        inventory: InventoryItem,
        actor=None,
        request=None
    ) -> InventoryItem:
        """Mark a vehicle as sold."""
        return InventoryService.update_status(
            inventory,
            InventoryStatus.SOLD,
            actor=actor,
            reason="Vendu",
            request=request
        )

    @staticmethod
    def get_available_vehicles():
        """Get all available inventory items."""
        return InventoryItem.objects.filter(
            status=InventoryStatus.AVAILABLE,
            quantity__gt=0
        ).select_related('vehicle')

    @staticmethod
    def check_expired_reservations():
        """Check and release expired reservations."""
        expired = InventoryItem.objects.filter(
            status=InventoryStatus.RESERVED,
            reserved_until__lt=timezone.now()
        )
        count = 0
        for inventory in expired:
            InventoryService.release_reservation(
                inventory,
                reason="Réservation expirée automatiquement"
            )
            count += 1
        return count

    @staticmethod
    def get_inventory_logs(inventory: InventoryItem, limit: int = 50):
        """Get inventory logs for an item."""
        return inventory.logs.all()[:limit]
