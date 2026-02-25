"""
Analytics API URLs
"""
from django.urls import path
from . import analytics_views

app_name = 'analytics'

urlpatterns = [
    path('routes/top/', analytics_views.top_routes, name='top-routes'),
    path('commodities/breakdown/', analytics_views.commodity_breakdown, name='commodity-breakdown'),
    path('revenue/heatmap/', analytics_views.revenue_heatmap, name='revenue-heatmap'),
    path('drivers/leaderboard/', analytics_views.driver_leaderboard, name='driver-leaderboard'),
]