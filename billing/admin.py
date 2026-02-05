"""Admin configuration for billing models."""
from django.contrib import admin

from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice model."""

    list_display = [
        'invoice_number', 'order', 'billing_name', 'total_ttc',
        'currency', 'issued_at'
    ]
    list_filter = ['currency', 'issued_at']
    search_fields = ['invoice_number', 'order__order_number', 'billing_name']
    raw_id_fields = ['order']
    readonly_fields = [
        'invoice_number', 'total_ht', 'total_tva', 'total_ttc',
        'issued_at', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Facture', {
            'fields': ('invoice_number', 'order', 'issued_at')
        }),
        ('Montants', {
            'fields': (('total_ht', 'total_tva', 'total_ttc'), 'currency')
        }),
        ('Client', {
            'fields': ('billing_name', 'billing_address', 'company_name', 'company_vat_number')
        }),
        ('Document', {
            'fields': ('pdf_url', 'notes')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""

    list_display = [
        'id', 'order', 'provider', 'amount', 'currency',
        'status', 'initiated_at', 'paid_at'
    ]
    list_filter = ['provider', 'status', 'initiated_at']
    search_fields = ['order__order_number', 'provider_reference']
    raw_id_fields = ['order']
    readonly_fields = [
        'initiated_at', 'paid_at', 'refunded_at',
        'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Paiement', {
            'fields': ('order', 'amount', 'currency', 'status')
        }),
        ('Prestataire', {
            'fields': ('provider', 'provider_reference', 'provider_data')
        }),
        ('Erreur', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('initiated_at', 'paid_at', 'refunded_at'),
            'classes': ('collapse',)
        }),
    )
