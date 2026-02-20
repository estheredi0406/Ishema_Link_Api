"""
Payment URLs
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('', views.PaymentViewSet.as_view({'get': 'list'}), name='payment-list'),
    path('<uuid:pk>/', views.PaymentViewSet.as_view({'get': 'retrieve'}), name='payment-detail'),
    path('initiate/', views.initiate_payment, name='initiate'),
    path('status/<str:transaction_ref>/', views.check_payment_status, name='status'),
    path('webhook/', views.payment_webhook, name='webhook'),
]