"""
Privacy & GDPR Compliance Views
Handles data export, anonymization, and consent tracking
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from .models import User
from .audit_models import AuditLog, ConsentRecord, DataExportRequest, AnonymizationRequest
from domestic.models import DomesticShipment


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'user_data': {'type': 'object'},
                'shipments': {'type': 'array'},
                'audit_logs': {'type': 'array'},
                'consent_records': {'type': 'array'}
            }
        }
    },
    tags=['Privacy & GDPR']
)
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_my_data(request):
    """
    GET /api/privacy/my-data/
    GDPR Right to Data Portability
    
    Export all data IshemaLink holds about the user
    Returns comprehensive JSON with all user information
    """
    user = request.user
    
    # User profile data
    user_data = {
        'personal_information': {
            'phone': user.phone,
            'email': user.email,
            'username': user.username,
            'national_id': user.national_id,  # Will be decrypted if encrypted
            'user_type': user.user_type,
            'assigned_sector': user.assigned_sector,
        },
        'verification_status': {
            'phone_verified': user.phone_verified,
            'phone_verified_at': user.phone_verified_at.isoformat() if user.phone_verified_at else None,
            'nid_verified': user.nid_verified,
            'nid_verified_at': user.nid_verified_at.isoformat() if user.nid_verified_at else None,
            'is_verified': user.is_verified,
            'verified_at': user.verified_at.isoformat() if user.verified_at else None,
        },
        'account_info': {
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
    }
    
    # Shipments (as sender)
    shipments_sent = DomesticShipment.objects.filter(sender=user).values(
        'id', 'tracking_code', 'status', 'receiver_name', 'receiver_phone',
        'origin_district', 'destination_district', 'weight', 'price',
        'created_at', 'delivered_at'
    )
    
    # Audit logs (who accessed my data)
    audit_logs = AuditLog.objects.filter(user=user).values(
        'action', 'resource_type', 'resource_id', 'timestamp', 'ip_address'
    )[:50]  # Last 50 accesses
    
    # Consent records
    consent_records = ConsentRecord.objects.filter(user=user).values(
        'consent_type', 'version', 'consented_at', 'revoked'
    )
    
    # Compile export
    export_data = {
        'export_date': timezone.now().isoformat(),
        'user_id': user.id,
        'user_data': user_data,
        'shipments_sent': list(shipments_sent),
        'audit_logs': list(audit_logs),
        'consent_records': list(consent_records),
        'data_retention_info': {
            'shipment_data': '7 years (Rwanda tax law)',
            'audit_logs': '5 years (compliance requirement)',
            'personal_data': 'Until account deletion or 2 years of inactivity'
        }
    }
    
    # Create export request record
    DataExportRequest.objects.create(
        user=user,
        status='COMPLETED',
        completed_at=timezone.now(),
        export_data=export_data,
        ip_address=get_client_ip(request)
    )
    
    return Response(export_data, status=status.HTTP_200_OK)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'reason': {'type': 'string'}
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'request_id': {'type': 'integer'}
            }
        }
    },
    tags=['Privacy & GDPR']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_anonymization(request):
    """
    POST /api/privacy/anonymize/
    GDPR Right to be Forgotten
    
    Request account deletion/anonymization
    Admin must review and approve before processing
    
    Body:
    {
        "reason": "I no longer use this service"
    }
    """
    user = request.user
    reason = request.data.get('reason', '')
    
    # Check if user has pending shipments
    pending_shipments = DomesticShipment.objects.filter(
        sender=user,
        status__in=['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'AT_HUB', 'OUT_FOR_DELIVERY']
    ).count()
    
    if pending_shipments > 0:
        return Response({
            'error': f'Cannot anonymize account with {pending_shipments} pending shipments. Please wait for delivery or cancel them.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create anonymization request
    anonymization_request = AnonymizationRequest.objects.create(
        user=user,
        reason=reason,
        status='PENDING'
    )
    
    return Response({
        'message': 'Anonymization request submitted. An admin will review your request within 30 days.',
        'request_id': anonymization_request.id,
        'status': 'PENDING',
        'note': 'Your data will be anonymized after admin approval. Shipment history will be retained (anonymized) for 7 years as required by Rwanda tax law.'
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total_logs': {'type': 'integer'},
                'logs': {'type': 'array'}
            }
        }
    },
    tags=['Privacy & GDPR']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_audit_logs(request):
    """
    GET /api/compliance/audit-logs/
    Admin-only: View all audit logs
    
    Query params:
    - user_phone: Filter by user phone
    - resource_type: Filter by resource type
    - action: Filter by action
    - days: Show logs from last N days (default: 7)
    """
    from datetime import timedelta
    
    # Get query params
    user_phone = request.query_params.get('user_phone')
    resource_type = request.query_params.get('resource_type')
    action = request.query_params.get('action')
    days = int(request.query_params.get('days', 7))
    
    # Build query
    logs = AuditLog.objects.all()
    
    if user_phone:
        logs = logs.filter(user_phone=user_phone)
    if resource_type:
        logs = logs.filter(resource_type=resource_type)
    if action:
        logs = logs.filter(action=action)
    
    # Filter by date
    cutoff_date = timezone.now() - timedelta(days=days)
    logs = logs.filter(timestamp__gte=cutoff_date)
    
    # Limit to 100 results
    logs = logs[:100]
    
    # Serialize
    log_data = logs.values(
        'id', 'user_phone', 'user_type', 'action', 'resource_type',
        'resource_id', 'timestamp', 'ip_address', 'reason'
    )
    
    return Response({
        'total_logs': logs.count(),
        'days': days,
        'logs': list(log_data)
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'consent_type': {'type': 'string'},
                    'version': {'type': 'string'},
                    'consented_at': {'type': 'string'}
                }
            }
        }
    },
    tags=['Privacy & GDPR']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_consent_history(request):
    """
    GET /api/privacy/consent-history/
    View your consent history (Terms of Service versions agreed to)
    """
    user = request.user
    
    consents = ConsentRecord.objects.filter(user=user).values(
        'consent_type', 'version', 'consented_at', 'revoked', 'revoked_at'
    )
    
    return Response(list(consents), status=status.HTTP_200_OK)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip