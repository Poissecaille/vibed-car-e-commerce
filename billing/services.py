"""Business logic services for billing."""
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.services import AuditService
from orders.models import Order, OrderStatus
from orders.services import OrderService

from .models import Invoice, Payment, PaymentProvider, PaymentStatus


class InvoiceService:
    """Service for invoice operations."""

    @staticmethod
    def get_invoice(invoice_id: int) -> Invoice | None:
        """Get invoice by ID."""
        try:
            return Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return None

    @staticmethod
    def get_invoice_by_number(invoice_number: str) -> Invoice | None:
        """Get invoice by number."""
        try:
            return Invoice.objects.get(invoice_number=invoice_number)
        except Invoice.DoesNotExist:
            return None

    @staticmethod
    def get_order_invoice(order: Order) -> Invoice | None:
        """Get invoice for an order."""
        try:
            return order.invoice
        except Invoice.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_invoice(order: Order, actor=None, request=None) -> Invoice:
        """Create an invoice for an order."""
        # Check if invoice already exists
        if hasattr(order, 'invoice'):
            return order.invoice

        # Get billing info
        billing_address = order.billing_address or order.shipping_address or {}
        user = order.user

        invoice = Invoice.objects.create(
            order=order,
            total_ht=order.subtotal,
            total_tva=order.tax_amount,
            total_ttc=order.total_amount,
            currency=order.currency,
            billing_name=user.full_name,
            billing_address=billing_address,
        )

        AuditService.log_create(invoice, actor=actor, request=request)
        return invoice

    @staticmethod
    def get_user_invoices(user):
        """Get all invoices for a user."""
        return Invoice.objects.filter(order__user=user).order_by('-issued_at')


class PaymentService:
    """Service for payment operations."""

    @staticmethod
    def get_payment(payment_id: int) -> Payment | None:
        """Get payment by ID."""
        try:
            return Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return None

    @staticmethod
    def get_order_payments(order: Order):
        """Get all payments for an order."""
        return order.payments.all()

    @staticmethod
    @transaction.atomic
    def initiate_payment(
        order: Order,
        provider: str = PaymentProvider.MOCK,
        actor=None,
        request=None
    ) -> tuple[Payment, str]:
        """Initiate a new payment for an order."""
        # Check order status
        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            return None, "Cette commande ne peut pas être payée"

        # Check for existing successful payment
        existing = order.payments.filter(status=PaymentStatus.SUCCESS).first()
        if existing:
            return None, "Cette commande a déjà été payée"

        # Create payment
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentStatus.INITIATED,
        )

        AuditService.log_create(payment, actor=actor, request=request)

        # For mock provider, auto-generate a reference
        if provider == PaymentProvider.MOCK:
            payment.provider_reference = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
            payment.save(update_fields=['provider_reference'])

        return payment, "Paiement initialisé"

    @staticmethod
    @transaction.atomic
    def process_payment_callback(
        payment: Payment,
        status: str,
        provider_reference: str = None,
        provider_data: dict = None,
        error_message: str = "",
        actor=None,
        request=None
    ) -> tuple[Payment, str]:
        """Process a payment callback/webhook."""
        old_status = payment.status

        if provider_reference:
            payment.provider_reference = provider_reference
        if provider_data:
            payment.provider_data = provider_data

        payment.status = status
        payment.error_message = error_message

        if status == PaymentStatus.SUCCESS:
            payment.paid_at = timezone.now()
            # Update order status
            OrderService.update_status(
                payment.order,
                OrderStatus.PAID,
                actor=actor,
                reason=f"Paiement {payment.id} réussi",
                request=request
            )
            # Create invoice
            InvoiceService.create_invoice(payment.order, actor=actor, request=request)

        elif status == PaymentStatus.REFUNDED:
            payment.refunded_at = timezone.now()
            OrderService.update_status(
                payment.order,
                OrderStatus.REFUNDED,
                actor=actor,
                reason=f"Paiement {payment.id} remboursé",
                request=request
            )

        payment.save()

        AuditService.log_status_change(
            payment,
            old_status,
            status,
            actor=actor,
            request=request,
            extra_data={'provider_reference': provider_reference}
        )

        return payment, f"Paiement mis à jour: {status}"

    @staticmethod
    def mock_pay(payment: Payment, actor=None, request=None) -> tuple[Payment, str]:
        """
        Simulate a successful payment (for testing/development).
        Only works with MOCK provider.
        """
        if payment.provider != PaymentProvider.MOCK:
            return payment, "Seul le provider MOCK peut être simulé"

        if payment.status != PaymentStatus.INITIATED:
            return payment, "Ce paiement a déjà été traité"

        return PaymentService.process_payment_callback(
            payment,
            status=PaymentStatus.SUCCESS,
            provider_data={'mock': True, 'timestamp': timezone.now().isoformat()},
            actor=actor,
            request=request
        )

    @staticmethod
    def get_user_payments(user):
        """Get all payments for a user."""
        return Payment.objects.filter(order__user=user).order_by('-initiated_at')
