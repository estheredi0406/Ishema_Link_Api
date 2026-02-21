"""
Admin Dashboard Views
Control Tower for system monitoring
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from domestic.models import DomesticShipment, Manifest
from payments.models import Payment
from bookings.models import Booking
from core.models import User


@extend_schema(
    responses={200: {'type': 'object'}},
    tags=['Admin Dashboard']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_summary(request):
    """
    GET /api/admin/dashboard/summary/
    
    Real-time dashboard summary
    Shows current system status at a glance
    """
    # Time filters
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Shipment statistics
    total_shipments = DomesticShipment.objects.count()
    active_shipments = DomesticShipment.objects.filter(
        status__in=['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'AT_HUB', 'OUT_FOR_DELIVERY']
    ).count()
    delivered_today = DomesticShipment.objects.filter(
        status='DELIVERED',
        delivered_at__date=today
    ).count()
    
    # Revenue statistics
    total_revenue = Payment.objects.filter(
        status='SUCCESSFUL'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    revenue_today = Payment.objects.filter(
        status='SUCCESSFUL',
        completed_at__date=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    revenue_last_7_days = Payment.objects.filter(
        status='SUCCESSFUL',
        completed_at__gte=last_7_days
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    revenue_last_30_days = Payment.objects.filter(
        status='SUCCESSFUL',
        completed_at__gte=last_30_days
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Payment statistics
    pending_payments = Payment.objects.filter(
        status__in=['PENDING', 'PROCESSING']
    ).count()
    
    successful_payments = Payment.objects.filter(
        status='SUCCESSFUL'
    ).count()
    
    failed_payments = Payment.objects.filter(
        status='FAILED'
    ).count()
    
    # Booking statistics
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(
        status='PENDING_PAYMENT'
    ).count()
    
    # User statistics
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    new_users_today = User.objects.filter(
        created_at__date=today
    ).count()
    
    # Active manifests
    active_manifests = Manifest.objects.filter(
        status__in=['DRAFT', 'READY', 'IN_TRANSIT']
    ).count()
    
    return Response({
        'timestamp': timezone.now().isoformat(),
        'shipments': {
            'total': total_shipments,
            'active': active_shipments,
            'delivered_today': delivered_today,
            'by_status': DomesticShipment.objects.values('status').annotate(
                count=Count('id')
            )
        },
        'revenue': {
            'total': float(total_revenue),
            'today': float(revenue_today),
            'last_7_days': float(revenue_last_7_days),
            'last_30_days': float(revenue_last_30_days),
            'currency': 'RWF'
        },
        'payments': {
            'pending': pending_payments,
            'successful': successful_payments,
            'failed': failed_payments,
            'success_rate': round((successful_payments / (successful_payments + failed_payments) * 100), 2) if (successful_payments + failed_payments) > 0 else 0
        },
        'bookings': {
            'total': total_bookings,
            'pending_payment': pending_bookings
        },
        'users': {
            'total': total_users,
            'verified': verified_users,
            'new_today': new_users_today,
            'verification_rate': round((verified_users / total_users * 100), 2) if total_users > 0 else 0
        },
        'manifests': {
            'active': active_manifests
        }
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: {'type': 'object'}},
    tags=['Admin Dashboard']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def active_shipments(request):
    """
    GET /api/admin/dashboard/active-shipments/
    
    List all active shipments (in transit, pending delivery)
    """
    shipments = DomesticShipment.objects.filter(
        status__in=['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'AT_HUB', 'OUT_FOR_DELIVERY']
    ).select_related('sender').order_by('-created_at')[:50]
    
    shipment_data = []
    for shipment in shipments:
        shipment_data.append({
            'tracking_code': shipment.tracking_code,
            'status': shipment.status,
            'status_display': shipment.get_status_display(),
            'sender_phone': shipment.sender.phone,
            'receiver_name': shipment.receiver_name,
            'receiver_phone': shipment.receiver_phone,
            'origin': f"{shipment.origin_sector}, {shipment.origin_district}",
            'destination': f"{shipment.destination_sector}, {shipment.destination_district}",
            'weight': float(shipment.weight),
            'price': float(shipment.price),
            'transport_mode': shipment.transport_mode,
            'created_at': shipment.created_at.isoformat(),
            'days_in_transit': (timezone.now() - shipment.created_at).days
        })
    
    return Response({
        'total_active': len(shipment_data),
        'shipments': shipment_data
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: {'type': 'object'}},
    tags=['Admin Dashboard']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def revenue_breakdown(request):
    """
    GET /api/admin/dashboard/revenue/
    
    Revenue breakdown by transport mode, district, time period
    """
    # Get query params
    days = int(request.query_params.get('days', 30))
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Revenue by transport mode
    by_transport = DomesticShipment.objects.filter(
        created_at__gte=cutoff_date,
        payments__status='SUCCESSFUL'
    ).values('transport_mode').annotate(
        total_shipments=Count('id'),
        total_revenue=Sum('price')
    ).order_by('-total_revenue')
    
    # Revenue by origin district
    by_district = DomesticShipment.objects.filter(
        created_at__gte=cutoff_date,
        payments__status='SUCCESSFUL'
    ).values('origin_district').annotate(
        total_shipments=Count('id'),
        total_revenue=Sum('price')
    ).order_by('-total_revenue')[:10]
    
    # Revenue trend (daily for last N days)
    daily_revenue = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        revenue = Payment.objects.filter(
            status='SUCCESSFUL',
            completed_at__date=date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        daily_revenue.append({
            'date': date.isoformat(),
            'revenue': float(revenue)
        })
    
    return Response({
        'period_days': days,
        'by_transport_mode': list(by_transport),
        'by_district': list(by_district),
        'daily_trend': daily_revenue[::-1]  # Reverse to show oldest first
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: {'type': 'object'}},
    tags=['Admin Dashboard']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_health(request):
    """
    GET /api/admin/dashboard/health/
    
    System health check
    Shows potential issues requiring attention
    """
    # Stale shipments (in transit > 3 days)
    stale_shipments = DomesticShipment.objects.filter(
        status__in=['IN_TRANSIT', 'AT_HUB'],
        created_at__lt=timezone.now() - timedelta(days=3)
    ).count()
    
    # Failed payments (last 24 hours)
    failed_payments_24h = Payment.objects.filter(
        status='FAILED',
        initiated_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Pending payments (> 1 hour old)
    pending_payments_old = Payment.objects.filter(
        status__in=['PENDING', 'PROCESSING'],
        initiated_at__lt=timezone.now() - timedelta(hours=1)
    ).count()
    
    # Unverified users with shipments
    unverified_with_shipments = DomesticShipment.objects.filter(
        sender__is_verified=False
    ).count()
    
    # System status
    issues = []
    if stale_shipments > 0:
        issues.append({
            'type': 'warning',
            'message': f'{stale_shipments} shipments have been in transit for more than 3 days'
        })
    
    if failed_payments_24h > 10:
        issues.append({
            'type': 'error',
            'message': f'{failed_payments_24h} payment failures in the last 24 hours'
        })
    
    if pending_payments_old > 5:
        issues.append({
            'type': 'warning',
            'message': f'{pending_payments_old} payments pending for over 1 hour'
        })
    
    if unverified_with_shipments > 0:
        issues.append({
            'type': 'info',
            'message': f'{unverified_with_shipments} shipments from unverified users'
        })
    
    return Response({
        'status': 'healthy' if len(issues) == 0 else 'degraded',
        'issues': issues,
        'metrics': {
            'stale_shipments': stale_shipments,
            'failed_payments_24h': failed_payments_24h,
            'pending_payments_old': pending_payments_old,
            'unverified_with_shipments': unverified_with_shipments
        },
        'checked_at': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)