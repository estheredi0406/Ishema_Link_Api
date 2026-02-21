"""
Payment Tests
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from domestic.models import DomesticShipment
from payments.models import Payment
from payments.momo_service import MobileMoneyService

User = get_user_model()


@pytest.mark.django_db
class TestPaymentFlow:
    """Test complete payment flow"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+250788123456',
            password='Pass123!',
            user_type='CUSTOMER'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a shipment
        self.shipment = DomesticShipment.objects.create(
            sender=self.user,
            sender_phone=self.user.phone,
            receiver_name='Test Receiver',
            receiver_phone='+250788999999',
            delivery_address='Test Address',
            origin_district='Kigali',
            origin_sector='Nyarugenge',
            destination_district='Huye',
            destination_sector='Tumba',
            weight=Decimal('5.00'),
            price=Decimal('5000.00'),
            transport_mode='BUS',
            status='AWAITING_PAYMENT'
        )
    
    def test_payment_initiation(self):
        """Test payment initiation"""
        response = self.client.post('/api/payments/initiate/', {
            'shipment_id': self.shipment.id,
            'payment_method': 'MTN_MOMO',
            'phone_number': '+250788123456',
            'amount': '5000.00'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'transaction_ref' in response.data
        assert 'payment_id' in response.data
        
        # Verify payment record created
        payment = Payment.objects.get(
            transaction_ref=response.data['transaction_ref']
        )
        assert payment.status == 'PENDING'
        assert payment.amount == Decimal('5000.00')
    
    def test_payment_wrong_amount(self):
        """Test payment with wrong amount fails"""
        response = self.client.post('/api/payments/initiate/', {
            'shipment_id': self.shipment.id,
            'payment_method': 'MTN_MOMO',
            'phone_number': '+250788123456',
            'amount': '3000.00'  # Wrong amount
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_payment_webhook_success(self):
        """Test successful payment webhook"""
        # Create payment
        payment = Payment.objects.create(
            user=self.user,
            shipment=self.shipment,
            transaction_ref='TEST-123',
            amount=Decimal('5000.00'),
            payment_method='MTN_MOMO',
            phone_number='+250788123456',
            status='PENDING'
        )
        
        # Send webhook
        response = self.client.post('/api/payments/webhook/', {
            'transaction_ref': 'TEST-123',
            'status': 'SUCCESSFUL',
            'event': 'payment.completed'
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify payment updated
        payment.refresh_from_db()
        assert payment.status == 'SUCCESSFUL'
        
        # Verify shipment activated
        self.shipment.refresh_from_db()
        assert self.shipment.status == 'PENDING'


@pytest.mark.django_db
class TestMobileMoneyService:
    """Test Mobile Money service"""
    
    def test_payment_initiation_returns_transaction_ref(self):
        """Test MoMo service returns transaction reference"""
        result = MobileMoneyService.initiate_payment(
            phone='+250788123456',
            amount=5000.00,
            payment_method='MTN_MOMO'
        )
        
        assert result['success'] is True
        assert 'transaction_ref' in result
        assert result['transaction_ref'].startswith('MM-')
    
    def test_payment_status_check(self):
        """Test checking payment status"""
        result = MobileMoneyService.check_payment_status('MM-TEST123')
        
        assert 'status' in result
        assert result['status'] in ['SUCCESSFUL', 'PENDING', 'FAILED']