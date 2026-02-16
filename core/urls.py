"""
Core app URL configuration
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'core'

urlpatterns = [
    # System endpoints
    path('status/', views.health_check, name='health-check'),
    
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/verify-nid/', views.NIDVerificationView.as_view(), name='verify-nid'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # ADD THIS
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # ADD THIS
    
    # User profile
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
]