"""
Core Models
Shared models used across the application
this defines how user data is stored
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone 
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model for IshemaLink
    Supports three user types: Agent, Customer, Admin
    """
    
    USER_TYPE_CHOICES = [
        ('AGENT', 'Agent'),
        ('CUSTOMER', 'Customer'),
        ('ADMIN', 'Admin'),
    ]
    
    # Phone number with Rwanda format validator
    phone_regex = RegexValidator(
        regex=r'^\+250\s?7[0-9]{2}\s?[0-9]{3}\s?[0-9]{3}$',
        message="Phone number must be in format: +250 7XX XXX XXX"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        help_text="Rwanda phone number in format: +250 7XX XXX XXX"
    )
    date_joined = models.DateTimeField(default=timezone.now)
    # National ID - 16 digits
    national_id = models.CharField(
        max_length=16,
        unique=True,
        blank=True,
        null=True,
        help_text="16-digit Rwanda National ID"
    )
    
    # User type
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='CUSTOMER'
    )
    
    # For Agents - their assigned sector
    assigned_sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Sector where agent operates (e.g., 'Kicukiro/Niboye')"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Make email optional (not everyone has email in Rwanda)
    email = models.EmailField(blank=True, null=True)
    
    # Use phone as the unique identifier for login
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']  # Required for createsuperuser command
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone} ({self.get_user_type_display()})"
    
    @property
    def is_agent(self):
        """Check if user is an agent"""
        return self.user_type == 'AGENT'
    
    @property
    def is_customer(self):
        """Check if user is a customer"""
        return self.user_type == 'CUSTOMER'