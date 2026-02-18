"""
Audit Middleware - The "Glass Log"
Automatically logs all access to sensitive endpoints
"""
import logging
from django.utils import timezone
from django.urls import resolve
from .audit_models import AuditLog

logger = logging.getLogger(__name__)


class AuditMiddleware:
    """
    Middleware that logs access to sensitive resources
    Creates audit trail for compliance with Rwanda Data Protection Law
    """
    
    # Endpoints that should be audited
    AUDITED_ENDPOINTS = [
        'shipment-detail',  # Viewing shipment details
        'user-profile',  # Viewing user profile
        'verification-status',  # Checking verification status
        'manifest-detail',  # Viewing manifest
        'my-data',  # Data export
    ]
    
    # Fields considered sensitive
    SENSITIVE_FIELDS = [
        'national_id',
        'phone',
        'email',
        'tax_id',
        'receiver_phone',
        'sender_phone',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only audit after successful responses
        if response.status_code == 200 and request.user.is_authenticated:
            self.log_access(request, response)
        
        return response
    
    def log_access(self, request, response):
        """
        Log access to sensitive data
        """
        try:
            # Get the URL name
            resolver_match = resolve(request.path_info)
            url_name = resolver_match.url_name
            
            # Check if this endpoint should be audited
            if url_name not in self.AUDITED_ENDPOINTS:
                return
            
            # Determine resource type and ID
            resource_type = self.get_resource_type(url_name)
            resource_id = resolver_match.kwargs.get('pk') or resolver_match.kwargs.get('id')
            
            # Get client IP
            ip_address = self.get_client_ip(request)
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                user_phone=request.user.phone,
                user_type=request.user.user_type,
                action='VIEW',
                resource_type=resource_type,
                resource_id=resource_id,
                sensitive_fields=self.SENSITIVE_FIELDS,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                metadata={
                    'method': request.method,
                    'path': request.path,
                    'url_name': url_name,
                }
            )
            
            logger.info(f"📝 Audit: {request.user.phone} viewed {resource_type} {resource_id}")
            
        except Exception as e:
            # Don't break the request if audit logging fails
            logger.error(f"Audit logging failed: {e}")
    
    def get_resource_type(self, url_name):
        """Map URL name to resource type"""
        mapping = {
            'shipment-detail': 'shipment',
            'user-profile': 'user',
            'verification-status': 'verification',
            'manifest-detail': 'manifest',
            'my-data': 'data_export',
        }
        return mapping.get(url_name, 'unknown')
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip