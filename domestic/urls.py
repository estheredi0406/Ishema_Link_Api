"""
Domestic app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import tariff_views
from . import manifest_views  # ADD THIS

router = DefaultRouter()
router.register(r'shipments', views.DomesticShipmentViewSet, basename='shipment')
router.register(r'manifests', manifest_views.ManifestViewSet, basename='manifest')  # ADD THIS

app_name = 'domestic'

urlpatterns = [
    path('', include(router.urls)),
    
    # Tariff endpoints
    path('tariff/calculate/', tariff_views.TariffCalculateView.as_view(), name='tariff-calculate'),
    path('tariff/clear-cache/', tariff_views.TariffCacheClearView.as_view(), name='tariff-clear-cache'),
]