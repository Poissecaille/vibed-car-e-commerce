"""Wishlist models."""
from django.db import models

from core.models import TimestampedModel


class Wishlist(TimestampedModel):
    """User's wishlist."""

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='wishlist'
    )

    class Meta:
        db_table = 'wishlists'
        verbose_name = 'Liste de souhaits'
        verbose_name_plural = 'Listes de souhaits'

    def __str__(self):
        return f"Wishlist de {self.user.email}"

    @property
    def items_count(self):
        return self.items.count()


class WishlistItem(models.Model):
    """Item in a wishlist."""

    id = models.BigAutoField(primary_key=True)
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'wishlist_items'
        verbose_name = 'Article wishlist'
        verbose_name_plural = 'Articles wishlist'
        unique_together = ['wishlist', 'vehicle']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.wishlist.user.email} - {self.vehicle.title}"
