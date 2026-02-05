"""Business logic services for wishlist."""
from django.db import IntegrityError

from vehicles.models import Vehicle

from .models import Wishlist, WishlistItem


class WishlistService:
    """Service for wishlist operations."""

    @staticmethod
    def get_or_create_wishlist(user) -> Wishlist:
        """Get or create a wishlist for a user."""
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        return wishlist

    @staticmethod
    def get_wishlist_items(user) -> list[WishlistItem]:
        """Get all items in user's wishlist."""
        wishlist = WishlistService.get_or_create_wishlist(user)
        return wishlist.items.select_related('vehicle').all()

    @staticmethod
    def add_to_wishlist(user, vehicle_id: str, notes: str = "") -> tuple[WishlistItem | None, str]:
        """Add a vehicle to user's wishlist."""
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, is_active=True)
        except Vehicle.DoesNotExist:
            return None, "Véhicule non trouvé"

        wishlist = WishlistService.get_or_create_wishlist(user)

        try:
            item = WishlistItem.objects.create(
                wishlist=wishlist,
                vehicle=vehicle,
                notes=notes
            )
            return item, "Véhicule ajouté à la liste de souhaits"
        except IntegrityError:
            return None, "Ce véhicule est déjà dans votre liste de souhaits"

    @staticmethod
    def remove_from_wishlist(user, item_id: int) -> tuple[bool, str]:
        """Remove an item from user's wishlist."""
        wishlist = WishlistService.get_or_create_wishlist(user)
        try:
            item = WishlistItem.objects.get(id=item_id, wishlist=wishlist)
            item.delete()
            return True, "Véhicule retiré de la liste de souhaits"
        except WishlistItem.DoesNotExist:
            return False, "Article non trouvé"

    @staticmethod
    def remove_vehicle_from_wishlist(user, vehicle_id: str) -> tuple[bool, str]:
        """Remove a vehicle from user's wishlist by vehicle ID."""
        wishlist = WishlistService.get_or_create_wishlist(user)
        try:
            item = WishlistItem.objects.get(wishlist=wishlist, vehicle_id=vehicle_id)
            item.delete()
            return True, "Véhicule retiré de la liste de souhaits"
        except WishlistItem.DoesNotExist:
            return False, "Véhicule non trouvé dans la liste de souhaits"

    @staticmethod
    def is_in_wishlist(user, vehicle_id: str) -> bool:
        """Check if a vehicle is in user's wishlist."""
        wishlist = WishlistService.get_or_create_wishlist(user)
        return WishlistItem.objects.filter(wishlist=wishlist, vehicle_id=vehicle_id).exists()

    @staticmethod
    def clear_wishlist(user) -> int:
        """Clear all items from user's wishlist."""
        wishlist = WishlistService.get_or_create_wishlist(user)
        count = wishlist.items.count()
        wishlist.items.all().delete()
        return count

    @staticmethod
    def update_notes(user, item_id: int, notes: str) -> tuple[WishlistItem | None, str]:
        """Update notes for a wishlist item."""
        wishlist = WishlistService.get_or_create_wishlist(user)
        try:
            item = WishlistItem.objects.get(id=item_id, wishlist=wishlist)
            item.notes = notes
            item.save(update_fields=['notes'])
            return item, "Notes mises à jour"
        except WishlistItem.DoesNotExist:
            return None, "Article non trouvé"
