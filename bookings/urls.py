"""
Booking URLs
"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking list and detail
    path('', views.BookingViewSet.as_view({'get': 'list'}), name='booking-list'),
    path('<int:pk>/', views.BookingViewSet.as_view({'get': 'retrieve'}), name='booking-detail'),
    
    # Unified booking endpoints
    path('create/', views.create_unified_booking, name='create'),
    path('status/<str:booking_reference>/', views.get_booking_status, name='status'),
]