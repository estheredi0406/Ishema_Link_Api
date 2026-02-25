"""
Maintenance Mode Middleware
"""
from django.http import JsonResponse
from django.core.cache import cache


class MaintenanceMiddleware:
    """
    Check if system is in maintenance mode
    Allows admin endpoints to pass through
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if in maintenance mode
        is_maintenance = cache.get('maintenance_mode', False)
        
        # Allow these paths even in maintenance
        allowed_paths = [
            '/api/ops/maintenance/',
            '/api/health/',
            '/admin/',
        ]
        
        if is_maintenance:
            # Allow admin and ops paths
            if any(request.path.startswith(path) for path in allowed_paths):
                return self.get_response(request)
            
            # Block all other requests
            return JsonResponse({
                'error': 'System is currently under maintenance',
                'maintenance_mode': True
            }, status=503)
        
        return self.get_response(request)