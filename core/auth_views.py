"""
Authentication Views for Hybrid Auth Strategy
Session Auth for Web Dashboard, JWT for Mobile Apps
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from .serializers import UserSerializer


class LoginRateThrottle(AnonRateThrottle):
    """Strict rate limiting for login endpoints - 5 per minute"""
    rate = '5/minute'
    
    def allow_request(self, request, view):
        print(f"\n🔍 === THROTTLE DEBUG ===")
        print(f"Rate: {self.rate}")
        print(f"Scope: {self.scope}")
        
        # Try to get cache key
        try:
            cache_key = self.get_cache_key(request, view)
            print(f"Cache key: {cache_key}")
        except Exception as e:
            print(f"Cache key error: {e}")
        
        result = super().allow_request(request, view)
        
        print(f"Allow request: {result}")
        
        try:
            wait = self.wait()
            print(f"Wait time: {wait}")
        except Exception as e:
            print(f"Wait time error: {e}")
            
        print(f"======================\n")
        
        return result


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'phone': {'type': 'string', 'example': '+250788123456'},
                'password': {'type': 'string', 'example': 'SecurePass123!'}
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'user': {'type': 'object'},
                'auth_method': {'type': 'string'}
            }
        },
        401: {'description': 'Invalid credentials'},
        429: {'description': 'Too many login attempts'}
    },
    tags=['Authentication']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def session_login(request):
    """
    POST /api/auth/login/session/
    Web dashboard login - creates session cookie
    
    Auto-logout when browser closes.
    Strict rate limiting: 5 attempts per minute.
    """
    phone = request.data.get('phone')
    password = request.data.get('password')
    
    if not phone or not password:
        return Response({
            'error': 'Phone and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate
    user = authenticate(request, username=phone, password=password)
    
    if user is None:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({
            'error': 'Account is disabled'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Create session
    login(request, user)
    
    return Response({
        'message': 'Login successful',
        'user': UserSerializer(user).data,
        'auth_method': 'session',
        'session_expiry': '8 hours'
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: {'description': 'Logged out successfully'}},
    tags=['Authentication']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    POST /api/auth/logout/
    Universal logout - works for both Session and JWT
    
    For JWT: Blacklists the refresh token
    For Session: Destroys the session
    """
    # If using JWT, blacklist the refresh token
    refresh_token = request.data.get('refresh_token')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass  # Token already blacklisted or invalid
    
    # Logout session (if exists)
    if request.user.is_authenticated:
        logout(request)
    
    return Response({
        'message': 'Logged out successfully'
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'phone': {'type': 'string'},
                'user_type': {'type': 'string'},
                'auth_method': {'type': 'string'}
            }
        }
    },
    tags=['Authentication']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whoami(request):
    """
    GET /api/auth/whoami/
    Returns current user details and authentication method
    """
    # Determine auth method
    auth_method = 'unknown'
    if hasattr(request, 'auth') and request.auth:
        auth_method = 'jwt'
    elif request.user.is_authenticated and hasattr(request, 'session'):
        auth_method = 'session'
    
    return Response({
        'user': UserSerializer(request.user).data,
        'auth_method': auth_method,
        'is_authenticated': request.user.is_authenticated
    }, status=status.HTTP_200_OK)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'old_password': {'type': 'string'},
                'new_password': {'type': 'string'},
                'new_password_confirm': {'type': 'string'}
            }
        }
    },
    responses={
        200: {'description': 'Password changed successfully'},
        400: {'description': 'Validation error'}
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change(request):
    """
    POST /api/auth/password/change/
    Change password for authenticated user
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')
    
    # Validate
    if not all([old_password, new_password, new_password_confirm]):
        return Response({
            'error': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(old_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != new_password_confirm:
        return Response({
            'error': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Change password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)