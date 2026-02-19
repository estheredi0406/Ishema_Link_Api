"""
Domestic app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import tariff_views
from . import manifest_views
from . import government_views  # ADD THIS

router = DefaultRouter()
router.register(r'shipments', views.DomesticShipmentViewSet, basename='shipment')
router.register(r'manifests', manifest_views.ManifestViewSet, basename='manifest')

app_name = 'domestic'

urlpatterns = [
    path('', include(router.urls)),
    
    # Tariff endpoints
    path('tariff/calculate/', tariff_views.TariffCalculateView.as_view(), name='tariff-calculate'),
    path('tariff/clear-cache/', tariff_views.TariffCacheClearView.as_view(), name='tariff-clear-cache'),
    
    # ========================================================================
    # GOVERNMENT PORTAL (Task 4)
    # ========================================================================
    
    # Government Read-Only Access
    path('gov/shipments/', government_views.gov_all_shipments, name='gov-shipments'),
    path('gov/statistics/', government_views.gov_statistics, name='gov-statistics'),
    path('gov/manifests/', government_views.gov_all_manifests, name='gov-manifests'),
]