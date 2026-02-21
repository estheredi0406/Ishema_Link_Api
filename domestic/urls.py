"""
Domestic Shipment URLs
"""
from django.urls import path
from . import views, government_views

app_name = 'domestic'

urlpatterns = [
    # Shipment CRUD
    path('shipments/', views.DomesticShipmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='shipment-list'),
    path('shipments/<int:pk>/', views.DomesticShipmentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='shipment-detail'),
    
    # Custom actions
    path('shipments/<int:pk>/update-status/', views.DomesticShipmentViewSet.as_view({'post': 'update_status'}), name='shipment-update-status'),
    path('shipments/<int:pk>/tracking/', views.DomesticShipmentViewSet.as_view({'get': 'tracking'}), name='shipment-tracking'),
    path('shipments/batch-update/', views.DomesticShipmentViewSet.as_view({'post': 'batch_update'}), name='shipment-batch-update'),
    
    # Government portal (correct function names!)
    path('gov/shipments/', government_views.gov_all_shipments, name='gov-shipments'),
    path('gov/statistics/', government_views.gov_statistics, name='gov-statistics'),
    path('gov/manifests/', government_views.gov_all_manifests, name='gov-manifests'),
]