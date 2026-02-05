"""Schemas for wishlist API endpoints."""
from datetime import datetime
from uuid import UUID

from ninja import Schema

from vehicles.schemas import VehicleSchema


class WishlistItemSchema(Schema):
    """Schema for wishlist item."""
    id: int
    vehicle: VehicleSchema
    added_at: datetime
    notes: str


class WishlistItemCreateSchema(Schema):
    """Schema for adding item to wishlist."""
    vehicle_id: UUID
    notes: str = ""


class WishlistSchema(Schema):
    """Schema for wishlist."""
    items: list[WishlistItemSchema]
    items_count: int


class MessageSchema(Schema):
    """Generic message response."""
    message: str
