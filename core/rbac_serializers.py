"""
RBAC Serializers with Field-Level Security
Different serializers show different fields based on user role
"""
from rest_framework import serializers
from .models import DomesticShipment
from .serializers import ShipmentLogSerializer


class DriverShipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for DRIVERS - hides financial information
    Drivers can see: tracking, addresses, package details
    Drivers CANNOT see: pricing, sender phone
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DomesticShipment
        fields = [
            'id', 'tracking_code', 'status', 'status_display',
            'receiver_name', 'receiver_phone',
            'origin_district', 'origin_sector',
            'destination_district', 'destination_sector',
            'weight', 'description',
            'picked_up_at', 'delivered_at'
        ]
        # Notice: NO 'price', NO 'sender_phone'


class CustomerShipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for CUSTOMERS - full details including price
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    logs = ShipmentLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = DomesticShipment
        fields = [
            'id', 'tracking_code', 'status', 'status_display',
            'sender_phone', 'receiver_name', 'receiver_phone',
            'origin_district', 'origin_sector',
            'destination_district', 'destination_sector',
            'weight', 'description', 'price',
            'transport_mode', 'created_at',
            'picked_up_at', 'delivered_at', 'logs'
        ]


class GovOfficialShipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for GOVERNMENT OFFICIALS - all data including audit info
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sender_details = serializers.SerializerMethodField()
    
    class Meta:
        model = DomesticShipment
        fields = '__all__'
    
    def get_sender_details(self, obj):
        """Include sender verification status for compliance"""
        return {
            'phone': obj.sender.phone,
            'verified': obj.sender.is_verified,
            'user_type': obj.sender.user_type
        }