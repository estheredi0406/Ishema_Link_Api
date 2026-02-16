"""
Core API Views
Handles system-wide endpoints like health checks, auth, and user management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView, GenericAPIView
from django.db import connection
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer,
    NIDVerificationSerializer
)
# Add these imports at the top
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
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
            "register": "/api/auth/register/",
            "verify_nid": "/api/auth/verify-nid/",
        }
    })


class UserRegistrationView(CreateAPIView):
    """
    POST /api/auth/register/
    Register a new user account
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class NIDVerificationView(GenericAPIView):
    """
    POST /api/auth/verify-nid/
    Verify National ID format
    """
    permission_classes = [AllowAny]
    serializer_class = NIDVerificationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                "valid": True,
                "nid": serializer.validated_data['nid'],
                "message": "Valid Rwanda National ID format"
            }, status=status.HTTP_200_OK)
        
        # Extract error message safely
        error_message = "Invalid NID format"
        if 'nid' in serializer.errors:
            error_message = serializer.errors['nid'][0]
        
        return Response({
            "valid": False,
            "error": error_message
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(RetrieveAPIView):
    """
    GET /api/users/me/
    Get current user profile
    """
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user