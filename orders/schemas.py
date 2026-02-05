"""Schemas for order API endpoints."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema

from vehicles.schemas import VehicleSchema


class OrderItemSchema(Schema):
    """Schema for order item."""
    id: int
    vehicle: VehicleSchema
    price_snapshot: Decimal


class OrderSchema(Schema):
    """Schema for order."""
    id: UUID
    order_number: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    tax_rate: Decimal
    total_amount: Decimal
    currency: str
    items_count: int
    created_at: datetime
    confirmed_at: datetime | None = None
    paid_at: datetime | None = None


class OrderDetailSchema(OrderSchema):
    """Detailed order schema with items."""
    items: list[OrderItemSchema]
    shipping_address: dict | None = None
    billing_address: dict | None = None
    customer_notes: str
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None


class OrderCreateSchema(Schema):
    """Schema for creating an order from cart."""
    shipping_address_id: UUID | None = None
    billing_address_id: UUID | None = None
    customer_notes: str = ""


class OrderStatusUpdateSchema(Schema):
    """Schema for updating order status."""
    status: str
    reason: str = ""


class OrderStatusHistorySchema(Schema):
    """Schema for order status history."""
    id: int
    previous_status: str
    new_status: str
    changed_by_email: str | None = None
    reason: str
    timestamp: datetime


class MessageSchema(Schema):
    """Generic message response."""
    message: str
