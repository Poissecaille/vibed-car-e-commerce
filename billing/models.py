"""Billing models for invoices and payments."""
from decimal import Decimal

from django.db import models

from core.models import TimestampedModel


class PaymentStatus(models.TextChoices):
    """Payment status enumeration."""
    INITIATED = 'INITIATED', 'Initialisé'
    PENDING = 'PENDING', 'En attente'
    PROCESSING = 'PROCESSING', 'En cours de traitement'
    SUCCESS = 'SUCCESS', 'Réussi'
    FAILED = 'FAILED', 'Échoué'
    CANCELLED = 'CANCELLED', 'Annulé'
    REFUNDED = 'REFUNDED', 'Remboursé'


class PaymentProvider(models.TextChoices):
    """Payment provider enumeration."""
    STRIPE = 'STRIPE', 'Stripe'
    PAYPAL = 'PAYPAL', 'PayPal'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Virement bancaire'
    CHECK = 'CHECK', 'Chèque'
    CASH = 'CASH', 'Espèces'
    MOCK = 'MOCK', 'Mock (Test)'


class Invoice(TimestampedModel):
    """Invoice for an order."""

    id = models.BigAutoField(primary_key=True)
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='invoice'
    )
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    # Amounts
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total HT")
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total TVA")
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total TTC")
    currency = models.CharField(max_length=3, default='EUR')

    # Billing details (snapshot)
    billing_name = models.CharField(max_length=255)
    billing_address = models.JSONField()
    company_name = models.CharField(max_length=255, blank=True)
    company_vat_number = models.CharField(max_length=50, blank=True)

    # PDF storage
    pdf_url = models.URLField(blank=True)

    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'invoices'
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-issued_at']

    def __str__(self):
        return f"Facture {self.invoice_number} - {self.order.order_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)

    def _generate_invoice_number(self) -> str:
        """Generate a unique invoice number."""
        from django.utils import timezone
        year = timezone.now().year
        count = Invoice.objects.filter(
            issued_at__year=year
        ).count() + 1
        return f"FAC-{year}-{count:06d}"


class Payment(TimestampedModel):
    """Payment record for an order."""

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    provider = models.CharField(
        max_length=20,
        choices=PaymentProvider.choices,
        default=PaymentProvider.MOCK
    )
    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Référence du paiement chez le prestataire"
    )
    provider_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Données brutes du prestataire"
    )

    # Amount
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')

    # Status
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.INITIATED,
        db_index=True
    )
    error_message = models.TextField(blank=True)

    # Dates
    initiated_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['provider', 'provider_reference']),
        ]

    def __str__(self):
        return f"Paiement {self.id} - {self.order.order_number} ({self.status})"

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.SUCCESS
