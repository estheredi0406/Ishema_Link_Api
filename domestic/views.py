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
from django.db import models
from .models import DomesticShipment, ShipmentLog
from .serializers import (
    DomesticShipmentSerializer,
    ShipmentCreateSerializer,
    StatusUpdateSerializer,
    BatchStatusUpdateSerializer,
    ShipmentLogSerializer
)
from .tasks import update_shipment_status_task, batch_update_shipments_task
from core.permissions import IsShipmentOwner, CanViewFinancialData
from .rbac_serializers import DriverShipmentSerializer, CustomerShipmentSerializer, GovOfficialShipmentSerializer


class DomesticShipmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shipments with RBAC
    Different users see different data based on their role
    """
    permission_classes = [IsAuthenticated, IsShipmentOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'transport_mode', 'origin_district', 'destination_district']
    search_fields = ['tracking_code', 'receiver_name', 'receiver_phone']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter queryset based on user role
        - Customers: Only their own shipments
        - Agents: Shipments in their sector
        - Drivers: Shipments assigned to them
        - Admin/Gov: All shipments
        """
        user = self.request.user
        
        # Admin and Gov officials see all
        if user.user_type in ['ADMIN', 'GOV_OFFICIAL']:
            return DomesticShipment.objects.all()
        
        # Agents see shipments in their sector
        if user.is_agent and user.assigned_sector:
            return DomesticShipment.objects.filter(
                models.Q(origin_sector=user.assigned_sector) |
                models.Q(destination_sector=user.assigned_sector)
            )
        
        # Customers see shipments they sent or received
        if user.is_customer:
            return DomesticShipment.objects.filter(
                models.Q(sender=user) |
                models.Q(receiver_phone=user.phone)
            )
        
        # Drivers see shipments in their manifests
        if user.is_driver:
            # For now, show all (we'll refine with manifest assignment)
            return DomesticShipment.objects.all()
        
        # Default: empty queryset
        return DomesticShipment.objects.none()
    
    def get_serializer_class(self):
        """
        Return different serializers based on user role
        Field-level security: Drivers don't see pricing
        """
        user = self.request.user
        
        # Different serializer for create action
        if self.action == 'create':
            return ShipmentCreateSerializer
        
        # Drivers get limited serializer (no pricing)
        if user.is_driver:
            return DriverShipmentSerializer
        
        # Gov officials get full data serializer
        if user.is_gov_official:
            return GovOfficialShipmentSerializer
        
        # Customers and agents get standard serializer
        return CustomerShipmentSerializer
    
    def perform_create(self, serializer):
        """
        Automatically set sender to current user when creating shipment
        """
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        POST /api/domestic/shipments/{id}/update-status/
        Update shipment status asynchronously
        
        Returns HTTP 202 Accepted (task queued)
        """
        shipment = self.get_object()
        serializer = StatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Queue async task
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
        GET /api/domestic/shipments/{id}/tracking/
        Get full tracking history for this shipment
        """
        shipment = self.get_object()
        logs = ShipmentLog.objects.filter(shipment=shipment).order_by('created_at')
        
        return Response({
            'tracking_code': shipment.tracking_code,
            'current_status': shipment.get_status_display(),
            'created_at': shipment.created_at,
            'picked_up_at': shipment.picked_up_at,
            'delivered_at': shipment.delivered_at,
            'history': ShipmentLogSerializer(logs, many=True).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request):
        """
        POST /api/domestic/shipments/batch-update/
        Update multiple shipments at once
        
        Body:
        {
            "tracking_codes": ["RW-260216-1234", "RW-260216-5678"],
            "status": "IN_TRANSIT",
            "location": "Nyabugogo Hub",
            "notes": "Loaded onto bus"
        }
        """
        serializer = BatchStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            tracking_codes = serializer.validated_data['tracking_codes']
            new_status = serializer.validated_data['status']
            
            # Get shipment IDs
            shipments = DomesticShipment.objects.filter(
                tracking_code__in=tracking_codes
            ).values_list('id', flat=True)
            
            if not shipments:
                return Response({
                    'error': 'No shipments found with provided tracking codes'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Queue async batch task
            task = batch_update_shipments_task.delay(
                shipment_ids=list(shipments),
                new_status=new_status,
                location=serializer.validated_data.get('location', ''),
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'message': f'Batch update processing for {len(shipments)} shipments',
                'task_id': task.id,
                'shipment_count': len(shipments)
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)