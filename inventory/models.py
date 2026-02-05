"""Inventory models for stock management."""
from django.db import models

from core.models import TimestampedModel


class InventoryStatus(models.TextChoices):
    """Inventory status enumeration."""
    AVAILABLE = 'AVAILABLE', 'Disponible'
    RESERVED = 'RESERVED', 'Réservé'
    SOLD = 'SOLD', 'Vendu'
    PENDING_DELIVERY = 'PENDING_DELIVERY', 'En attente de livraison'
    MAINTENANCE = 'MAINTENANCE', 'En maintenance'


class InventoryItem(TimestampedModel):
    """Inventory item linking a vehicle to stock information."""

    vehicle = models.OneToOneField(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='inventory'
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        help_text="Quantité en stock (généralement 1 pour les véhicules)"
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Emplacement physique du véhicule"
    )
    status = models.CharField(
        max_length=20,
        choices=InventoryStatus.choices,
        default=InventoryStatus.AVAILABLE,
        db_index=True
    )
    reserved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reserved_vehicles'
    )
    reserved_until = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_items'
        verbose_name = 'Stock véhicule'
        verbose_name_plural = 'Stocks véhicules'

    def __str__(self):
        return f"{self.vehicle.title} - {self.status}"

    @property
    def is_available(self):
        """Check if the vehicle is available for purchase."""
        return self.status == InventoryStatus.AVAILABLE and self.quantity > 0


class InventoryLog(models.Model):
    """Log of inventory status changes."""

    id = models.BigAutoField(primary_key=True)
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=InventoryStatus.choices
    )
    new_status = models.CharField(
        max_length=20,
        choices=InventoryStatus.choices
    )
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_logs'
        verbose_name = 'Log de stock'
        verbose_name_plural = 'Logs de stock'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.inventory_item.vehicle.title}: {self.previous_status} → {self.new_status}"
