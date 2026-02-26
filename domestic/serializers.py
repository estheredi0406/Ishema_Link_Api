"""
Domestic Shipment Serializers
Handles conversion between Shipment models and JSON
"""
from rest_framework import serializers
from .models import DomesticShipment, ShipmentLog
from core.validators import validate_rwanda_phone
import logging

logger = logging.getLogger(__name__)


class ShipmentLogSerializer(serializers.ModelSerializer):
    """Serializer for shipment tracking logs"""
    
    class Meta:
        model = ShipmentLog
        fields = ['id', 'status', 'location', 'notes', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']


class DomesticShipmentSerializer(serializers.ModelSerializer):
    """Serializer for domestic shipments (used for responses)"""
    
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
        read_only_fields = ['id', 'price', 'tracking_code', 'sender', 'created_at', 'updated_at', 'picked_up_at', 'delivered_at']
    
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
            'transport_mode'
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
    
    def _calculate_price(self, validated_data):
        """Calculate price using tariff service"""
        from .tariff_service import TariffService
        from decimal import Decimal
        
        try:
            tariff_result = TariffService.calculate_tariff(
                weight=Decimal(str(validated_data['weight'])),
                origin_district=validated_data['origin_district'],
                destination_district=validated_data['destination_district'],
                transport_mode=validated_data['transport_mode']
            )
            
            logger.info(f" Tariff calculation result: {tariff_result}")
            
            if not tariff_result.get('success'):
                error_msg = tariff_result.get('error', 'Unable to calculate price')
                logger.error(f" Tariff calculation failed: {error_msg}")
                raise serializers.ValidationError({'price': error_msg})
            
            price = Decimal(str(tariff_result['price']))
            logger.info(f" Price calculated: {price} RWF")
            return price
            
        except Exception as e:
            logger.error(f" Error calculating price: {str(e)}")
            raise serializers.ValidationError({'price': str(e)})
    
    def create(self, validated_data):
        """
        Create shipment with automatic price calculation
        """
        logger.info(" Starting shipment creation...")
        logger.info(f"   Origin: {validated_data['origin_district']} → {validated_data['destination_district']}")
        logger.info(f"   Weight: {validated_data['weight']} kg")
        logger.info(f"   Transport: {validated_data['transport_mode']}")
        
        # Calculate price
        price = self._calculate_price(validated_data)
        
        # Add calculated price to validated_data
        validated_data['price'] = price
        
        # Create shipment
        shipment = DomesticShipment.objects.create(**validated_data)
        
        logger.info(f" Shipment created successfully!")
        logger.info(f"   ID: {shipment.id}")
        logger.info(f"   Tracking Code: {shipment.tracking_code}")
        logger.info(f"   Price: {shipment.price}")
        
        # Return the actual model instance (not dict)
        return shipment


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