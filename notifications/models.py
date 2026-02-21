"""
Notification Models
Tracks all notifications sent to users
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    Notification record
    Tracks SMS and Email notifications
    """
    
    TYPE_CHOICES = [
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
        ('PUSH', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('DELIVERED', 'Delivered'),
    ]
    
    EVENT_CHOICES = [
        ('BOOKING_CREATED', 'Booking Created'),
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('SHIPMENT_PICKED_UP', 'Shipment Picked Up'),
        ('SHIPMENT_IN_TRANSIT', 'Shipment In Transit'),
        ('SHIPMENT_OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('SHIPMENT_DELIVERED', 'Delivered'),
        ('SHIPMENT_CANCELLED', 'Cancelled'),
    ]
    
    # Recipient
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    recipient_phone = models.CharField(max_length=17, blank=True)
    recipient_email = models.EmailField(blank=True)
    
    # Notification details
    notification_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='SMS'
    )
    event = models.CharField(
        max_length=30,
        choices=EVENT_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    # Related objects
    shipment_id = models.IntegerField(null=True, blank=True)
    booking_id = models.IntegerField(null=True, blank=True)
    payment_id = models.IntegerField(null=True, blank=True)
    
    # Provider response
    provider = models.CharField(max_length=50, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    external_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['event', '-created_at']),
            models.Index(fields=['recipient_phone']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.event} to {self.recipient_phone or self.recipient_email}"