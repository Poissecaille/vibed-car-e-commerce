"""Cart models."""
from decimal import Decimal

from django.db import models

from core.models import BaseModel


class CartStatus(models.TextChoices):
    """Cart status enumeration."""
    ACTIVE = 'ACTIVE', 'Actif'
    CONVERTED = 'CONVERTED', 'Converti en commande'
    ABANDONED = 'ABANDONED', 'Abandonné'
    EXPIRED = 'EXPIRED', 'Expiré'


class Cart(BaseModel):
    """Shopping cart for a user."""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='carts'
    )
    status = models.CharField(
        max_length=20,
        choices=CartStatus.choices,
        default=CartStatus.ACTIVE,
        db_index=True
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    converted_to_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_cart'
    )

    class Meta:
        db_table = 'carts'
        verbose_name = 'Panier'
        verbose_name_plural = 'Paniers'
        ordering = ['-created_at']

    def __str__(self):
        return f"Panier de {self.user.email} ({self.status})"

    @property
    def items_count(self) -> int:
        """Get the number of items in the cart."""
        return self.items.count()

    @property
    def total_amount(self) -> Decimal:
        """Calculate the total amount of the cart."""
        return sum(item.price_snapshot for item in self.items.all())

    @property
    def is_active(self) -> bool:
        """Check if the cart is active."""
        return self.status == CartStatus.ACTIVE


class CartItem(models.Model):
    """Item in a cart."""

    id = models.BigAutoField(primary_key=True)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Prix au moment de l'ajout au panier"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Article panier'
        verbose_name_plural = 'Articles panier'
        unique_together = ['cart', 'vehicle']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.cart.user.email} - {self.vehicle.title}"

    def save(self, *args, **kwargs):
        # Capture price at the time of adding to cart
        if not self.price_snapshot:
            self.price_snapshot = self.vehicle.price
        super().save(*args, **kwargs)
