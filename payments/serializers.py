"""
Payment Serializers
"""
from rest_framework import serializers
from .models import Payment, PaymentWebhook


class PaymentInitiateSerializer(serializers.Serializer):
    """Initiate payment request"""
    shipment_id = serializers.IntegerField(required=True)
    payment_method = serializers.ChoiceField(
        choices=['MTN_MOMO', 'AIRTEL_MONEY', 'CASH'],
        default='MTN_MOMO'
    )
    phone_number = serializers.CharField(max_length=17, required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)


class PaymentSerializer(serializers.ModelSerializer):
    """Payment details"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_successful = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'transaction_ref', 'amount', 'payment_method',
            'phone_number', 'status', 'status_display', 'is_successful',
            'initiated_at', 'completed_at', 'shipment'
        ]
        read_only_fields = ['payment_id', 'transaction_ref', 'initiated_at']


class PaymentWebhookSerializer(serializers.Serializer):
    """Webhook callback from payment provider"""
    transaction_ref = serializers.CharField(required=True)
    status = serializers.ChoiceField(
        choices=['SUCCESSFUL', 'FAILED'],
        required=True
    )
    event = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)