"""Schemas for inventory API endpoints."""
from datetime import datetime
from uuid import UUID

from ninja import Schema


class InventoryItemSchema(Schema):
    """Schema for inventory item."""
    vehicle_id: UUID
    quantity: int
    location: str
    status: str
    reserved_by_id: UUID | None = None
    reserved_until: datetime | None = None
    notes: str
    is_available: bool
    updated_at: datetime


class InventoryItemUpdateSchema(Schema):
    """Schema for updating inventory item."""
    quantity: int | None = None
    location: str | None = None
    status: str | None = None
    notes: str | None = None


class InventoryLogSchema(Schema):
    """Schema for inventory log."""
    id: int
    vehicle_id: UUID
    previous_status: str
    new_status: str
    changed_by_id: UUID | None = None
    reason: str
    timestamp: datetime


class InventoryStatusUpdateSchema(Schema):
    """Schema for updating inventory status."""
    status: str
    reason: str = ""
