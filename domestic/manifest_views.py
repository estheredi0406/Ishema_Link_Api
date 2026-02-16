"""
Manifest Views with Advanced Pagination
Demonstrates efficient handling of large datasets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Manifest, DomesticShipment
from .manifest_serializers import (
    ManifestListSerializer,
    ManifestDetailSerializer,
    ManifestCreateSerializer,
    ManifestShipmentSerializer,
    AddShipmentsSerializer
)


class ManifestShipmentPagination(PageNumberPagination):
    """
    Custom pagination for manifest shipments
    Larger page size since shipments are lightweight
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class ManifestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing manifests with pagination
    """
    queryset = Manifest.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'manifest_type', 'origin_district', 'destination_district']
    search_fields = ['manifest_number', 'vehicle_number', 'driver_name']
    ordering_fields = ['created_at', 'scheduled_departure', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return ManifestListSerializer
        elif self.action == 'create':
            return ManifestCreateSerializer
        return ManifestDetailSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'], url_path='shipments')
    def shipments(self, request, pk=None):
        """
        GET /api/domestic/manifests/{id}/shipments/
        Get paginated list of shipments in this manifest
        
        Query params:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 100)
        - status: Filter by shipment status
        - search: Search by tracking code or receiver name
        """
        manifest = self.get_object()
        
        # Get shipments queryset
        shipments = manifest.shipments.all()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            shipments = shipments.filter(status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            shipments = shipments.filter(
                tracking_code__icontains=search
            ) | shipments.filter(
                receiver_name__icontains=search
            )
        
        # Order by created_at
        shipments = shipments.order_by('-created_at')
        
        # Paginate
        paginator = ManifestShipmentPagination()
        page = paginator.paginate_queryset(shipments, request)
        
        if page is not None:
            serializer = ManifestShipmentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ManifestShipmentSerializer(shipments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='add-shipments')
    def add_shipments(self, request, pk=None):
        """
        POST /api/domestic/manifests/{id}/add-shipments/
        Add shipments to this manifest
        
        Body:
        {
            "shipment_ids": [1, 2, 3, 4, 5]
        }
        """
        manifest = self.get_object()
        serializer = AddShipmentsSerializer(data=request.data)
        
        if serializer.is_valid():
            shipment_ids = serializer.validated_data['shipment_ids']
            
            # Get valid shipments
            shipments = DomesticShipment.objects.filter(id__in=shipment_ids)
            
            if not shipments.exists():
                return Response({
                    'error': 'No valid shipments found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Add to manifest
            manifest.shipments.add(*shipments)
            
            return Response({
                'message': f'Added {shipments.count()} shipments to manifest',
                'manifest_number': manifest.manifest_number,
                'total_shipments': manifest.total_shipments
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='remove-shipments')
    def remove_shipments(self, request, pk=None):
        """
        POST /api/domestic/manifests/{id}/remove-shipments/
        Remove shipments from this manifest
        """
        manifest = self.get_object()
        serializer = AddShipmentsSerializer(data=request.data)
        
        if serializer.is_valid():
            shipment_ids = serializer.validated_data['shipment_ids']
            
            # Remove from manifest
            manifest.shipments.remove(*shipment_ids)
            
            return Response({
                'message': f'Removed shipments from manifest',
                'manifest_number': manifest.manifest_number,
                'total_shipments': manifest.total_shipments
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        POST /api/domestic/manifests/{id}/update-status/
        Update manifest status
        
        Body:
        {
            "status": "IN_TRANSIT"
        }
        """
        manifest = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Manifest.STATUS_CHOICES):
            return Response({
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        manifest.status = new_status
        manifest.save()
        
        return Response({
            'message': 'Manifest status updated',
            'manifest_number': manifest.manifest_number,
            'status': manifest.get_status_display()
        }, status=status.HTTP_200_OK)