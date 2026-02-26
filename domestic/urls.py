"""
Domestic Shipment URLs
"""
from django.urls import path
from . import views, government_views

app_name = 'domestic'

urlpatterns = [
    # 1. Shipment CRUD (List and Create)
    path('shipments/', views.DomesticShipmentViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='shipment-list'),

    # 2. Shipment CRUD (Detail, Update, Delete)
    path('shipments/<int:pk>/', views.DomesticShipmentViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='shipment-detail'),
    
    # 3. Custom Action: Update Status (single)
    path('shipments/<int:pk>/update-status/', views.DomesticShipmentViewSet.as_view({
        'post': 'update_status'
    }), name='shipment-update-status'),

    # 4. Custom Action: Tracking History
    path('shipments/<int:pk>/tracking/', views.DomesticShipmentViewSet.as_view({
        'get': 'tracking'
    }), name='shipment-tracking'),

    # 5. Custom Action: Batch Update (multiple)
    path('shipments/batch-update/', views.DomesticShipmentViewSet.as_view({
        'post': 'batch_update'
    }), name='shipment-batch-update'),
    
    # 6. Government portal
    path('gov/shipments/', government_views.gov_all_shipments, name='gov-shipments'),
    path('gov/statistics/', government_views.gov_statistics, name='gov-statistics'),
    path('gov/manifests/', government_views.gov_all_manifests, name='gov-manifests'),
]