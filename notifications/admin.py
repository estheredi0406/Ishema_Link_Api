"""
Notification Admin
"""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'notification_type', 'event', 'status',
        'recipient_phone', 'recipient_email', 'created_at', 'sent_at'
    ]
    list_filter = ['notification_type', 'event', 'status', 'created_at']
    search_fields = ['recipient_phone', 'recipient_email', 'message', 'external_id']
    readonly_fields = [
        'created_at', 'sent_at', 'delivered_at', 'failed_at',
        'provider_response', 'external_id'
    ]
    
    def has_add_permission(self, request):
        """Notifications are created by the system, not manually"""
        return False