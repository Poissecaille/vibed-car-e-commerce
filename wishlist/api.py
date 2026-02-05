"""API endpoints for wishlist."""
from uuid import UUID

from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .schemas import (
    MessageSchema,
    WishlistItemCreateSchema,
    WishlistItemSchema,
    WishlistSchema,
)
from .services import WishlistService

router = Router()


@router.get("/", response=WishlistSchema, auth=JWTAuth())
def get_wishlist(request):
    """Get current user's wishlist."""
    items = WishlistService.get_wishlist_items(request.auth)
    return WishlistSchema(
        items=[
            WishlistItemSchema(
                id=item.id,
                vehicle=item.vehicle,
                added_at=item.added_at,
                notes=item.notes
            )
            for item in items
        ],
        items_count=len(items)
    )


@router.post("/items", response={201: WishlistItemSchema, 400: MessageSchema}, auth=JWTAuth())
def add_to_wishlist(request, data: WishlistItemCreateSchema):
    """Add a vehicle to wishlist."""
    item, message = WishlistService.add_to_wishlist(
        request.auth,
        str(data.vehicle_id),
        data.notes
    )
    if item is None:
        return 400, MessageSchema(message=message)
    return 201, WishlistItemSchema(
        id=item.id,
        vehicle=item.vehicle,
        added_at=item.added_at,
        notes=item.notes
    )


@router.delete("/items/{item_id}", response={200: MessageSchema, 404: MessageSchema}, auth=JWTAuth())
def remove_from_wishlist(request, item_id: int):
    """Remove an item from wishlist."""
    success, message = WishlistService.remove_from_wishlist(request.auth, item_id)
    if not success:
        return 404, MessageSchema(message=message)
    return MessageSchema(message=message)


@router.delete("/vehicles/{vehicle_id}", response={200: MessageSchema, 404: MessageSchema}, auth=JWTAuth())
def remove_vehicle_from_wishlist(request, vehicle_id: UUID):
    """Remove a vehicle from wishlist by vehicle ID."""
    success, message = WishlistService.remove_vehicle_from_wishlist(
        request.auth,
        str(vehicle_id)
    )
    if not success:
        return 404, MessageSchema(message=message)
    return MessageSchema(message=message)


@router.get("/check/{vehicle_id}", response=dict, auth=JWTAuth())
def check_in_wishlist(request, vehicle_id: UUID):
    """Check if a vehicle is in the wishlist."""
    is_in_wishlist = WishlistService.is_in_wishlist(request.auth, str(vehicle_id))
    return {"in_wishlist": is_in_wishlist}


@router.delete("/", response=MessageSchema, auth=JWTAuth())
def clear_wishlist(request):
    """Clear all items from wishlist."""
    count = WishlistService.clear_wishlist(request.auth)
    return MessageSchema(message=f"{count} article(s) supprimé(s)")


@router.patch("/items/{item_id}/notes", response={200: WishlistItemSchema, 404: MessageSchema}, auth=JWTAuth())
def update_item_notes(request, item_id: int, notes: str = ""):
    """Update notes for a wishlist item."""
    item, message = WishlistService.update_notes(request.auth, item_id, notes)
    if item is None:
        return 404, MessageSchema(message=message)
    return WishlistItemSchema(
        id=item.id,
        vehicle=item.vehicle,
        added_at=item.added_at,
        notes=item.notes
    )
