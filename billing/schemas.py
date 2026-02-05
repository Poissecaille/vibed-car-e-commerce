"""Schemas for billing API endpoints."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema


class InvoiceSchema(Schema):
    """Schema for invoice."""
    id: int
    order_id: UUID
    invoice_number: str
    issued_at: datetime
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    currency: str
    billing_name: str
    billing_address: dict
    pdf_url: str


class PaymentSchema(Schema):
    """Schema for payment."""
    id: int
    order_id: UUID
    provider: str
    provider_reference: str
    amount: Decimal
    currency: str
    status: str
    initiated_at: datetime
    paid_at: datetime | None = None


class PaymentCreateSchema(Schema):
    """Schema for initiating a payment."""
    provider: str = "MOCK"


class PaymentCallbackSchema(Schema):
    """Schema for payment callback/webhook."""
    provider_reference: str
    status: str
    provider_data: dict | None = None


class MessageSchema(Schema):
    """Generic message response."""
    message: str
