"""API endpoints for orders."""
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .models import Order
from .schemas import (
    MessageSchema,
    OrderCreateSchema,
    OrderDetailSchema,
    OrderSchema,
    OrderStatusHistorySchema,
    OrderStatusUpdateSchema,
)
from .services import OrderService

router = Router()


@router.get("/", response=list[OrderSchema], auth=JWTAuth())
def list_orders(request, status: str | None = None):
    """List current user's orders."""
    orders = OrderService.get_user_orders(request.auth, status=status)
    return [_build_order_response(order) for order in orders]


@router.post("/", response={201: OrderDetailSchema, 400: MessageSchema}, auth=JWTAuth())
def create_order(request, data: OrderCreateSchema):
    """Create an order from the current cart."""
    order, message = OrderService.create_order_from_cart(
        request.auth,
        shipping_address_id=data.shipping_address_id,
        billing_address_id=data.billing_address_id,
        customer_notes=data.customer_notes,
        request=request
    )
    if order is None:
        return 400, MessageSchema(message=message)
    return 201, _build_order_detail_response(order)


@router.get("/{order_id}", response=OrderDetailSchema, auth=JWTAuth())
def get_order(request, order_id: UUID):
    """Get order details."""
    order = OrderService.get_order(order_id, user=request.auth)
    if not order:
        return router.create_response(request, {"detail": "Commande non trouvée"}, status=404)
    return _build_order_detail_response(order)


@router.get("/number/{order_number}", response=OrderDetailSchema, auth=JWTAuth())
def get_order_by_number(request, order_number: str):
    """Get order by order number."""
    order = OrderService.get_order_by_number(order_number, user=request.auth)
    if not order:
        return router.create_response(request, {"detail": "Commande non trouvée"}, status=404)
    return _build_order_detail_response(order)


@router.post("/{order_id}/cancel", response={200: OrderSchema, 400: MessageSchema}, auth=JWTAuth())
def cancel_order(request, order_id: UUID, reason: str = ""):
    """Cancel an order."""
    order = OrderService.get_order(order_id, user=request.auth)
    if not order:
        return router.create_response(request, {"detail": "Commande non trouvée"}, status=404)

    order, message = OrderService.cancel_order(
        order,
        actor=request.auth,
        reason=reason,
        request=request
    )
    if "non autorisée" in message:
        return 400, MessageSchema(message=message)
    return _build_order_response(order)


@router.get("/{order_id}/history", response=list[OrderStatusHistorySchema], auth=JWTAuth())
def get_order_history(request, order_id: UUID):
    """Get order status history."""
    order = OrderService.get_order(order_id, user=request.auth)
    if not order:
        return router.create_response(request, {"detail": "Commande non trouvée"}, status=404)

    history = OrderService.get_order_history(order)
    return [
        OrderStatusHistorySchema(
            id=h.id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            changed_by_email=h.changed_by.email if h.changed_by else None,
            reason=h.reason,
            timestamp=h.timestamp
        )
        for h in history
    ]


# Admin endpoints
@router.get("/admin/all", response=dict, auth=JWTAuth())
def list_all_orders(request, status: str | None = None, page: int = 1, page_size: int = 20):
    """List all orders (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    result = OrderService.get_all_orders(
        status=status,
        page=page,
        page_size=min(page_size, 100)
    )
    return {
        'items': [_build_order_response(o) for o in result['items']],
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
        'pages': result['pages'],
    }


@router.post("/admin/{order_id}/status", response={200: OrderSchema, 400: MessageSchema}, auth=JWTAuth())
def update_order_status(request, order_id: UUID, data: OrderStatusUpdateSchema):
    """Update order status (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    order = get_object_or_404(Order, id=order_id)
    order, message = OrderService.update_status(
        order,
        data.status,
        actor=request.auth,
        reason=data.reason,
        request=request
    )
    if "non autorisée" in message:
        return 400, MessageSchema(message=message)
    return _build_order_response(order)


def _build_order_response(order: Order) -> OrderSchema:
    """Build order response schema."""
    return OrderSchema(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        tax_rate=order.tax_rate,
        total_amount=order.total_amount,
        currency=order.currency,
        items_count=order.items_count,
        created_at=order.created_at,
        confirmed_at=order.confirmed_at,
        paid_at=order.paid_at,
    )


def _build_order_detail_response(order: Order) -> OrderDetailSchema:
    """Build detailed order response schema."""
    from .schemas import OrderItemSchema
    return OrderDetailSchema(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        tax_rate=order.tax_rate,
        total_amount=order.total_amount,
        currency=order.currency,
        items_count=order.items_count,
        created_at=order.created_at,
        confirmed_at=order.confirmed_at,
        paid_at=order.paid_at,
        items=[
            OrderItemSchema(
                id=item.id,
                vehicle=item.vehicle,
                price_snapshot=item.price_snapshot,
            )
            for item in order.items.select_related('vehicle').all()
        ],
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        customer_notes=order.customer_notes,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
    )
