"""
Prometheus Metrics & Operations Endpoints
For monitoring and observability
"""
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from drf_spectacular.utils import extend_schema
import psutil
import os

# Simple in-memory metrics storage
METRICS = {
    'requests_total': 0,
    'requests_by_endpoint': {},
    'response_times': [],
    'errors_total': 0,
}


@extend_schema(
    summary="Prometheus metrics endpoint",
    description="Returns metrics in Prometheus format for monitoring",
    tags=['Operations & Monitoring']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_metrics(request):
    """
    GET /api/ops/metrics/
    
    Prometheus-formatted metrics endpoint
    """
    metrics_output = []
    
    # Request metrics
    metrics_output.append(f"# HELP http_requests_total Total HTTP requests")
    metrics_output.append(f"# TYPE http_requests_total counter")
    metrics_output.append(f"http_requests_total {METRICS['requests_total']}")
    
    # Error metrics
    metrics_output.append(f"\n# HELP http_errors_total Total HTTP errors")
    metrics_output.append(f"# TYPE http_errors_total counter")
    metrics_output.append(f"http_errors_total {METRICS['errors_total']}")
    
    # Database connections
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            db_connections = cursor.fetchone()[0]
        
        metrics_output.append(f"\n# HELP database_connections Active database connections")
        metrics_output.append(f"# TYPE database_connections gauge")
        metrics_output.append(f"database_connections {db_connections}")
    except:
        pass
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics_output.append(f"\n# HELP system_cpu_percent CPU usage percentage")
    metrics_output.append(f"# TYPE system_cpu_percent gauge")
    metrics_output.append(f"system_cpu_percent {cpu_percent}")
    
    metrics_output.append(f"\n# HELP system_memory_percent Memory usage percentage")
    metrics_output.append(f"# TYPE system_memory_percent gauge")
    metrics_output.append(f"system_memory_percent {memory.percent}")
    
    metrics_output.append(f"\n# HELP system_disk_percent Disk usage percentage")
    metrics_output.append(f"# TYPE system_disk_percent gauge")
    metrics_output.append(f"system_disk_percent {disk.percent}")
    
    return HttpResponse('\n'.join(metrics_output), content_type='text/plain')


@extend_schema(
    summary="Deep health check with system metrics",
    description="Comprehensive health check including disk space, CPU, and memory",
    tags=['Operations & Monitoring']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def deep_health_check(request):
    """
    GET /api/health/deep/
    
    Comprehensive health check including disk space
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {},
        'system': {}
    }
    
    # Database check (SQLite & PostgreSQL compatible)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Get database size
        db_size = 0
        try:
            # Try PostgreSQL method first
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_database_size(current_database())")
                db_size = cursor.fetchone()[0]
        except:
            # Fallback for SQLite
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                db_path = str(settings.DATABASES['default']['NAME'])
                if os.path.exists(db_path):
                    db_size = os.path.getsize(db_path)
        
        health_status['checks']['database'] = {
            'status': 'ok',
            'size_bytes': db_size,
            'size_mb': round(db_size / 1024 / 1024, 2) if db_size else 0
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Cache check
    try:
        cache.set('health_deep_check', 'ok', 10)
        result = cache.get('health_deep_check')
        if result == 'ok':
            health_status['checks']['cache'] = {'status': 'ok'}
        else:
            health_status['checks']['cache'] = {'status': 'degraded'}
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['cache'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Disk space check
    try:
        disk = psutil.disk_usage('/')
        health_status['checks']['disk'] = {
            'status': 'ok' if disk.percent < 85 else 'warning',
            'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
            'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
            'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
            'percent_used': disk.percent
        }
        
        if disk.percent >= 95:
            health_status['status'] = 'critical'
        elif disk.percent >= 85:
            health_status['status'] = 'degraded'
            
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # System resources
    health_status['system'] = {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_percent': psutil.virtual_memory().percent,
        'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
    }
    
    # Return appropriate status code
    status_code = {
        'healthy': 200,
        'degraded': 200,
        'critical': 503,
        'unhealthy': 503
    }.get(health_status['status'], 200)
    
    return JsonResponse(health_status, status=status_code)


@extend_schema(
    summary="Toggle maintenance mode",
    description="Enable or disable system maintenance mode",
    tags=['Operations & Monitoring']
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def toggle_maintenance(request):
    """
    POST /api/ops/maintenance/toggle/
    
    Enable/disable maintenance mode
    """
    enabled = request.data.get('enabled', False)
    
    if enabled:
        cache.set('maintenance_mode', True, timeout=None)
        return JsonResponse({
            'maintenance_mode': True,
            'message': 'System is now in maintenance mode'
        })
    else:
        cache.delete('maintenance_mode')
        return JsonResponse({
            'maintenance_mode': False,
            'message': 'System is now operational'
        })


@extend_schema(
    summary="Check maintenance mode status",
    description="Returns whether system is currently in maintenance mode",
    tags=['Operations & Monitoring']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def check_maintenance(request):
    """
    GET /api/ops/maintenance/status/
    
    Check if system is in maintenance mode
    """
    is_maintenance = cache.get('maintenance_mode', False)
    
    if is_maintenance:
        return JsonResponse({
            'maintenance_mode': True,
            'message': 'System is currently under maintenance'
        }, status=503)
    
    return JsonResponse({
        'maintenance_mode': False,
        'message': 'System is operational'
    })