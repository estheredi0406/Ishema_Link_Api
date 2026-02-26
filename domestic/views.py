from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import logging

from .models import DomesticShipment, ShipmentLog
from .serializers import (
    DomesticShipmentSerializer, 
    ShipmentCreateSerializer, 
    StatusUpdateSerializer,
    BatchStatusUpdateSerializer,
    ShipmentLogSerializer
)

logger = logging.getLogger(__name__)


class DomesticShipmentViewSet(viewsets.ModelViewSet):
    queryset = DomesticShipment.objects.all().prefetch_related('logs').order_by('-created_at')
    serializer_class = DomesticShipmentSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ShipmentCreateSerializer
        if self.action == 'update_status':
            return StatusUpdateSerializer
        if self.action == 'batch_update':
            return BatchStatusUpdateSerializer
        return DomesticShipmentSerializer

    def create(self, request, *args, **kwargs):
        """Override create to ensure proper response with price"""
        logger.info("📝 CREATE REQUEST RECEIVED")
        logger.info(f"   Data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"❌ Validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # This calls serializer.create() and calculates the price
        shipment = serializer.save(sender=request.user)
        
        logger.info(f"✅ Shipment saved! Price: {shipment.price}")
        
        # NOW return the FULL serializer with all fields including price!
        response_serializer = DomesticShipmentSerializer(shipment)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """Pass the authenticated user to the serializer's save method"""
        logger.info(f"👤 Creating shipment for user: {self.request.user}")
        shipment = serializer.save(sender=self.request.user)
        logger.info(f"📦 Shipment created: {shipment.tracking_code}, price={shipment.price}")
        return shipment

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Updates the status of a single shipment and logs the change"""
        shipment = self.get_object()
        serializer = StatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            
            with transaction.atomic():
                if new_status == 'PICKED_UP':
                    shipment.picked_up_at = timezone.now()
                elif new_status == 'DELIVERED':
                    shipment.delivered_at = timezone.now()
                
                shipment.status = new_status
                shipment.save()
                
                ShipmentLog.objects.create(
                    shipment=shipment,
                    status=new_status,
                    location=serializer.validated_data.get('location', ''),
                    notes=serializer.validated_data.get('notes', ''),
                    created_by=request.user
                )
            
            return Response({'status': 'Status updated successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Returns the log history for a specific shipment"""
        shipment = self.get_object()
        logs = shipment.logs.all().order_by('-created_at')
        serializer = ShipmentLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request):
        """Updates multiple shipments at once via tracking codes"""
        serializer = BatchStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            codes = serializer.validated_data['tracking_codes']
            new_status = serializer.validated_data['status']
            
            updated_count = DomesticShipment.objects.filter(tracking_code__in=codes).update(
                status=new_status,
                updated_at=timezone.now()
            )
            
            return Response({
                'message': f'Successfully updated {updated_count} shipments',
                'updated_count': updated_count
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)