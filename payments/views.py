"""
Payment API Views
Handles payment initiation, status checks, and webhooks
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from .models import Payment, PaymentWebhook
from .serializers import (
    PaymentInitiateSerializer,
    PaymentSerializer,
    PaymentWebhookSerializer
)
from .momo_service import MobileMoneyService
from domestic.models import DomesticShipment
from notifications.services import NotificationService  # ADD THIS
import logging

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payment ViewSet
    List and retrieve user's payments
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        """User can only see their own payments"""
        return Payment.objects.filter(user=self.request.user)


@extend_schema(
    request=PaymentInitiateSerializer,
    responses={
        200: PaymentSerializer,
        400: {'description': 'Invalid request'}
    },
    tags=['Payments']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    POST /api/payments/initiate/
    Initiate Mobile Money payment for shipment
    
    Flow:
    1. Validate shipment exists and belongs to user
    2. Create payment record
    3. Call Mobile Money provider API
    4. Return transaction reference
    
    Body:
    {
        "shipment_id": 1,
        "payment_method": "MTN_MOMO",
        "phone_number": "+250788123456",
        "amount": 5000.00
    }
    """
    serializer = PaymentInitiateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    shipment_id = serializer.validated_data['shipment_id']
    payment_method = serializer.validated_data['payment_method']
    phone_number = serializer.validated_data['phone_number']
    amount = serializer.validated_data['amount']
    
    # Validate shipment
    try:
        shipment = DomesticShipment.objects.get(id=shipment_id)
    except DomesticShipment.DoesNotExist:
        return Response({
            'error': 'Shipment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check shipment belongs to user
    if shipment.sender != request.user:
        return Response({
            'error': 'You do not own this shipment'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if shipment already paid
    if shipment.payments.filter(status='SUCCESSFUL').exists():
        return Response({
            'error': 'Shipment already paid'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate amount matches shipment price
    if float(amount) != float(shipment.price):
        return Response({
            'error': f'Amount must be {shipment.price} RWF'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Initiate payment with Mobile Money provider
    try:
        momo_response = MobileMoneyService.initiate_payment(
            phone=phone_number,
            amount=float(amount),
            payment_method=payment_method
        )
        
        if not momo_response['success']:
            return Response({
                'error': 'Failed to initiate payment with provider'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            shipment=shipment,
            transaction_ref=momo_response['transaction_ref'],
            amount=amount,
            payment_method=payment_method,
            phone_number=phone_number,
            status='PENDING',
            provider_response=momo_response,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        logger.info(f"💳 Payment initiated: {payment.transaction_ref} for shipment {shipment.tracking_code}")
        
        return Response({
            'payment_id': str(payment.payment_id),
            'transaction_ref': payment.transaction_ref,
            'status': payment.status,
            'message': momo_response['message'],
            'amount': float(payment.amount),
            'shipment_tracking_code': shipment.tracking_code
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        return Response({
            'error': 'Payment initiation failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={
        200: PaymentSerializer,
        404: {'description': 'Payment not found'}
    },
    tags=['Payments']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_payment_status(request, transaction_ref):
    """
    GET /api/payments/status/{transaction_ref}/
    Check payment status with provider
    """
    try:
        payment = Payment.objects.get(
            transaction_ref=transaction_ref,
            user=request.user
        )
    except Payment.DoesNotExist:
        return Response({
            'error': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # If already completed, return current status
    if payment.status in ['SUCCESSFUL', 'FAILED', 'CANCELLED']:
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
    
    # Check with provider
    provider_status = MobileMoneyService.check_payment_status(transaction_ref)
    
    # Update payment status
    old_status = payment.status
    payment.status = provider_status['status']
    
    if payment.status == 'SUCCESSFUL':
        payment.completed_at = timezone.now()
        
        # Update shipment status
        if payment.shipment:
            payment.shipment.status = 'PENDING'  # Ready for pickup
            payment.shipment.save()
            
            # Send notification
            NotificationService.notify_payment_success(payment)
    
    elif payment.status == 'FAILED':
        payment.failed_at = timezone.now()
    
    payment.save()
    
    if old_status != payment.status:
        logger.info(f"💳 Payment status updated: {transaction_ref} → {payment.status}")
    
    return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


@extend_schema(
    request=PaymentWebhookSerializer,
    responses={
        200: {'description': 'Webhook processed'},
        400: {'description': 'Invalid webhook'}
    },
    tags=['Payments']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # Webhooks come from external provider
def payment_webhook(request):
    """
    POST /api/payments/webhook/
    Receive payment status webhook from Mobile Money provider
    
    This endpoint is called by MTN/Airtel servers when payment completes
    
    Body:
    {
        "transaction_ref": "MM-ABC123",
        "status": "SUCCESSFUL",
        "event": "payment.completed",
        "data": {...}
    }
    """
    serializer = PaymentWebhookSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.warning(f"Invalid webhook payload: {request.data}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    transaction_ref = serializer.validated_data['transaction_ref']
    webhook_status = serializer.validated_data['status']
    
    # Log webhook
    webhook = PaymentWebhook.objects.create(
        provider=request.data.get('provider', 'UNKNOWN'),
        event_type=request.data.get('event', 'payment.update'),
        payload=request.data
    )
    
    try:
        # Find payment
        payment = Payment.objects.get(transaction_ref=transaction_ref)
        webhook.payment = payment
        webhook.save()
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            old_status = payment.status
            payment.status = webhook_status
            payment.provider_response = request.data
            
            if webhook_status == 'SUCCESSFUL':
                payment.completed_at = timezone.now()
                
                # Update shipment - CRITICAL: Payment confirms booking
                if payment.shipment:
                    payment.shipment.status = 'PENDING'
                    payment.shipment.save()
                    
                    logger.info(f"✅ Payment successful: {transaction_ref}")
                    logger.info(f"   Shipment {payment.shipment.tracking_code} activated")
                    
                    # Send success notification
                    NotificationService.notify_payment_success(payment)
            
            elif webhook_status == 'FAILED':
                payment.failed_at = timezone.now()
                
                # Rollback: Cancel shipment if payment fails
                if payment.shipment:
                    payment.shipment.status = 'CANCELLED'
                    payment.shipment.save()
                    
                    logger.warning(f"❌ Payment failed: {transaction_ref}")
                    logger.warning(f"   Shipment {payment.shipment.tracking_code} cancelled")
            
            payment.save()
            
            # Mark webhook as processed
            webhook.processed = True
            webhook.processed_at = timezone.now()
            webhook.save()
        
        return Response({
            'message': 'Webhook processed successfully',
            'transaction_ref': transaction_ref,
            'status': payment.status
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for webhook: {transaction_ref}")
        return Response({
            'error': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return Response({
            'error': 'Webhook processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip