"""
Notification URLs
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification list
    path('', views.NotificationViewSet.as_view({'get': 'list'}), name='notification-list'),
    path('<int:pk>/', views.NotificationViewSet.as_view({'get': 'retrieve'}), name='notification-detail'),
    
    # Admin actions
    path('broadcast/', views.broadcast_notification, name='broadcast'),
    path('test/sms/', views.send_test_sms, name='test-sms'),
]