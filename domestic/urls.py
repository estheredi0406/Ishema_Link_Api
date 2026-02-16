"""
Domestic app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'shipments', views.DomesticShipmentViewSet, basename='shipment')

app_name = 'domestic'

urlpatterns = [
    path('', include(router.urls)),
]