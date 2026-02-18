"""
Custom JWT Serializers
Adds extra claims to JWT tokens (user_type, phone, verification status)
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that adds user_type and other claims to token
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['user_type'] = user.user_type
        token['phone'] = user.phone
        token['is_verified'] = getattr(user, 'is_verified', False)
        token['assigned_sector'] = user.assigned_sector if user.user_type == 'AGENT' else None
        
        return token
    
    def validate(self, attrs):
        """Add extra data to response"""
        data = super().validate(attrs)
        
        # Add user info to response
        data['user'] = {
            'id': self.user.id,
            'phone': self.user.phone,
            'user_type': self.user.user_type,
            'username': self.user.username,
        }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom view using our custom serializer"""
    serializer_class = CustomTokenObtainPairSerializer