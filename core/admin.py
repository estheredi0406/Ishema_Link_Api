"""
Django Admin Configuration for Core App
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model
    """
    # Fields to display in the user list
    list_display = ['phone', 'username', 'user_type', 'assigned_sector', 'is_staff', 'is_active']
    list_filter = ['user_type', 'is_staff', 'is_active', 'created_at']
    search_fields = ['phone', 'username', 'national_id', 'email']
    
    # Fields when viewing/editing a user
    fieldsets = (
        ('Authentication', {
            'fields': ('phone', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': ('email', 'national_id', 'user_type', 'assigned_sector')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    # Fields when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'username', 'password1', 'password2', 'user_type'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    ordering = ['-created_at']