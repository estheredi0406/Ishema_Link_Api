"""
Domestic Shipment Models
Handles local deliveries within Rwanda
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class DomesticShipment(models.Model):
    """
    Shipment for domestic (local Rwanda) deliveries
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Pickup'),
        ('PICKED_UP', 'Picked Up'),
        ('IN_TRANSIT', 'In Transit'),
        ('AT_HUB', 'At Hub'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TRANSPORT_CHOICES = [
        ('MOTO', 'Motorcycle'),
        ('BUS', 'Bus'),
    ]
    
    # Tracking
    tracking_code = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Sender & Receiver
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_domestic_shipments'
    )
    sender_phone = models.CharField(max_length=17)
    receiver_name = models.CharField(max_length=100)
    receiver_phone = models.CharField(max_length=17)
    
    # Location
    origin_district = models.CharField(max_length=50)
    origin_sector = models.CharField(max_length=50)
    destination_district = models.CharField(max_length=50)
    destination_sector = models.CharField(max_length=50)
    delivery_address = models.TextField()
    
    # Package Details
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in KG")
    description = models.TextField()
    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_CHOICES, default='MOTO')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_code']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.tracking_code} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Generate tracking code if not exists
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)
    
    def generate_tracking_code(self):
        """Generate unique tracking code: RW-YYMMDD-XXXX"""
        import random
        date_part = timezone.now().strftime('%y%m%d')
        random_part = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"RW-{date_part}-{random_part}"


class ShipmentLog(models.Model):
    """
    Tracking log for shipment status changes
    Records every status change with timestamp and location
    """
    shipment = models.ForeignKey(
        DomesticShipment,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    status = models.CharField(max_length=20)
    location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.shipment.tracking_code} - {self.status} at {self.created_at}"