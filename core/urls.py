"""
Core app URL configuration
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import auth_views
from .jwt_serializers import CustomTokenObtainPairView

app_name = 'core'

urlpatterns = [
    # System endpoints
    path('status/', views.health_check, name='health-check'),
    
    # Session Authentication (Web Dashboard)
    path('auth/login/session/', auth_views.session_login, name='session-login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    
    # JWT Authentication (Mobile Apps)
    path('auth/token/obtain/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Universal endpoints
    path('auth/whoami/', auth_views.whoami, name='whoami'),
    path('auth/password/change/', auth_views.password_change, name='password-change'),  # FIXED: Changed from .as_view() to function
    
    # User management
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/verify-nid/', views.NIDVerificationView.as_view(), name='verify-nid'),
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
]