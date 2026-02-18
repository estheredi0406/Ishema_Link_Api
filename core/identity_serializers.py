"""
Identity & KYC Serializers
Handles user verification, OTP, and KYC workflows
"""
from rest_framework import serializers
from .models import User
from .validators import validate_rwanda_phone, validate_rwanda_nid


class SendOTPSerializer(serializers.Serializer):
    """Request OTP for phone verification"""
    phone = serializers.CharField(max_length=17)
    purpose = serializers.ChoiceField(
        choices=['verification', 'recovery'],
        default='verification'
    )
    
    def validate_phone(self, value):
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Verify OTP code"""
    phone = serializers.CharField(max_length=17)
    otp = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(
        choices=['verification', 'recovery'],
        default='verification'
    )


class NIDVerificationSerializer(serializers.Serializer):
    """Submit NID for verification"""
    national_id = serializers.CharField(max_length=16, required=True)
    
    def validate_national_id(self, value):
        is_valid, error_msg = validate_rwanda_nid(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        
        # Check if NID is already in use
        user_id = self.context.get('user_id')
        if User.objects.filter(national_id=value).exclude(id=user_id).exists():
            raise serializers.ValidationError("This National ID is already registered")
        
        return value


class VerificationStatusSerializer(serializers.ModelSerializer):
    """Show user's verification status"""
    verification_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'email',
            'phone_verified', 'phone_verified_at',
            'nid_verified', 'nid_verified_at', 'national_id',
            'is_verified', 'verified_at',
            'verification_summary'
        ]
    
    def get_verification_summary(self, obj):
        return obj.verification_status


class AccountRecoveryInitiateSerializer(serializers.Serializer):
    """Initiate account recovery"""
    phone = serializers.CharField(max_length=17)
    
    def validate_phone(self, value):
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        
        # Check if user exists
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("No account found with this phone number")
        
        return value


class AccountRecoveryConfirmSerializer(serializers.Serializer):
    """Confirm recovery and reset password"""
    phone = serializers.CharField(max_length=17)
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    new_password_confirm = serializers.CharField(min_length=8, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password': 'Passwords do not match'
            })
        return attrs