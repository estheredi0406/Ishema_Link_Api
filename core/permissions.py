"""
Custom Permission Classes
Implements granular access control for IshemaLink
"""
from rest_framework import permissions


class IsSectorAgent(permissions.BasePermission):
    """
    Permission: Only sector agents can access
    Agents can only see data from their assigned sector
    """
    
    def has_permission(self, request, view):
        """Check if user is an agent"""
        return request.user and request.user.is_authenticated and request.user.is_agent
    
    def has_object_permission(self, request, view, obj):
        """Check if agent is assigned to this sector"""
        # For shipments, check origin or destination sector
        if hasattr(obj, 'origin_sector'):
            return (
                obj.origin_sector == request.user.assigned_sector or
                obj.destination_sector == request.user.assigned_sector
            )
        return True


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission: Owner has full access, others read-only
    Used for shipments (sender can edit, others can only view)
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        return False


class IsShipmentOwner(permissions.BasePermission):
    """
    Permission: User must be the sender or receiver of the shipment
    Customers can only see their own shipments
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin and gov officials can see all
        if request.user.user_type in ['ADMIN', 'GOV_OFFICIAL']:
            return True
        
        # Agents can see shipments in their sector
        if request.user.is_agent:
            return (
                obj.origin_sector == request.user.assigned_sector or
                obj.destination_sector == request.user.assigned_sector
            )
        
        # Drivers can see shipments assigned to them
        if request.user.is_driver:
            # Check if shipment is in a manifest assigned to this driver
            # For now, allow if driver needs to deliver
            return True  # We'll refine this later
        
        # Customers can only see their own shipments
        if hasattr(obj, 'sender'):
            return obj.sender == request.user or obj.receiver_phone == request.user.phone
        
        return False


class IsGovOfficial(permissions.BasePermission):
    """
    Permission: Government officials (RURA, RRA) - Read-only access to everything
    """
    
    def has_permission(self, request, view):
        """Allow gov officials"""
        return request.user and request.user.is_authenticated and request.user.is_gov_official
    
    def has_object_permission(self, request, view, obj):
        """Gov officials have read-only access"""
        # Only allow safe methods (GET, HEAD, OPTIONS)
        return request.method in permissions.SAFE_METHODS


class IsAdminOrGovReadOnly(permissions.BasePermission):
    """
    Permission: Admins have full access, Gov officials have read-only
    """
    
    def has_permission(self, request, view):
        """Check user type"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins have full access
        if request.user.user_type == 'ADMIN':
            return True
        
        # Gov officials have read-only access
        if request.user.is_gov_official:
            return request.method in permissions.SAFE_METHODS
        
        return False


class CanViewFinancialData(permissions.BasePermission):
    """
    Permission: Only specific roles can view financial data (price, revenue)
    Drivers CANNOT see pricing information
    """
    
    def has_permission(self, request, view):
        """Check if user can see financial data"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin, gov officials, and customers can see financial data
        allowed_types = ['ADMIN', 'GOV_OFFICIAL', 'CUSTOMER', 'AGENT']
        return request.user.user_type in allowed_types