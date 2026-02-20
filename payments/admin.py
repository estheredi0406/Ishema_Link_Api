"""
Payment Admin
"""
from django.contrib import admin
from .models import Payment, PaymentWebhook


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_ref', 'user', 'amount', 'payment_method',
        'status', 'shipment', 'initiated_at'
    ]
    list_filter = ['status', 'payment_method', 'initiated_at']
    search_fields = ['transaction_ref', 'user__phone', 'phone_number']
    readonly_fields = [
        'payment_id', 'transaction_ref', 'initiated_at',
        'completed_at', 'failed_at', 'provider_response'
    ]


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ['provider', 'event_type', 'payment', 'received_at', 'processed']
    list_filter = ['processed', 'provider', 'received_at']
    readonly_fields = ['received_at', 'payload']