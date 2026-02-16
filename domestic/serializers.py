"""
Domestic Shipment Serializers
Handles conversion between Shipment models and JSON
"""
from rest_framework import serializers
from .models import DomesticShipment, ShipmentLog
from core.validators import validate_rwanda_phone


class ShipmentLogSerializer(serializers.ModelSerializer):
    """Serializer for shipment tracking logs"""
    
    class Meta:
        model = ShipmentLog
        fields = ['id', 'status', 'location', 'notes', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']


class DomesticShipmentSerializer(serializers.ModelSerializer):
    """Serializer for domestic shipments"""
    
    logs = ShipmentLogSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DomesticShipment
        fields = [
            'id', 'tracking_code', 'status', 'status_display',
            'sender', 'sender_phone', 'receiver_name', 'receiver_phone',
            'origin_district', 'origin_sector',
            'destination_district', 'destination_sector',
            'delivery_address', 'weight', 'description',
            'transport_mode', 'price',
            'created_at', 'updated_at', 'picked_up_at', 'delivered_at',
            'logs'
        ]
        read_only_fields = ['id', 'tracking_code', 'created_at', 'updated_at', 'picked_up_at', 'delivered_at']
    
    def validate_sender_phone(self, value):
        """Validate sender phone format"""
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_receiver_phone(self, value):
        """Validate receiver phone format"""
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new shipments"""
    
    class Meta:
        model = DomesticShipment
        fields = [
            'sender_phone', 'receiver_name', 'receiver_phone',
            'origin_district', 'origin_sector',
            'destination_district', 'destination_sector',
            'delivery_address', 'weight', 'description',
            'transport_mode', 'price'
        ]
    
    def validate_sender_phone(self, value):
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_receiver_phone(self, value):
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value


class StatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating shipment status"""
    
    status = serializers.ChoiceField(choices=DomesticShipment.STATUS_CHOICES)
    location = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class BatchStatusUpdateSerializer(serializers.Serializer):
    """Serializer for batch status updates"""
    
    tracking_codes = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1,
        max_length=100
    )
    status = serializers.ChoiceField(choices=DomesticShipment.STATUS_CHOICES)