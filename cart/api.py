"""API endpoints for cart."""
from uuid import UUID

from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .schemas import CartItemCreateSchema, CartItemSchema, CartSchema, MessageSchema
from .services import CartService

router = Router()


@router.get("/", response=CartSchema, auth=JWTAuth())
def get_cart(request):
    """Get current user's active cart."""
    cart = CartService.get_or_create_cart(request.auth)
    items = list(cart.items.select_related('vehicle').all())
    return CartSchema(
        id=cart.id,
        status=cart.status,
        items=[
            CartItemSchema(
                id=item.id,
                vehicle=item.vehicle,
                price_snapshot=item.price_snapshot,
                added_at=item.added_at
            )
            for item in items
        ],
        items_count=len(items),
        total_amount=cart.total_amount,
        created_at=cart.created_at,
        expires_at=cart.expires_at
    )


@router.post("/items", response={201: CartItemSchema, 400: MessageSchema}, auth=JWTAuth())
def add_to_cart(request, data: CartItemCreateSchema):
    """Add a vehicle to cart."""
    item, message = CartService.add_to_cart(request.auth, str(data.vehicle_id))
    if item is None:
        return 400, MessageSchema(message=message)
    return 201, CartItemSchema(
        id=item.id,
        vehicle=item.vehicle,
        price_snapshot=item.price_snapshot,
        added_at=item.added_at
    )


@router.delete("/items/{item_id}", response={200: MessageSchema, 404: MessageSchema}, auth=JWTAuth())
def remove_from_cart(request, item_id: int):
    """Remove an item from cart."""
    success, message = CartService.remove_from_cart(request.auth, item_id)
    if not success:
        return 404, MessageSchema(message=message)
    return MessageSchema(message=message)


@router.delete("/vehicles/{vehicle_id}", response={200: MessageSchema, 404: MessageSchema}, auth=JWTAuth())
def remove_vehicle_from_cart(request, vehicle_id: UUID):
    """Remove a vehicle from cart by vehicle ID."""
    success, message = CartService.remove_vehicle_from_cart(request.auth, str(vehicle_id))
    if not success:
        return 404, MessageSchema(message=message)
    return MessageSchema(message=message)


@router.delete("/", response=MessageSchema, auth=JWTAuth())
def clear_cart(request):
    """Clear all items from cart."""
    count = CartService.clear_cart(request.auth)
    return MessageSchema(message=f"{count} article(s) supprimé(s)")


@router.post("/check-availability", response=dict, auth=JWTAuth())
def check_availability(request):
    """Check availability of all items in cart."""
    cart = CartService.get_active_cart(request.auth)
    if not cart:
        return {"unavailable_items": [], "all_available": True}

    unavailable = CartService.check_items_availability(cart)
    return {
        "unavailable_items": unavailable,
        "all_available": len(unavailable) == 0
    }


@router.post("/refresh-prices", response=dict, auth=JWTAuth())
def refresh_prices(request):
    """Refresh prices for all items in cart."""
    cart = CartService.get_active_cart(request.auth)
    if not cart:
        return {"price_changes": [], "has_changes": False}

    changes = CartService.refresh_prices(cart)
    return {
        "price_changes": changes,
        "has_changes": len(changes) > 0
    }
