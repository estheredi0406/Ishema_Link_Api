"""
Core API Views
Handles system-wide endpoints like health checks and API root
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection


@api_view(['GET'])
@permission_classes([AllowAny])  # No authentication required
def health_check(request):
    """
    System health check endpoint
    Returns database connectivity status and basic system info
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return Response({
        "status": "healthy",
        "service": "IshemaLink API",
        "version": "1.0.0",
        "database": db_status,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint
    Provides information about available API endpoints
    """
    return Response({
        "message": "Welcome to IshemaLink API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/status/",
            "api_root": "/api/",
            "docs": "/api/docs/",
        }
    })