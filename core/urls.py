"""
Core app URL configuration
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import auth_views
from . import identity_views
from . import admin_dashboard_views
from . import privacy_views
from . import rbac_views  # ADD THIS
from .jwt_serializers import CustomTokenObtainPairView
from . import health_views

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
    
    # Identity & KYC Endpoints
    path('identity/send-otp/', identity_views.send_otp, name='send-otp'),
    path('identity/verify-otp/', identity_views.verify_otp, name='verify-otp'),
    path('identity/verify-nid/', identity_views.verify_nid, name='identity-verify-nid'),
    path('identity/status/', identity_views.verification_status, name='verification-status'),
    path('identity/recover/initiate/', identity_views.recovery_initiate, name='recovery-initiate'),
    path('identity/recover/confirm/', identity_views.recovery_confirm, name='recovery-confirm'),
    
    # Privacy & GDPR Endpoints
    path('privacy/my-data/', privacy_views.export_my_data, name='my-data'),
    path('privacy/anonymize/', privacy_views.request_anonymization, name='anonymize'),
    path('privacy/consent-history/', privacy_views.my_consent_history, name='consent-history'),
    
    # Admin/Compliance
    path('compliance/audit-logs/', privacy_views.admin_audit_logs, name='audit-logs'),
    
    # RBAC ENDPOINTS (Task 4)
    
    # Role Management
    path('rbac/roles/', rbac_views.list_roles, name='list-roles'),
    path('rbac/assign/', rbac_views.assign_role, name='assign-role'),

    # Dashboard endpoints
    path('admin/dashboard/summary/', admin_dashboard_views.dashboard_summary, name='dashboard-summary'),
    path('admin/dashboard/active-shipments/', admin_dashboard_views.active_shipments, name='active-shipments'),
    path('admin/dashboard/revenue/', admin_dashboard_views.revenue_breakdown, name='revenue-breakdown'),
    path('admin/dashboard/health/', admin_dashboard_views.system_health, name='system-health'),


    path('health/', health_views.health_check, name='health-check'),
    path('ready/', health_views.readiness_check, name='readiness'),
    path('alive/', health_views.liveness_check, name='liveness'),

]