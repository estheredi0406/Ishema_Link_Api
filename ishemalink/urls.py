"""
IshemaLink API URL Configuration
Main routing file that includes all app URLs
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import api_root

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    
    # ... existing URLs ...
    path('api/notifications/', include('notifications.urls', namespace='notifications')),  # ADD THIS

    # API Root
    path('api/', api_root, name='api-root'),
    
    # Core endpoints (health check, auth, users)
    path('api/', include('core.urls', namespace='core')),
    
    # Domestic shipments  
    path('api/domestic/', include('domestic.urls', namespace='domestic')),  
    path('api/payments/', include('payments.urls', namespace='payments')),

    #Bookings
    path('api/bookings/', include('bookings.urls', namespace='bookings')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]