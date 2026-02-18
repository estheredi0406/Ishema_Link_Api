"""
Core app URL configuration
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import auth_views
from . import identity_views  # ADD THIS
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
    path('auth/password/change/', auth_views.password_change, name='password-change'),
    
    # User management
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/verify-nid/', views.NIDVerificationView.as_view(), name='verify-nid'),
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
    
    # ========================================================================
    # IDENTITY & KYC ENDPOINTS (Task 2)
    # ========================================================================
    
    # Phone Verification
    path('identity/send-otp/', identity_views.send_otp, name='send-otp'),
    path('identity/verify-otp/', identity_views.verify_otp, name='verify-otp'),
    
    # NID Verification
    path('identity/verify-nid/', identity_views.verify_nid, name='identity-verify-nid'),
    
    # Verification Status
    path('identity/status/', identity_views.verification_status, name='verification-status'),
    
    # Account Recovery
    path('identity/recover/initiate/', identity_views.recovery_initiate, name='recovery-initiate'),
    path('identity/recover/confirm/', identity_views.recovery_confirm, name='recovery-confirm'),
]