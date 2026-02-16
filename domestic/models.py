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
    

class TariffZone(models.Model):
    """
    Geographic zones for tariff calculation
    Rwanda is divided into pricing zones
    """
    name = models.CharField(max_length=100, unique=True)
    districts = models.JSONField(help_text="List of districts in this zone")  # Keep for reference
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TariffZone(models.Model):
    """
    Geographic zones for tariff calculation
    Rwanda is divided into pricing zones
    """
    name = models.CharField(max_length=100, unique=True)
    districts = models.JSONField(help_text="List of districts in this zone")
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DomesticTariff(models.Model):
    """
    Tariff rates for domestic shipments
    Pricing based on: weight, origin zone, destination zone, transport mode
    """
    # Weight range (in KG)
    min_weight = models.DecimalField(max_digits=6, decimal_places=2)
    max_weight = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Zones
    origin_zone = models.ForeignKey(
        TariffZone, 
        on_delete=models.CASCADE,
        related_name='origin_tariffs'
    )
    destination_zone = models.ForeignKey(
        TariffZone,
        on_delete=models.CASCADE,
        related_name='destination_tariffs'
    )
    
    # Transport mode
    transport_mode = models.CharField(
        max_length=10,
        choices=DomesticShipment.TRANSPORT_CHOICES
    )
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Validity
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['origin_zone', 'destination_zone', 'transport_mode']),
            models.Index(fields=['is_active', 'effective_date']),
        ]




    
    def __str__(self):
        return f"{self.origin_zone} → {self.destination_zone} ({self.transport_mode})"
class Manifest(models.Model):
    """
    Manifest - collection of shipments for a specific route/vehicle
    Used by agents to track bulk shipments
    """
    MANIFEST_TYPE_CHOICES = [
        ('BUS_ROUTE', 'Bus Route'),
        ('MOTO_DELIVERY', 'Motorcycle Delivery'),
        ('HUB_TRANSFER', 'Hub Transfer'),
        ('PICKUP_ROUTE', 'Pickup Route'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_TRANSIT', 'In Transit'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Manifest details
    manifest_number = models.CharField(max_length=20, unique=True, db_index=True)
    manifest_type = models.CharField(max_length=20, choices=MANIFEST_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Route information
    origin_district = models.CharField(max_length=50)
    destination_district = models.CharField(max_length=50)
    
    # Assignment
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_manifests',
        limit_choices_to={'user_type': 'AGENT'}
    )
    
    # Shipments (many-to-many)
    shipments = models.ManyToManyField(
        DomesticShipment,
        related_name='manifests',
        blank=True
    )
    
    # Vehicle/Transport info
    vehicle_number = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=17, blank=True)
    
    # Schedule
    scheduled_departure = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)
    scheduled_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_manifests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['manifest_number']),
            models.Index(fields=['status', 'origin_district']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.manifest_number} - {self.origin_district} → {self.destination_district}"
    
    def save(self, *args, **kwargs):
        # Generate manifest number if not exists
        if not self.manifest_number:
            self.manifest_number = self.generate_manifest_number()
        super().save(*args, **kwargs)
    
    def generate_manifest_number(self):
        """Generate unique manifest number: MAN-YYMMDD-XXXX"""
        import random
        date_part = timezone.now().strftime('%y%m%d')
        random_part = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"MAN-{date_part}-{random_part}"
    
    @property
    def total_shipments(self):
        """Count of shipments in this manifest"""
        return self.shipments.count()
    
    @property
    def total_weight(self):
        """Total weight of all shipments"""
        from django.db.models import Sum
        result = self.shipments.aggregate(total=Sum('weight'))
        return result['total'] or 0