"""
RBAC Management Views
Manage roles and permissions
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from .models import User


@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'roles': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'value': {'type': 'string'},
                            'label': {'type': 'string'},
                            'description': {'type': 'string'}
                        }
                    }
                }
            }
        }
    },
    tags=['RBAC']
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_roles(request):
    """
    GET /api/rbac/roles/
    List all available roles in the system
    """
    roles = [
        {
            'value': 'CUSTOMER',
            'label': 'Customer',
            'description': 'Regular user who sends/receives packages',
            'permissions': [
                'Create shipments',
                'View own shipments',
                'Track packages',
                'View pricing'
            ]
        },
        {
            'value': 'AGENT',
            'label': 'Sector Agent',
            'description': 'Agent assigned to a specific sector',
            'permissions': [
                'View shipments in assigned sector',
                'Update shipment status',
                'Create manifests',
                'View pricing'
            ]
        },
        {
            'value': 'DRIVER',
            'label': 'Delivery Driver',
            'description': 'Driver who delivers packages',
            'permissions': [
                'View assigned shipments',
                'Update delivery status',
                'Cannot view pricing'
            ]
        },
        {
            'value': 'ADMIN',
            'label': 'Administrator',
            'description': 'Full system access',
            'permissions': [
                'All permissions',
                'Manage users',
                'View all data',
                'System configuration'
            ]
        },
        {
            'value': 'GOV_OFFICIAL',
            'label': 'Government Official',
            'description': 'RURA/RRA inspector - read-only access',
            'permissions': [
                'View all shipments (read-only)',
                'View all users (read-only)',
                'View financial data',
                'Cannot modify data'
            ]
        }
    ]
    
    return Response({'roles': roles}, status=status.HTTP_200_OK)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'user_id': {'type': 'integer'},
                'new_role': {'type': 'string', 'enum': ['CUSTOMER', 'AGENT', 'DRIVER', 'ADMIN', 'GOV_OFFICIAL']},
                'assigned_sector': {'type': 'string', 'description': 'Required for AGENT role'}
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'user': {'type': 'object'}
            }
        }
    },
    tags=['RBAC']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_role(request):
    """
    POST /api/rbac/assign/
    Assign or change a user's role
    
    Body:
    {
        "user_id": 2,
        "new_role": "AGENT",
        "assigned_sector": "Kicukiro/Niboye"  // Required for AGENT
    }
    """
    user_id = request.data.get('user_id')
    new_role = request.data.get('new_role')
    assigned_sector = request.data.get('assigned_sector')
    
    # Validate
    if not user_id or not new_role:
        return Response({
            'error': 'user_id and new_role are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    valid_roles = ['CUSTOMER', 'AGENT', 'DRIVER', 'ADMIN', 'GOV_OFFICIAL']
    if new_role not in valid_roles:
        return Response({
            'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if AGENT role requires sector
    if new_role == 'AGENT' and not assigned_sector:
        return Response({
            'error': 'assigned_sector is required for AGENT role'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update role
    old_role = user.user_type
    user.user_type = new_role
    
    if new_role == 'AGENT':
        user.assigned_sector = assigned_sector
    else:
        user.assigned_sector = None  # Clear sector for non-agents
    
    user.save()
    
    return Response({
        'message': f'User role changed from {old_role} to {new_role}',
        'user': {
            'id': user.id,
            'phone': user.phone,
            'user_type': user.user_type,
            'assigned_sector': user.assigned_sector
        }
    }, status=status.HTTP_200_OK)