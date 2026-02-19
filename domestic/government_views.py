"""
Government Portal Views
Read-only access for RURA/RRA officials
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from core.permissions import IsGovOfficial
from .models import DomesticShipment, Manifest
from .rbac_serializers import GovOfficialShipmentSerializer


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total_shipments': {'type': 'integer'},
                'shipments': {'type': 'array'}
            }
        }
    },
    tags=['Government Portal']
)
@api_view(['GET'])
@permission_classes([IsGovOfficial])
def gov_all_shipments(request):
    """
    GET /api/gov/shipments/
    Government Portal: View all shipments (read-only)
    
    Query params:
    - status: Filter by status
    - days: Show shipments from last N days (default: 30)
    - district: Filter by origin or destination district
    """
    # Get query params
    status_filter = request.query_params.get('status')
    days = int(request.query_params.get('days', 30))
    district = request.query_params.get('district')
    
    # Build query
    shipments = DomesticShipment.objects.all()
    
    if status_filter:
        shipments = shipments.filter(status=status_filter)
    
    if district:
        shipments = shipments.filter(
            models.Q(origin_district=district) |
            models.Q(destination_district=district)
        )
    
    # Filter by date
    cutoff_date = timezone.now() - timedelta(days=days)
    shipments = shipments.filter(created_at__gte=cutoff_date)
    
    # Order by most recent
    shipments = shipments.order_by('-created_at')[:100]  # Limit to 100
    
    # Serialize
    serializer = GovOfficialShipmentSerializer(shipments, many=True)
    
    return Response({
        'total_shipments': shipments.count(),
        'days': days,
        'shipments': serializer.data
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total_shipments': {'type': 'integer'},
                'total_revenue': {'type': 'number'},
                'by_status': {'type': 'object'},
                'by_district': {'type': 'array'}
            }
        }
    },
    tags=['Government Portal']
)
@api_view(['GET'])
@permission_classes([IsGovOfficial])
def gov_statistics(request):
    """
    GET /api/gov/statistics/
    Government Portal: Overall system statistics
    
    Query params:
    - days: Statistics for last N days (default: 30)
    """
    days = int(request.query_params.get('days', 30))
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Get shipments in time period
    shipments = DomesticShipment.objects.filter(created_at__gte=cutoff_date)
    
    # Overall stats
    total_shipments = shipments.count()
    total_revenue = shipments.aggregate(Sum('price'))['price__sum'] or 0
    avg_price = shipments.aggregate(Avg('price'))['price__avg'] or 0
    
    # By status
    by_status = {}
    for status_choice in DomesticShipment.STATUS_CHOICES:
        status_code = status_choice[0]
        count = shipments.filter(status=status_code).count()
        by_status[status_code] = {
            'label': status_choice[1],
            'count': count
        }
    
    # By district (top 10)
    by_district = shipments.values('origin_district').annotate(
        count=Count('id'),
        revenue=Sum('price')
    ).order_by('-count')[:10]
    
    # By transport mode
    by_transport = shipments.values('transport_mode').annotate(
        count=Count('id')
    )
    
    return Response({
        'period_days': days,
        'total_shipments': total_shipments,
        'total_revenue': float(total_revenue),
        'average_price': float(avg_price),
        'by_status': by_status,
        'by_district': list(by_district),
        'by_transport_mode': list(by_transport)
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total_manifests': {'type': 'integer'},
                'manifests': {'type': 'array'}
            }
        }
    },
    tags=['Government Portal']
)
@api_view(['GET'])
@permission_classes([IsGovOfficial])
def gov_all_manifests(request):
    """
    GET /api/gov/manifests/
    Government Portal: View all manifests (read-only)
    """
    # Get all manifests
    manifests = Manifest.objects.all().order_by('-created_at')[:50]
    
    manifest_data = []
    for manifest in manifests:
        manifest_data.append({
            'id': manifest.id,
            'manifest_number': manifest.manifest_number,
            'manifest_type': manifest.manifest_type,
            'status': manifest.status,
            'origin_district': manifest.origin_district,
            'destination_district': manifest.destination_district,
            'vehicle_number': manifest.vehicle_number,
            'driver_name': manifest.driver_name,
            'total_shipments': manifest.total_shipments,
            'total_weight': float(manifest.total_weight),
            'scheduled_departure': manifest.scheduled_departure,
            'created_at': manifest.created_at
        })
    
    return Response({
        'total_manifests': manifests.count(),
        'manifests': manifest_data
    }, status=status.HTTP_200_OK)


# Import models at the top
from django.db import models