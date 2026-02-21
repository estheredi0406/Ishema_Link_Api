"""
Booking Admin
"""
from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference', 'user', 'status', 'total_amount',
        'shipment', 'payment', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['booking_reference', 'user__phone']
    readonly_fields = ['booking_reference', 'created_at', 'confirmed_at', 'completed_at']