"""
Domestic Shipment Views
API endpoints for shipment management and tracking
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import DomesticShipment, ShipmentLog
from .serializers import (
    DomesticShipmentSerializer,
    ShipmentCreateSerializer,
    StatusUpdateSerializer,
    BatchStatusUpdateSerializer,
    ShipmentLogSerializer
)
from .tasks import update_shipment_status_task, batch_update_shipments_task


class DomesticShipmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing domestic shipments
    Supports create, list, retrieve, update, delete
    """
    queryset = DomesticShipment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'transport_mode', 'origin_district', 'destination_district']
    search_fields = ['tracking_code', 'receiver_name', 'receiver_phone']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return ShipmentCreateSerializer
        return DomesticShipmentSerializer
    
    def perform_create(self, serializer):
        """Set sender to current user when creating shipment"""
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        POST /api/shipments/{id}/update-status/
        Update shipment status asynchronously
        
        Triggers async task that:
        1. Updates status
        2. Creates tracking log
        3. Sends SMS notifications
        """
        shipment = self.get_object()
        serializer = StatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Trigger async task
            task = update_shipment_status_task.delay(
                shipment_id=shipment.id,
                new_status=serializer.validated_data['status'],
                location=serializer.validated_data.get('location', ''),
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'message': 'Status update processing',
                'tracking_code': shipment.tracking_code,
                'new_status': serializer.validated_data['status'],
                'task_id': task.id,
                'note': 'Notifications will be sent to sender and receiver'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='tracking')
    def tracking(self, request, pk=None):
        """
        GET /api/shipments/{id}/tracking/
        Get full tracking history for a shipment
        """
        shipment = self.get_object()
        logs = shipment.logs.all()
        
        return Response({
            'tracking_code': shipment.tracking_code,
            'current_status': shipment.get_status_display(),
            'created_at': shipment.created_at,
            'delivered_at': shipment.delivered_at,
            'history': ShipmentLogSerializer(logs, many=True).data
        })
    
    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request):
        """
        POST /api/shipments/batch-update/
        Update multiple shipments at once
        
        Body:
        {
            "tracking_codes": ["RW-260216-1234", "RW-260216-5678"],
            "status": "AT_HUB"
        }
        """
        serializer = BatchStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            tracking_codes = serializer.validated_data['tracking_codes']
            new_status = serializer.validated_data['status']
            
            # Get shipment IDs from tracking codes
            shipments = DomesticShipment.objects.filter(
                tracking_code__in=tracking_codes
            )
            shipment_ids = list(shipments.values_list('id', flat=True))
            
            if not shipment_ids:
                return Response({
                    'error': 'No valid shipments found with provided tracking codes'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Trigger async batch update
            task = batch_update_shipments_task.delay(
                shipment_ids=shipment_ids,
                new_status=new_status
            )
            
            return Response({
                'message': f'Processing batch update for {len(shipment_ids)} shipments',
                'task_id': task.id,
                'status': 'queued',
                'shipments_count': len(shipment_ids)
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)