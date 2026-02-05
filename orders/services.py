"""Business logic services for orders."""
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from cart.models import Cart
from cart.services import CartService
from core.services import AuditService, model_to_dict
from inventory.models import InventoryItem
from inventory.services import InventoryService
from users.models import Address

from .models import Order, OrderItem, OrderStatus, OrderStatusHistory


class OrderService:
    """Service for order operations."""

    @staticmethod
    def get_user_orders(user, status: str | None = None):
        """Get all orders for a user."""
        queryset = Order.objects.filter(user=user)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

    @staticmethod
    def get_order(order_id, user=None) -> Order | None:
        """Get an order by ID."""
        try:
            order = Order.objects.get(id=order_id)
            if user and order.user != user and not user.is_admin():
                return None
            return order
        except Order.DoesNotExist:
            return None

    @staticmethod
    def get_order_by_number(order_number: str, user=None) -> Order | None:
        """Get an order by order number."""
        try:
            order = Order.objects.get(order_number=order_number)
            if user and order.user != user and not user.is_admin():
                return None
            return order
        except Order.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        user,
        shipping_address_id=None,
        billing_address_id=None,
        customer_notes: str = "",
        request=None
    ) -> tuple[Order | None, str]:
        """Create an order from the user's active cart."""
        cart = CartService.get_active_cart(user)
        if not cart or cart.items_count == 0:
            return None, "Le panier est vide"

        # Check availability
        unavailable = CartService.check_items_availability(cart)
        if unavailable:
            return None, f"Certains véhicules ne sont plus disponibles: {unavailable[0]['vehicle_title']}"

        # Get addresses
        shipping_address = None
        billing_address = None

        if shipping_address_id:
            try:
                addr = Address.objects.get(id=shipping_address_id, user=user)
                shipping_address = {
                    'street': addr.street,
                    'street_complement': addr.street_complement,
                    'city': addr.city,
                    'postal_code': addr.postal_code,
                    'country': addr.country,
                }
            except Address.DoesNotExist:
                return None, "Adresse de livraison non trouvée"

        if billing_address_id:
            try:
                addr = Address.objects.get(id=billing_address_id, user=user)
                billing_address = {
                    'street': addr.street,
                    'street_complement': addr.street_complement,
                    'city': addr.city,
                    'postal_code': addr.postal_code,
                    'country': addr.country,
                }
            except Address.DoesNotExist:
                return None, "Adresse de facturation non trouvée"

        # Calculate totals
        subtotal = cart.total_amount
        tax_rate = Decimal(str(getattr(settings, 'DEFAULT_VAT_RATE', 20.0)))
        tax_amount = subtotal * (tax_rate / 100)
        total_amount = subtotal + tax_amount

        # Create order
        order = Order.objects.create(
            user=user,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=billing_address,
            customer_notes=customer_notes,
        )

        # Create order items
        for cart_item in cart.items.select_related('vehicle').all():
            vehicle = cart_item.vehicle
            OrderItem.objects.create(
                order=order,
                vehicle=vehicle,
                price_snapshot=cart_item.price_snapshot,
                vehicle_snapshot={
                    'title': vehicle.title,
                    'brand': vehicle.brand,
                    'model': vehicle.model,
                    'year': vehicle.year,
                    'vin': vehicle.vin,
                }
            )

            # Reserve the vehicle
            try:
                inventory = InventoryItem.objects.get(vehicle=vehicle)
                InventoryService.reserve_vehicle(inventory, user, duration_hours=48)
            except InventoryItem.DoesNotExist:
                pass

        # Mark cart as converted
        CartService.mark_as_converted(cart, order)

        # Log creation
        AuditService.log_create(order, actor=user, request=request)

        return order, "Commande créée avec succès"

    @staticmethod
    @transaction.atomic
    def update_status(
        order: Order,
        new_status: str,
        actor=None,
        reason: str = "",
        request=None
    ) -> tuple[Order, str]:
        """Update order status with logging."""
        old_status = order.status

        if old_status == new_status:
            return order, "Statut inchangé"

        # Validate status transition
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PAID, OrderStatus.CANCELLED],
            OrderStatus.PAID: [OrderStatus.PROCESSING, OrderStatus.REFUNDED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.REFUNDED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.REFUNDED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: [],
        }

        if new_status not in valid_transitions.get(old_status, []):
            return order, f"Transition de {old_status} vers {new_status} non autorisée"

        # Create history entry
        OrderStatusHistory.objects.create(
            order=order,
            previous_status=old_status,
            new_status=new_status,
            changed_by=actor,
            reason=reason
        )

        # Update order
        order.status = new_status

        # Set relevant timestamps
        now = timezone.now()
        if new_status == OrderStatus.CONFIRMED:
            order.confirmed_at = now
        elif new_status == OrderStatus.PAID:
            order.paid_at = now
            # Mark vehicles as sold
            for item in order.items.all():
                try:
                    inventory = InventoryItem.objects.get(vehicle=item.vehicle)
                    InventoryService.mark_as_sold(inventory, actor=actor)
                except InventoryItem.DoesNotExist:
                    pass
        elif new_status == OrderStatus.SHIPPED:
            order.shipped_at = now
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = now
        elif new_status == OrderStatus.CANCELLED:
            order.cancelled_at = now
            # Release reservations
            for item in order.items.all():
                try:
                    inventory = InventoryItem.objects.get(vehicle=item.vehicle)
                    InventoryService.release_reservation(
                        inventory,
                        actor=actor,
                        reason=f"Commande {order.order_number} annulée"
                    )
                except InventoryItem.DoesNotExist:
                    pass

        order.save()

        AuditService.log_status_change(
            order,
            old_status,
            new_status,
            actor=actor,
            request=request,
            extra_data={'reason': reason}
        )

        return order, f"Statut mis à jour: {new_status}"

    @staticmethod
    def cancel_order(order: Order, actor=None, reason: str = "", request=None):
        """Cancel an order."""
        return OrderService.update_status(
            order,
            OrderStatus.CANCELLED,
            actor=actor,
            reason=reason or "Annulé par l'utilisateur",
            request=request
        )

    @staticmethod
    def get_order_history(order: Order):
        """Get status history for an order."""
        return order.status_history.all()

    @staticmethod
    def get_all_orders(
        status: str | None = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Get all orders (admin)."""
        queryset = Order.objects.all()
        if status:
            queryset = queryset.filter(status=status)

        total = queryset.count()
        pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        return {
            'items': queryset[offset:offset + page_size],
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': pages,
        }
