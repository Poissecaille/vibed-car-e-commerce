"""Order models."""
from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import BaseModel


class OrderStatus(models.TextChoices):
    """Order status enumeration."""
    PENDING = 'PENDING', 'En attente'
    CONFIRMED = 'CONFIRMED', 'Confirmée'
    PAID = 'PAID', 'Payée'
    PROCESSING = 'PROCESSING', 'En traitement'
    SHIPPED = 'SHIPPED', 'Expédiée'
    DELIVERED = 'DELIVERED', 'Livrée'
    CANCELLED = 'CANCELLED', 'Annulée'
    REFUNDED = 'REFUNDED', 'Remboursée'


class Order(BaseModel):
    """Order representing a purchase transaction."""

    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True
    )

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')

    # Addresses (stored as snapshot at order time)
    shipping_address = models.JSONField(null=True, blank=True)
    billing_address = models.JSONField(null=True, blank=True)

    # Notes
    customer_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Dates
    confirmed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at', 'status']),
        ]

    def __str__(self):
        return f"Commande {self.order_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        if not self.total_amount:
            self.calculate_totals()
        super().save(*args, **kwargs)

    def _generate_order_number(self) -> str:
        """Generate a unique order number."""
        import uuid
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M')
        unique_part = uuid.uuid4().hex[:6].upper()
        return f"ORD-{timestamp}-{unique_part}"

    def calculate_totals(self):
        """Calculate order totals from items."""
        self.subtotal = sum(item.price_snapshot for item in self.items.all())
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total_amount = self.subtotal + self.tax_amount

    @property
    def items_count(self) -> int:
        """Get the number of items in the order."""
        return self.items.count()


class OrderItem(models.Model):
    """Item in an order."""

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Prix au moment de la commande"
    )
    vehicle_snapshot = models.JSONField(
        help_text="Snapshot des données du véhicule au moment de la commande"
    )

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Article commande'
        verbose_name_plural = 'Articles commande'
        unique_together = ['order', 'vehicle']

    def __str__(self):
        return f"{self.order.order_number} - {self.vehicle.title}"


class OrderStatusHistory(models.Model):
    """History of order status changes."""

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(max_length=20, choices=OrderStatus.choices)
    new_status = models.CharField(max_length=20, choices=OrderStatus.choices)
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_status_history'
        verbose_name = "Historique statut commande"
        verbose_name_plural = "Historiques statuts commandes"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"
