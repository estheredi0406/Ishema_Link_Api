"""
Admin configuration for core app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .audit_models import AuditLog, ConsentRecord, DataExportRequest, AnonymizationRequest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ['phone', 'username', 'user_type', 'is_verified', 'phone_verified', 'nid_verified']
    list_filter = ['user_type', 'is_verified', 'phone_verified', 'nid_verified']
    search_fields = ['phone', 'username', 'national_id']
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('username', 'email', 'national_id')}),
        ('User Type', {'fields': ('user_type', 'assigned_sector')}),
        ('Verification', {'fields': ('phone_verified', 'phone_verified_at', 'nid_verified', 'nid_verified_at', 'is_verified', 'verified_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit Log admin - Read only"""
    list_display = ['timestamp', 'user_phone', 'action', 'resource_type', 'resource_id', 'ip_address']
    list_filter = ['action', 'resource_type', 'timestamp']
    search_fields = ['user_phone', 'resource_type', 'ip_address']
    readonly_fields = ['user', 'user_phone', 'user_type', 'action', 'resource_type', 'resource_id', 'sensitive_fields', 'timestamp', 'ip_address', 'user_agent', 'reason', 'metadata']
    
    def has_add_permission(self, request):
        return False  # Cannot manually add audit logs
    
    def has_delete_permission(self, request, obj=None):
        return False  # Cannot delete audit logs (compliance requirement)


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """Consent tracking admin"""
    list_display = ['user', 'consent_type', 'version', 'consented_at', 'revoked']
    list_filter = ['consent_type', 'revoked', 'consented_at']
    search_fields = ['user__phone']


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    """Data export requests admin"""
    list_display = ['user', 'status', 'requested_at', 'completed_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['user__phone']


@admin.register(AnonymizationRequest)
class AnonymizationRequestAdmin(admin.ModelAdmin):
    """Anonymization requests admin"""
    list_display = ['user', 'status', 'requested_at', 'processed_at', 'reviewed_by']
    list_filter = ['status', 'requested_at']
    search_fields = ['user__phone']