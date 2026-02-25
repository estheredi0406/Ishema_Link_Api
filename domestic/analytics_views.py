"""
Analytics API Endpoints
Business Intelligence for MINICOM and stakeholders
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .analytics_service import AnalyticsService


@extend_schema(
    summary="Top traffic routes",
    description="Most frequented district-to-district corridors for infrastructure planning",
    tags=['Analytics & BI']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_routes(request):
    """
    GET /api/analytics/routes/top/
    
    High-traffic corridors for MINICOM road planning
    
    Data is aggregated and anonymized - no personal information
    """
    limit = int(request.query_params.get('limit', 10))
    
    routes = AnalyticsService.get_top_routes(limit=limit)
    
    return Response({
        'success': True,
        'data': routes,
        'total_routes': len(routes),
        'use_case': 'Infrastructure planning - prioritize road maintenance/expansion',
        'privacy': 'Aggregated data - no personal information disclosed'
    })


@extend_schema(
    summary="Commodity breakdown statistics",
    description="Volume analysis by cargo type (Food vs Electronics vs Construction etc.)",
    tags=['Analytics & BI']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def commodity_breakdown(request):
    """
    GET /api/analytics/commodities/breakdown/
    
    Cargo type statistics for market analysis
    
    Categories: Food, Electronics, Construction, Textiles, Agricultural, Other
    """
    commodities = AnalyticsService.get_commodity_breakdown()
    
    total_weight = sum(c['total_weight_kg'] for c in commodities)
    total_revenue = sum(c['total_revenue_rwf'] for c in commodities)
    
    return Response({
        'success': True,
        'data': commodities,
        'summary': {
            'total_categories': len(commodities),
            'total_weight_kg': round(total_weight, 2),
            'total_revenue_rwf': round(total_revenue, 2)
        },
        'use_case': 'Market analysis - understand cargo mix and pricing',
        'privacy': 'Aggregated data - no individual shipments or senders identified'
    })


@extend_schema(
    summary="Revenue heatmap by location",
    description="Geospatial revenue data for business expansion planning",
    tags=['Analytics & BI']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenue_heatmap(request):
    """
    GET /api/analytics/revenue/heatmap/
    
    Revenue distribution across Rwanda districts/sectors
    
    Helps identify high-value areas for business expansion
    """
    heatmap = AnalyticsService.get_revenue_heatmap()
    
    total_revenue = sum(h['total_revenue_rwf'] for h in heatmap)
    
    return Response({
        'success': True,
        'data': heatmap,
        'summary': {
            'total_locations': len(heatmap),
            'total_revenue_rwf': round(total_revenue, 2)
        },
        'use_case': 'Business expansion - identify high-revenue areas',
        'privacy': 'Geographic aggregation - no customer personal data'
    })


@extend_schema(
    summary="Driver/transporter performance",
    description="Anonymized performance metrics for top transporters",
    tags=['Analytics & BI']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_leaderboard(request):
    """
    GET /api/analytics/drivers/leaderboard/
    
    Performance metrics for transporters (anonymized)
    
    Metrics: Delivery count, on-time rate, volume handled
    """
    performance = AnalyticsService.get_driver_performance()
    
    return Response({
        'success': True,
        'data': performance,
        'use_case': 'Transporter incentives and quality monitoring',
        'privacy': 'Fully anonymized - no driver personal information disclosed'
    })