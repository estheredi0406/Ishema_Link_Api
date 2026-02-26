# domestic/admin.py
from django.contrib import admin
from .models import DomesticShipment, TariffZone, DomesticTariff

# Existing shipment admin (keep it as is)
@admin.register(DomesticShipment)
class DomesticShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_code', 'sender', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['tracking_code', 'receiver_name']

# Simple Tariff Zone admin (no list_display issues)
@admin.register(TariffZone)
class TariffZoneAdmin(admin.ModelAdmin):
    pass  # Django will show all fields automatically

# Simple Domestic Tariff admin
@admin.register(DomesticTariff)
class DomesticTariffAdmin(admin.ModelAdmin):
    pass  # Django will show all fields automatically