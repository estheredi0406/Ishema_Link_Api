"""
Booking Serializers
"""
from rest_framework import serializers
from .models import Booking


class UnifiedBookingSerializer(serializers.Serializer):
    """
    Unified booking request
    Creates shipment + initiates payment in one call
    """
    # Shipment details
    receiver_name = serializers.CharField(max_length=100)
    receiver_phone = serializers.CharField(max_length=17)
    receiver_address = serializers.CharField(max_length=255, required=False)
    delivery_address = serializers.CharField(max_length=255, required=False)
    
    origin_district = serializers.CharField(max_length=50)
    origin_sector = serializers.CharField(max_length=50)
    destination_district = serializers.CharField(max_length=50)
    destination_sector = serializers.CharField(max_length=50)
    
    weight = serializers.DecimalField(max_digits=6, decimal_places=2)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    transport_mode = serializers.ChoiceField(
        choices=['BUS', 'MOTORCYCLE', 'TRUCK'],
        default='BUS'
    )
    
    # Payment details
    payment_method = serializers.ChoiceField(
        choices=['MTN_MOMO', 'AIRTEL_MONEY', 'CASH'],
        default='MTN_MOMO'
    )
    payment_phone = serializers.CharField(
        max_length=17,
        required=False,
        help_text="Phone for payment (defaults to user's phone)"
    )


class BookingSerializer(serializers.ModelSerializer):
    """Booking details"""
    shipment_tracking_code = serializers.CharField(source='shipment.tracking_code', read_only=True)
    payment_transaction_ref = serializers.CharField(source='payment.transaction_ref', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'booking_reference', 'status', 'status_display',
            'total_amount', 'shipment_tracking_code',
            'payment_transaction_ref', 'created_at'
        ]