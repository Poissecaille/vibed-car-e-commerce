"""Business logic services for cart."""
from django.db import IntegrityError, transaction
from django.utils import timezone

from inventory.models import InventoryItem, InventoryStatus
from vehicles.models import Vehicle

from .models import Cart, CartItem, CartStatus


class CartService:
    """Service for cart operations."""

    @staticmethod
    def get_active_cart(user) -> Cart | None:
        """Get the active cart for a user."""
        return Cart.objects.filter(
            user=user,
            status=CartStatus.ACTIVE,
            is_deleted=False
        ).first()

    @staticmethod
    def get_or_create_cart(user) -> Cart:
        """Get or create an active cart for a user."""
        cart = CartService.get_active_cart(user)
        if not cart:
            # Set cart to expire in 24 hours
            cart = Cart.objects.create(
                user=user,
                status=CartStatus.ACTIVE,
                expires_at=timezone.now() + timezone.timedelta(hours=24)
            )
        return cart

    @staticmethod
    def get_cart_items(user) -> list[CartItem]:
        """Get all items in user's active cart."""
        cart = CartService.get_active_cart(user)
        if not cart:
            return []
        return list(cart.items.select_related('vehicle').all())

    @staticmethod
    @transaction.atomic
    def add_to_cart(user, vehicle_id: str) -> tuple[CartItem | None, str]:
        """Add a vehicle to user's cart."""
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, is_active=True)
        except Vehicle.DoesNotExist:
            return None, "Véhicule non trouvé"

        # Check inventory availability
        try:
            inventory = InventoryItem.objects.get(vehicle=vehicle)
            if not inventory.is_available:
                return None, "Ce véhicule n'est pas disponible"
        except InventoryItem.DoesNotExist:
            pass  # No inventory record means we assume it's available

        cart = CartService.get_or_create_cart(user)

        try:
            item = CartItem.objects.create(
                cart=cart,
                vehicle=vehicle,
                price_snapshot=vehicle.price
            )
            return item, "Véhicule ajouté au panier"
        except IntegrityError:
            return None, "Ce véhicule est déjà dans votre panier"

    @staticmethod
    def remove_from_cart(user, item_id: int) -> tuple[bool, str]:
        """Remove an item from user's cart."""
        cart = CartService.get_active_cart(user)
        if not cart:
            return False, "Panier non trouvé"

        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            return True, "Véhicule retiré du panier"
        except CartItem.DoesNotExist:
            return False, "Article non trouvé"

    @staticmethod
    def remove_vehicle_from_cart(user, vehicle_id: str) -> tuple[bool, str]:
        """Remove a vehicle from user's cart by vehicle ID."""
        cart = CartService.get_active_cart(user)
        if not cart:
            return False, "Panier non trouvé"

        try:
            item = CartItem.objects.get(cart=cart, vehicle_id=vehicle_id)
            item.delete()
            return True, "Véhicule retiré du panier"
        except CartItem.DoesNotExist:
            return False, "Véhicule non trouvé dans le panier"

    @staticmethod
    def clear_cart(user) -> int:
        """Clear all items from user's active cart."""
        cart = CartService.get_active_cart(user)
        if not cart:
            return 0
        count = cart.items.count()
        cart.items.all().delete()
        return count

    @staticmethod
    def mark_as_converted(cart: Cart, order):
        """Mark cart as converted to order."""
        cart.status = CartStatus.CONVERTED
        cart.converted_to_order = order
        cart.save(update_fields=['status', 'converted_to_order', 'updated_at'])

    @staticmethod
    def mark_as_abandoned(cart: Cart):
        """Mark cart as abandoned."""
        cart.status = CartStatus.ABANDONED
        cart.save(update_fields=['status', 'updated_at'])

    @staticmethod
    def check_items_availability(cart: Cart) -> list[dict]:
        """Check availability of all items in cart."""
        unavailable = []
        for item in cart.items.select_related('vehicle').all():
            try:
                inventory = InventoryItem.objects.get(vehicle=item.vehicle)
                if not inventory.is_available:
                    unavailable.append({
                        'item_id': item.id,
                        'vehicle_title': item.vehicle.title,
                        'reason': inventory.get_status_display()
                    })
            except InventoryItem.DoesNotExist:
                pass
        return unavailable

    @staticmethod
    def refresh_prices(cart: Cart) -> list[dict]:
        """Refresh prices for all items in cart and return changes."""
        changes = []
        for item in cart.items.select_related('vehicle').all():
            if item.price_snapshot != item.vehicle.price:
                changes.append({
                    'item_id': item.id,
                    'vehicle_title': item.vehicle.title,
                    'old_price': item.price_snapshot,
                    'new_price': item.vehicle.price
                })
                item.price_snapshot = item.vehicle.price
                item.save(update_fields=['price_snapshot'])
        return changes

    @staticmethod
    def check_expired_carts():
        """Mark expired carts as such."""
        expired = Cart.objects.filter(
            status=CartStatus.ACTIVE,
            expires_at__lt=timezone.now()
        )
        count = expired.update(status=CartStatus.EXPIRED)
        return count
