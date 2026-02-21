"""
Notification Views
API for testing and broadcasting notifications
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from .models import Notification
from .services import NotificationService
from rest_framework import serializers


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'event', 'status',
            'recipient_phone', 'recipient_email', 'subject',
            'message', 'created_at', 'sent_at'
        ]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification ViewSet
    User can view their own notifications
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """User can only see their own notifications"""
        return Notification.objects.filter(
            user=self.request.user
        ) | Notification.objects.filter(
            recipient_phone=self.request.user.phone
        )


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'target': {'type': 'string', 'enum': ['all', 'drivers', 'customers']}
            }
        }
    },
    responses={200: {'type': 'object'}},
    tags=['Notifications']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def broadcast_notification(request):
    """
    POST /api/notifications/broadcast/
    
    Send notification to multiple users
    (Admin only)
    
    Body:
    {
        "message": "System maintenance in 1 hour",
        "target": "all"  // or "drivers", "customers"
    }
    """
    from core.models import User
    
    message = request.data.get('message')
    target = request.data.get('target', 'all')
    
    if not message:
        return Response({
            'error': 'Message is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get target users
    if target == 'drivers':
        users = User.objects.filter(user_type='DRIVER')
    elif target == 'customers':
        users = User.objects.filter(user_type='CUSTOMER')
    else:
        users = User.objects.filter(is_active=True)
    
    # Send notifications
    sent_count = 0
    failed_count = 0
    
    for user in users[:100]:  # Limit to 100 for safety
        result = NotificationService.send_sms(
            phone=user.phone,
            message=message,
            event='BROADCAST',
            metadata={'broadcast_target': target}
        )
        
        if result['success']:
            sent_count += 1
        else:
            failed_count += 1
    
    return Response({
        'message': 'Broadcast complete',
        'target': target,
        'total_users': users.count(),
        'sent': sent_count,
        'failed': failed_count
    }, status=status.HTTP_200_OK)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'phone': {'type': 'string'},
                'message': {'type': 'string'}
            }
        }
    },
    responses={200: {'type': 'object'}},
    tags=['Notifications']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_test_sms(request):
    """
    POST /api/notifications/test/sms/
    
    Send test SMS (Admin only)
    
    Body:
    {
        "phone": "+250788123456",
        "message": "Test message"
    }
    """
    phone = request.data.get('phone')
    message = request.data.get('message', 'Test SMS from IshemaLink')
    
    if not phone:
        return Response({
            'error': 'Phone number is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    result = NotificationService.send_sms(
        phone=phone,
        message=message,
        event='TEST',
        metadata={'test': True}
    )
    
    return Response(result, status=status.HTTP_200_OK)