"""
Booking Models
Tracks unified bookings (shipment + payment)
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Booking(models.Model):
    """
    Unified booking record
    Links shipment and payment together
    """
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    
    # Linked records
    shipment = models.OneToOneField(
        'domestic.DomesticShipment',
        on_delete=models.CASCADE,
        related_name='booking'
    )
    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.CASCADE,
        related_name='booking',
        null=True,
        blank=True
    )
    
    # Booking details
    booking_reference = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique booking reference"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING_PAYMENT',
        db_index=True
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total booking amount"
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.status}"