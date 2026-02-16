"""
Core app URL configuration
"""
from django.urls import path
from . import views

app_name = 'core'  # This is important for the namespace!

urlpatterns = [
    # System endpoints
    path('status/', views.health_check, name='health-check'),
    
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/verify-nid/', views.NIDVerificationView.as_view(), name='verify-nid'),
    
    # User profile
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
]