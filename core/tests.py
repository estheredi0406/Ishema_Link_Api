"""
Core App Tests
Tests for authentication, identity, and RBAC
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

User = get_user_model()


@pytest.mark.django_db
class TestAuthentication:
    """Test authentication endpoints"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user_data = {
            'phone': '+250788123456',
            'password': 'TestPass123!',
            'username': 'testuser'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post('/api/auth/token/obtain/', {
            'phone': self.user_data['phone'],
            'password': self.user_data['password']
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = self.client.post('/api/auth/token/obtain/', {
            'phone': self.user_data['phone'],
            'password': 'WrongPassword'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = self.client.post('/api/auth/token/obtain/', {
            'phone': '+250788999999',
            'password': 'SomePassword'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRBAC:
    """Test Role-Based Access Control"""
    
    def setup_method(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.customer = User.objects.create_user(
            phone='+250788111111',
            password='Pass123!',
            user_type='CUSTOMER'
        )
        
        self.driver = User.objects.create_user(
            phone='+250788222222',
            password='Pass123!',
            user_type='DRIVER'
        )
        
        self.admin = User.objects.create_user(
            phone='+250788333333',
            password='Pass123!',
            user_type='ADMIN',
            is_staff=True
        )
    
    def test_customer_can_access_own_data(self):
        """Test customer can access their own shipments"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/domestic/shipments/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_driver_no_pricing_access(self):
        """Test driver cannot see pricing information"""
        # This would require creating a shipment first
        # Testing the serializer logic instead
        from domestic.rbac_serializers import DriverShipmentSerializer
        
        serializer = DriverShipmentSerializer()
        fields = serializer.get_fields()
        
        assert 'price' not in fields
        assert 'sender_phone' not in fields
    
    def test_admin_dashboard_access(self):
        """Test admin can access dashboard"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/dashboard/summary/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_customer_cannot_access_admin_dashboard(self):
        """Test customer cannot access admin dashboard"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/admin/dashboard/summary/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user(self):
        """Test creating a basic user"""
        user = User.objects.create_user(
            phone='+250788123456',
            password='TestPass123!',
            username='testuser'
        )
        
        assert user.phone == '+250788123456'
        assert user.check_password('TestPass123!')
        assert user.is_active
        assert not user.is_staff
    
    def test_user_type_defaults_to_customer(self):
        """Test user type defaults to CUSTOMER"""
        user = User.objects.create_user(
            phone='+250788123456',
            password='TestPass123!'
        )
        
        assert user.user_type == 'CUSTOMER'
        assert user.is_customer
    
    def test_user_verification_status(self):
        """Test user verification logic"""
        user = User.objects.create_user(
            phone='+250788123456',
            password='TestPass123!'
        )
        
        # Initially not verified
        assert not user.is_verified
        
        # Verify phone
        user.phone_verified = True
        user.save()
        
        # Still not fully verified (needs NID)
        assert not user.is_verified
        
        # Verify NID
        user.national_id = '1234567890123456'
        user.nid_verified = True
        user.save()
        
        # Now fully verified
        assert user.is_verified