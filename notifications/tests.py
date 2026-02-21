"""
Notification Tests
"""
import pytest
from django.contrib.auth import get_user_model
from notifications.models import Notification
from notifications.services import NotificationService
from bookings.models import Booking
from payments.models import Payment
from domestic.models import DomesticShipment
from decimal import Decimal

User = get_user_model()


@pytest.mark.django_db
class TestNotificationService:
    """Test notification service"""
    
    def setup_method(self):
        self.user = User.objects.create_user(
            phone='+250788123456',
            password='Pass123!',
            user_type='CUSTOMER'
        )
    
    def test_send_sms_creates_notification(self):
        """Test sending SMS creates notification record"""
        result = NotificationService.send_sms(
            phone='+250788123456',
            message='Test message',
            event='TEST'
        )
        
        assert result['success'] is True
        assert 'notification_id' in result
        
        # Verify notification created
        notification = Notification.objects.get(id=result['notification_id'])
        assert notification.recipient_phone == '+250788123456'
        assert notification.message == 'Test message'
        assert notification.status == 'SENT'
        assert notification.event == 'TEST'
    
    def test_booking_notification(self):
        """Test booking created notification"""
        shipment = DomesticShipment.objects.create(
            sender=self.user,
            sender_phone=self.user.phone,
            receiver_name='Test',
            receiver_phone='+250788999999',
            delivery_address='Test',
            origin_district='Kigali',
            origin_sector='Nyarugenge',
            destination_district='Huye',
            destination_sector='Tumba',
            weight=Decimal('5.00'),
            price=Decimal('5000.00'),
            transport_mode='BUS',
            status='AWAITING_PAYMENT'
        )
        
        booking = Booking.objects.create(
            user=self.user,
            shipment=shipment,
            booking_reference='BK-TEST123',
            status='PENDING_PAYMENT',
            total_amount=Decimal('5000.00')
        )
        
        result = NotificationService.notify_booking_created(booking)
        
        assert result['success'] is True
        
        # Verify notification
        notification = Notification.objects.get(
            event='BOOKING_CREATED',
            recipient_phone=self.user.phone
        )
        assert 'BK-TEST123' in notification.message
    
    def test_payment_success_notification(self):
        """Test payment success notification"""
        shipment = DomesticShipment.objects.create(
            sender=self.user,
            sender_phone=self.user.phone,
            receiver_name='Test',
            receiver_phone='+250788999999',
            delivery_address='Test',
            origin_district='Kigali',
            origin_sector='Nyarugenge',
            destination_district='Huye',
            destination_sector='Tumba',
            weight=Decimal('5.00'),
            price=Decimal('5000.00'),
            transport_mode='BUS'
        )
        
        payment = Payment.objects.create(
            user=self.user,
            shipment=shipment,
            transaction_ref='TEST-123',
            amount=Decimal('5000.00'),
            payment_method='MTN_MOMO',
            phone_number='+250788123456',
            status='SUCCESSFUL'
        )
        
        result = NotificationService.notify_payment_success(payment)
        
        assert result['success'] is True
        
        # Verify notification
        notification = Notification.objects.get(
            event='PAYMENT_SUCCESS',
            recipient_phone='+250788123456'
        )
        assert 'confirmed' in notification.message.lower()
        assert '5000.00' in notification.message or '5000' in notification.message


@pytest.mark.django_db
class TestNotificationAPI:
    """Test notification API endpoints"""
    
    def setup_method(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+250788123456',
            password='Pass123!',
            user_type='CUSTOMER'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_user_notifications(self):
        """Test user can see their notifications"""
        # Create some notifications
        Notification.objects.create(
            recipient_phone=self.user.phone,
            notification_type='SMS',
            event='TEST',
            message='Test message',
            status='SENT'
        )
        
        response = self.client.get('/api/notifications/')
        
        assert response.status_code == 200
        assert len(response.data) >= 1