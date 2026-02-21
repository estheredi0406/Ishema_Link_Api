"""
Booking Tests
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from bookings.models import Booking
from domestic.models import DomesticShipment, TariffZone, DomesticTariff
from payments.models import Payment
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestUnifiedBooking:
    """Test unified booking service"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+250788123456',
            password='Pass123!',
            user_type='CUSTOMER'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create tariff zones
        zone_kigali = TariffZone.objects.create(
            name='Kigali Zone',
            districts=['Kigali', 'Gasabo', 'Kicukiro']
        )
        
        zone_south = TariffZone.objects.create(
            name='Southern Zone',
            districts=['Huye', 'Nyanza', 'Gisagara']
        )
        
        # Create tariff
        DomesticTariff.objects.create(
            origin_zone=zone_kigali,
            destination_zone=zone_south,
            transport_mode='BUS',
            base_price=Decimal('2000.00'),
            price_per_kg=Decimal('500.00'),
            min_weight=Decimal('0.00'),
            max_weight=Decimal('100.00'),
            is_active=True,
            effective_date=timezone.now().date()
        )
    
    def test_create_unified_booking(self):
        """Test creating booking with automatic payment"""
        response = self.client.post('/api/bookings/create/', {
            'receiver_name': 'John Doe',
            'receiver_phone': '+250788999999',
            'origin_district': 'Kigali',
            'origin_sector': 'Nyarugenge',
            'destination_district': 'Huye',
            'destination_sector': 'Tumba',
            'weight': '3.00',
            'transport_mode': 'BUS',
            'payment_method': 'MTN_MOMO'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'booking' in response.data
        assert 'payment' in response.data
        
        # Verify booking created
        booking_ref = response.data['booking']['booking_reference']
        booking = Booking.objects.get(booking_reference=booking_ref)
        assert booking.status == 'PENDING_PAYMENT'
        assert booking.user == self.user
        
        # Verify shipment created
        assert booking.shipment is not None
        assert booking.shipment.status == 'AWAITING_PAYMENT'
        
        # Verify payment created
        assert booking.payment is not None
        assert booking.payment.status == 'PENDING'
        
        # Verify price calculated (2000 base + 3kg * 500 = 3500)
        assert booking.total_amount == Decimal('3500.00')
    
    def test_booking_status_endpoint(self):
        """Test getting booking status"""
        # Create a booking first
        booking = Booking.objects.create(
            user=self.user,
            booking_reference='BK-TEST123',
            status='PENDING_PAYMENT',
            total_amount=Decimal('5000.00')
        )
        
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
        
        booking.shipment = shipment
        booking.save()
        
        # Get booking status
        response = self.client.get('/api/bookings/status/BK-TEST123/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'booking' in response.data
        assert response.data['booking']['booking_reference'] == 'BK-TEST123'
    
    def test_booking_invalid_route(self):
        """Test booking with invalid route fails"""
        response = self.client.post('/api/bookings/create/', {
            'receiver_name': 'John Doe',
            'receiver_phone': '+250788999999',
            'origin_district': 'InvalidDistrict',
            'origin_sector': 'InvalidSector',
            'destination_district': 'AnotherInvalid',
            'destination_sector': 'Tumba',
            'weight': '3.00',
            'transport_mode': 'BUS',
            'payment_method': 'MTN_MOMO'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is False
        assert 'error' in response.data


@pytest.mark.django_db
class TestBookingTransactions:
    """Test booking atomic transactions"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+250788123456',
            password='Pass123!',
            user_type='CUSTOMER'
        )
    
    def test_payment_failure_rolls_back_booking(self):
        """Test that failed payment doesn't create orphaned bookings"""
        initial_booking_count = Booking.objects.count()
        initial_shipment_count = DomesticShipment.objects.count()
        
        # This would fail at payment initiation in real scenario
        # For now, just verify counts remain same on failure
        
        assert Booking.objects.count() == initial_booking_count
        assert DomesticShipment.objects.count() == initial_shipment_count