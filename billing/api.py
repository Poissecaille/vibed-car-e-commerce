"""API endpoints for billing."""
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from orders.models import Order

from .models import Invoice, Payment
from .schemas import (
    InvoiceSchema,
    MessageSchema,
    PaymentCallbackSchema,
    PaymentCreateSchema,
    PaymentSchema,
)
from .services import InvoiceService, PaymentService

router = Router()


# Invoice endpoints
@router.get("/invoices", response=list[InvoiceSchema], auth=JWTAuth())
def list_invoices(request):
    """List current user's invoices."""
    invoices = InvoiceService.get_user_invoices(request.auth)
    return [_build_invoice_response(inv) for inv in invoices]


@router.get("/invoices/{invoice_id}", response=InvoiceSchema, auth=JWTAuth())
def get_invoice(request, invoice_id: int):
    """Get invoice details."""
    invoice = InvoiceService.get_invoice(invoice_id)
    if not invoice:
        return router.create_response(request, {"detail": "Facture non trouvée"}, status=404)

    # Check permission
    if invoice.order.user != request.auth and not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    return _build_invoice_response(invoice)


@router.get("/invoices/order/{order_id}", response=InvoiceSchema, auth=JWTAuth())
def get_order_invoice(request, order_id: UUID):
    """Get invoice for an order."""
    order = get_object_or_404(Order, id=order_id)

    # Check permission
    if order.user != request.auth and not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    invoice = InvoiceService.get_order_invoice(order)
    if not invoice:
        return router.create_response(request, {"detail": "Facture non trouvée"}, status=404)

    return _build_invoice_response(invoice)


# Payment endpoints
@router.get("/payments", response=list[PaymentSchema], auth=JWTAuth())
def list_payments(request):
    """List current user's payments."""
    payments = PaymentService.get_user_payments(request.auth)
    return [_build_payment_response(p) for p in payments]


@router.get("/payments/{payment_id}", response=PaymentSchema, auth=JWTAuth())
def get_payment(request, payment_id: int):
    """Get payment details."""
    payment = PaymentService.get_payment(payment_id)
    if not payment:
        return router.create_response(request, {"detail": "Paiement non trouvé"}, status=404)

    # Check permission
    if payment.order.user != request.auth and not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    return _build_payment_response(payment)


@router.post("/orders/{order_id}/pay", response={201: PaymentSchema, 400: MessageSchema}, auth=JWTAuth())
def initiate_payment(request, order_id: UUID, data: PaymentCreateSchema):
    """Initiate a payment for an order."""
    order = get_object_or_404(Order, id=order_id)

    # Check permission
    if order.user != request.auth:
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    payment, message = PaymentService.initiate_payment(
        order,
        provider=data.provider,
        actor=request.auth,
        request=request
    )

    if payment is None:
        return 400, MessageSchema(message=message)

    return 201, _build_payment_response(payment)


@router.post("/payments/{payment_id}/mock-pay", response={200: PaymentSchema, 400: MessageSchema}, auth=JWTAuth())
def mock_pay(request, payment_id: int):
    """Simulate a successful payment (development only)."""
    payment = PaymentService.get_payment(payment_id)
    if not payment:
        return router.create_response(request, {"detail": "Paiement non trouvé"}, status=404)

    # Check permission
    if payment.order.user != request.auth and not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    payment, message = PaymentService.mock_pay(
        payment,
        actor=request.auth,
        request=request
    )

    if "Seul le provider MOCK" in message or "déjà été traité" in message:
        return 400, MessageSchema(message=message)

    return _build_payment_response(payment)


# Webhook endpoint (for payment providers)
@router.post("/webhooks/{provider}", response=dict, auth=None)
def payment_webhook(request, provider: str, data: PaymentCallbackSchema):
    """Handle payment provider webhooks."""
    # Find payment by provider reference
    try:
        payment = Payment.objects.get(
            provider=provider.upper(),
            provider_reference=data.provider_reference
        )
    except Payment.DoesNotExist:
        return {"status": "error", "message": "Payment not found"}

    payment, message = PaymentService.process_payment_callback(
        payment,
        status=data.status,
        provider_data=data.provider_data,
        request=request
    )

    return {"status": "ok", "message": message}


def _build_invoice_response(invoice: Invoice) -> InvoiceSchema:
    """Build invoice response schema."""
    return InvoiceSchema(
        id=invoice.id,
        order_id=invoice.order_id,
        invoice_number=invoice.invoice_number,
        issued_at=invoice.issued_at,
        total_ht=invoice.total_ht,
        total_tva=invoice.total_tva,
        total_ttc=invoice.total_ttc,
        currency=invoice.currency,
        billing_name=invoice.billing_name,
        billing_address=invoice.billing_address,
        pdf_url=invoice.pdf_url,
    )


def _build_payment_response(payment: Payment) -> PaymentSchema:
    """Build payment response schema."""
    return PaymentSchema(
        id=payment.id,
        order_id=payment.order_id,
        provider=payment.provider,
        provider_reference=payment.provider_reference,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        initiated_at=payment.initiated_at,
        paid_at=payment.paid_at,
    )
