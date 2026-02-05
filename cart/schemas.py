"""Schemas for cart API endpoints."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema

from vehicles.schemas import VehicleSchema


class CartItemSchema(Schema):
    """Schema for cart item."""
    id: int
    vehicle: VehicleSchema
    price_snapshot: Decimal
    added_at: datetime


class CartItemCreateSchema(Schema):
    """Schema for adding item to cart."""
    vehicle_id: UUID


class CartSchema(Schema):
    """Schema for cart."""
    id: UUID
    status: str
    items: list[CartItemSchema]
    items_count: int
    total_amount: Decimal
    created_at: datetime
    expires_at: datetime | None = None


class MessageSchema(Schema):
    """Generic message response."""
    message: str
