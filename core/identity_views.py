"""
Identity & KYC Views
Handles phone verification, NID verification, and account recovery
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from .models import User
from .otp_service import OTPService
from .identity_serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    NIDVerificationSerializer,
    VerificationStatusSerializer,
    AccountRecoveryInitiateSerializer,
    AccountRecoveryConfirmSerializer
)


@extend_schema(
    request=SendOTPSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'expires_in': {'type': 'integer'},
                'otp': {'type': 'string', 'description': 'Only in development'}
            }
        }
    },
    tags=['Identity & KYC']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_otp(request):
    """
    POST /api/identity/send-otp/
    Send OTP to user's phone for verification
    """
    serializer = SendOTPSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    purpose = serializer.validated_data['purpose']
    
    # For verification, phone must match authenticated user
    if purpose == 'verification' and request.user.phone != phone:
        return Response({
            'error': 'Phone number does not match your account'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Send OTP
    result = OTPService.send_otp(phone, purpose)
    
    return Response(result, status=status.HTTP_200_OK)


@extend_schema(
    request=VerifyOTPSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'phone_verified': {'type': 'boolean'}
            }
        }
    },
    tags=['Identity & KYC']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    """
    POST /api/identity/verify-otp/
    Verify OTP code and mark phone as verified
    """
    serializer = VerifyOTPSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    otp = serializer.validated_data['otp']
    purpose = serializer.validated_data['purpose']
    
    # Verify phone matches user
    if request.user.phone != phone:
        return Response({
            'error': 'Phone number does not match your account'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify OTP
    result = OTPService.verify_otp(phone, otp, purpose)
    
    if not result['success']:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    # Mark phone as verified
    user = request.user
    user.phone_verified = True
    user.phone_verified_at = timezone.now()
    
    # Check if fully verified (phone + NID)
    if user.nid_verified and not user.is_verified:
        user.is_verified = True
        user.verified_at = timezone.now()
    
    user.save()
    
    return Response({
        'message': 'Phone verified successfully',
        'phone_verified': True,
        'fully_verified': user.is_verified
    }, status=status.HTTP_200_OK)


@extend_schema(
    request=NIDVerificationSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'nid_verified': {'type': 'boolean'}
            }
        }
    },
    tags=['Identity & KYC']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_nid(request):
    """
    POST /api/identity/verify-nid/
    Submit National ID for verification
    """
    serializer = NIDVerificationSerializer(
        data=request.data,
        context={'user_id': request.user.id}
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    national_id = serializer.validated_data['national_id']
    
    # Update user NID
    user = request.user
    user.national_id = national_id
    user.nid_verified = True
    user.nid_verified_at = timezone.now()
    
    # Check if fully verified (phone + NID)
    if user.phone_verified and not user.is_verified:
        user.is_verified = True
        user.verified_at = timezone.now()
    
    user.save()
    
    return Response({
        'message': 'National ID verified successfully',
        'nid_verified': True,
        'fully_verified': user.is_verified
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: VerificationStatusSerializer},
    tags=['Identity & KYC']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verification_status(request):
    """
    GET /api/identity/status/
    Get current user's verification status
    """
    serializer = VerificationStatusSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=AccountRecoveryInitiateSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'otp': {'type': 'string', 'description': 'Only in development'}
            }
        }
    },
    tags=['Identity & KYC']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def recovery_initiate(request):
    """
    POST /api/identity/recover/initiate/
    Start account recovery process - sends OTP to phone
    """
    serializer = AccountRecoveryInitiateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    
    # Send OTP
    result = OTPService.send_otp(phone, purpose='recovery')
    
    return Response({
        'message': 'Recovery OTP sent to your phone',
        'expires_in': result['expires_in'],
        'otp': result.get('otp')  # Only in development
    }, status=status.HTTP_200_OK)


@extend_schema(
    request=AccountRecoveryConfirmSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'}
            }
        }
    },
    tags=['Identity & KYC']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def recovery_confirm(request):
    """
    POST /api/identity/recover/confirm/
    Confirm recovery with OTP and reset password
    """
    serializer = AccountRecoveryConfirmSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    otp = serializer.validated_data['otp']
    new_password = serializer.validated_data['new_password']
    
    # Verify OTP
    result = OTPService.verify_otp(phone, otp, purpose='recovery')
    
    if not result['success']:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user
    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Reset password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password reset successfully. You can now login with your new password.'
    }, status=status.HTTP_200_OK)