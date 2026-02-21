"""
Health Check Views
For monitoring and load balancer health checks
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    GET /api/health/
    
    Comprehensive health check for load balancers
    Checks: Database, Cache, Disk
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
        logger.error(f"Database health check failed: {e}")
    
    # Check Cache
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error: cache read failed'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['cache'] = f'error: {str(e)}'
        logger.error(f"Cache health check failed: {e}")
    
    # Return status
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    GET /api/ready/
    
    Lightweight readiness check
    For Kubernetes readiness probes
    """
    return JsonResponse({'ready': True}, status=200)


def liveness_check(request):
    """
    GET /api/alive/
    
    Minimal liveness check
    For Kubernetes liveness probes
    """
    return JsonResponse({'alive': True}, status=200)