"""
Payment Models
Handles Mobile Money payments (MTN/Airtel)
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Payment(models.Model):
    """
    Payment record for shipment transactions
    Integrates with MTN Momo and Airtel Money
    """
    
    PAYMENT_METHOD_CHOICES = [
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('AIRTEL_MONEY', 'Airtel Money'),
        ('CASH', 'Cash on Delivery'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Primary identifiers
    payment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    transaction_ref = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="External payment provider reference"
    )
    
    # User & Shipment
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    shipment = models.ForeignKey(
        'domestic.DomesticShipment',
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,
        blank=True
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount in RWF"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='MTN_MOMO'
    )
    phone_number = models.CharField(
        max_length=17,
        help_text="Phone number used for payment"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    
    # Provider response
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw response from payment provider"
    )
    
    # Timestamps
    initiated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['status', '-initiated_at']),
            models.Index(fields=['user', '-initiated_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_ref} - {self.status}"
    
    @property
    def is_successful(self):
        return self.status == 'SUCCESSFUL'
    
    @property
    def is_pending(self):
        return self.status in ['PENDING', 'PROCESSING']


class PaymentWebhook(models.Model):
    """
    Stores all webhook callbacks from payment providers
    For audit and debugging
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='webhooks',
        null=True,
        blank=True
    )
    
    provider = models.CharField(max_length=50)
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    
    received_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-received_at']
    
    def __str__(self):
        return f"Webhook {self.provider} - {self.event_type}"