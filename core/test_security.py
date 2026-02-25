"""
Security Tests
Tests RBAC, authentication bypass attempts
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from domestic.models import DomesticShipment
from decimal import Decimal

User = get_user_model()


@pytest.mark.django_db
class TestRBACSecur:
    """Test Role-Based Access Control Security"""
    
    def test_customer_cannot_access_admin_endpoints(self):
        """Customers should not access admin-only endpoints"""
        client = APIClient()
        
        # Create customer user
        customer = User.objects.create_user(
            phone='+250788111111',
            password='CustomerPass123!',
            user_type='CUSTOMER',
            username='test_customer'
        )
        
        client.force_authenticate(user=customer)
        
        # Try to access admin dashboard (should fail)
        response = client.get('/api/core/admin/dashboard/summary/')
        assert response.status_code in [403, 404]  # Accept both forbidden or not found
    
    def test_user_cannot_view_other_users_shipments(self):
        """Users should only see their own shipments (privacy test)"""
        
        client = APIClient()
        
        # Create two users
        user1 = User.objects.create_user(
            phone='+250788222222',
            password='User1Pass123!',
            user_type='CUSTOMER',
            username='user1'
        )
        
        user2 = User.objects.create_user(
            phone='+250788333333',
            password='User2Pass123!',
            user_type='CUSTOMER',
            username='user2'
        )
        
        # User 1 creates a shipment
        shipment = DomesticShipment.objects.create(
            sender=user1,
            receiver_name='Receiver',
            receiver_phone='+250788444444',
            origin_district='KIGALI',
            origin_sector='GASABO',
            destination_district='HUYE',
            destination_sector='NGOMA',
            pickup_address='Gasabo, Kigali',
            delivery_address='Ngoma, Huye',
            description='Test item',
            weight=Decimal('10.00'),
            transport_mode='MOTORCYCLE',
            price=Decimal('5000.00')
        )
        
        # User 2 tries to access User 1's shipment
        client.force_authenticate(user=user2)
        response = client.get(f'/api/domestic/shipments/{shipment.id}/')
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestAuthenticationSecurity:
    """Test authentication security"""
    
    def test_unauthenticated_access_blocked(self):
        """Unauthenticated requests should be blocked"""
        client = APIClient()
        
        # Try to access protected endpoint without token
        response = client.get('/api/domestic/shipments/')
        assert response.status_code in [401, 403]  # Accept both unauthorized or forbidden
    
    def test_invalid_token_rejected(self):
        """Invalid tokens should be rejected"""
        client = APIClient()
        
        # Use fake token
        client.credentials(HTTP_AUTHORIZATION='Bearer FAKE_TOKEN_12345')
        response = client.get('/api/domestic/shipments/')
        assert response.status_code in [401, 403]  # Accept both