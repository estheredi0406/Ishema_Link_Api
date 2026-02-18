"""
Core Serializers
Handles conversion between User models and JSON
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from .validators import validate_rwanda_phone, validate_rwanda_nid


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    Validates Rwanda phone and NID format
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'phone', 'national_id', 
            'user_type', 'assigned_sector', 'email',
            'password', 'password_confirm'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': False},
            'assigned_sector': {'required': False},
        }
    
    def validate_phone(self, value):
        """Validate Rwanda phone format"""
        is_valid, error_msg = validate_rwanda_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_national_id(self, value):
        """Validate Rwanda National ID format"""
        if value:  # NID is optional for some users
            is_valid, error_msg = validate_rwanda_nid(value)
            if not is_valid:
                raise serializers.ValidationError(error_msg)
        return value
    
    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user with hashed password"""
        # Remove password_confirm from data
        validated_data.pop('password_confirm')
        
        # Create user with hashed password
        user = User.objects.create_user(
            username=validated_data['username'],
            phone=validated_data['phone'],
            password=validated_data['password'],
            national_id=validated_data.get('national_id'),
            user_type=validated_data.get('user_type', 'CUSTOMER'),
            assigned_sector=validated_data.get('assigned_sector'),
            email=validated_data.get('email'),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'username', 'email', 
            'user_type', 'national_id', 'assigned_sector',
            'phone_verified', 'nid_verified', 'is_verified',
            'verification_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'phone_verified', 'nid_verified', 'is_verified', 
            'created_at', 'updated_at'
        ]
    
    def get_verification_status(self, obj):
        return obj.verification_status


class NIDVerificationSerializer(serializers.Serializer):
    """
    Serializer for standalone NID verification
    """
    nid = serializers.CharField(max_length=16, required=True)
    
    def validate_nid(self, value):
        """Validate NID format"""
        is_valid, error_msg = validate_rwanda_nid(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value