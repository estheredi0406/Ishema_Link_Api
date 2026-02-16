"""
Manifest Serializers
Handles pagination and efficient data loading for manifests
"""
from rest_framework import serializers
from .models import Manifest, DomesticShipment
from .serializers import DomesticShipmentSerializer


class ManifestShipmentSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for shipments in manifest list
    Shows only essential info to reduce payload size
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DomesticShipment
        fields = [
            'id', 'tracking_code', 'status', 'status_display',
            'receiver_name', 'receiver_phone', 'weight',
            'destination_district', 'destination_sector'
        ]


class ManifestListSerializer(serializers.ModelSerializer):
    """
    Serializer for manifest list view
    Minimal data for performance
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_manifest_type_display', read_only=True)
    shipment_count = serializers.IntegerField(source='total_shipments', read_only=True)
    
    class Meta:
        model = Manifest
        fields = [
            'id', 'manifest_number', 'manifest_type', 'type_display',
            'status', 'status_display', 'origin_district', 'destination_district',
            'shipment_count', 'scheduled_departure', 'created_at'
        ]


class ManifestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed manifest serializer
    Includes paginated shipments
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_manifest_type_display', read_only=True)
    shipment_count = serializers.IntegerField(source='total_shipments', read_only=True)
    total_weight_kg = serializers.DecimalField(
        source='total_weight',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Manifest
        fields = [
            'id', 'manifest_number', 'manifest_type', 'type_display',
            'status', 'status_display',
            'origin_district', 'destination_district',
            'assigned_agent', 'vehicle_number', 'driver_name', 'driver_phone',
            'scheduled_departure', 'actual_departure',
            'scheduled_arrival', 'actual_arrival',
            'shipment_count', 'total_weight_kg',
            'notes', 'created_by', 'created_at', 'updated_at'
        ]


class ManifestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating manifests
    """
    shipment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Manifest
        fields = [
            'manifest_type', 'origin_district', 'destination_district',
            'assigned_agent', 'vehicle_number', 'driver_name', 'driver_phone',
            'scheduled_departure', 'notes', 'shipment_ids'
        ]
    
    def create(self, validated_data):
        shipment_ids = validated_data.pop('shipment_ids', [])
        manifest = Manifest.objects.create(**validated_data)
        
        # Add shipments
        if shipment_ids:
            shipments = DomesticShipment.objects.filter(id__in=shipment_ids)
            manifest.shipments.set(shipments)
        
        return manifest


class AddShipmentsSerializer(serializers.Serializer):
    """
    Serializer for adding shipments to manifest
    """
    shipment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )