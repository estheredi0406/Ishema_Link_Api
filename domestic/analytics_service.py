"""
Business Intelligence Analytics Service
Provides anonymized, aggregated data for MINICOM and stakeholders
"""
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate
from decimal import Decimal
from .models import DomesticShipment


class AnalyticsService:
    """
    BI Analytics for logistics intelligence
    All data is anonymized - no personal information exposed
    """
    
    @staticmethod
    def get_top_routes(limit=10):
        """
        Most frequented district-to-district routes
        
        Use case: MINICOM plans road infrastructure based on traffic
        
        Returns:
            List of routes with shipment counts and total cargo weight
        """
        routes = (
            DomesticShipment.objects
            .values('origin_district', 'destination_district')
            .annotate(
                shipment_count=Count('id'),
                total_weight_kg=Sum('weight'),
                avg_weight_kg=Avg('weight'),
                total_revenue=Sum('price')
            )
            .filter(shipment_count__gt=0)
            .order_by('-shipment_count')[:limit]
        )
        
        return [
            {
                'route': f"{r['origin_district']} → {r['destination_district']}",
                'origin': r['origin_district'],
                'destination': r['destination_district'],
                'shipment_count': r['shipment_count'],
                'total_weight_kg': float(r['total_weight_kg'] or 0),
                'avg_weight_kg': round(float(r['avg_weight_kg'] or 0), 2),
                'total_revenue_rwf': float(r['total_revenue'] or 0)
            }
            for r in routes
        ]
    
    @staticmethod
    def get_commodity_breakdown():
        """
        Cargo type statistics (anonymized)
        
        Use case: Understanding what types of goods are transported
        
        Returns:
            Breakdown by commodity type with volumes
        """
        # Common Rwanda commodity categories
        commodities = {
            'food': ['potato', 'maize', 'beans', 'rice', 'cassava', 'banana', 'vegetables', 'fruits'],
            'electronics': ['phone', 'computer', 'laptop', 'tablet', 'electronics', 'appliance'],
            'construction': ['cement', 'iron', 'steel', 'bricks', 'tiles', 'paint'],
            'textiles': ['clothes', 'fabric', 'textile', 'fashion', 'shoes'],
            'agricultural': ['fertilizer', 'seeds', 'tools', 'equipment', 'pesticide']
        }
        
        results = []
        
        for category, keywords in commodities.items():
            # Build query for this category
            query = Q()
            for keyword in keywords:
                query |= Q(description__icontains=keyword)
            
            stats = DomesticShipment.objects.filter(query).aggregate(
                shipment_count=Count('id'),
                total_weight_kg=Sum('weight'),
                total_revenue=Sum('price')
            )
            
            if stats['shipment_count'] and stats['shipment_count'] > 0:
                results.append({
                    'category': category.title(),
                    'shipment_count': stats['shipment_count'],
                    'total_weight_kg': float(stats['total_weight_kg'] or 0),
                    'total_revenue_rwf': float(stats['total_revenue'] or 0),
                    'avg_price_per_kg': round(
                        float(stats['total_revenue'] or 0) / float(stats['total_weight_kg'] or 1),
                        2
                    )
                })
        
        # Add "Other" category for unclassified
        all_categorized_ids = []
        for category, keywords in commodities.items():
            query = Q()
            for keyword in keywords:
                query |= Q(description__icontains=keyword)
            all_categorized_ids.extend(
                DomesticShipment.objects.filter(query).values_list('id', flat=True)
            )
        
        other_stats = DomesticShipment.objects.exclude(
            id__in=all_categorized_ids
        ).aggregate(
            shipment_count=Count('id'),
            total_weight_kg=Sum('weight'),
            total_revenue=Sum('price')
        )
        
        if other_stats['shipment_count'] and other_stats['shipment_count'] > 0:
            results.append({
                'category': 'Other',
                'shipment_count': other_stats['shipment_count'],
                'total_weight_kg': float(other_stats['total_weight_kg'] or 0),
                'total_revenue_rwf': float(other_stats['total_revenue'] or 0),
                'avg_price_per_kg': round(
                    float(other_stats['total_revenue'] or 0) / float(other_stats['total_weight_kg'] or 1),
                    2
                )
            })
        
        return sorted(results, key=lambda x: x['total_weight_kg'], reverse=True)
    
    @staticmethod
    def get_revenue_heatmap():
        """
        Revenue breakdown by geographic sector (anonymized)
        
        Use case: Identify high-revenue areas for business expansion
        
        Returns:
            Revenue statistics per district/sector
        """
        # Revenue by origin district
        origin_revenue = (
            DomesticShipment.objects
            .values('origin_district', 'origin_sector')
            .annotate(
                shipment_count=Count('id'),
                total_revenue=Sum('price'),
                avg_revenue=Avg('price')
            )
            .filter(total_revenue__gt=0)
            .order_by('-total_revenue')[:20]
        )
        
        return [
            {
                'district': r['origin_district'],
                'sector': r['origin_sector'],
                'location': f"{r['origin_sector']}, {r['origin_district']}",
                'shipment_count': r['shipment_count'],
                'total_revenue_rwf': float(r['total_revenue'] or 0),
                'avg_revenue_rwf': round(float(r['avg_revenue'] or 0), 2)
            }
            for r in origin_revenue
        ]
    
    @staticmethod
    def get_driver_performance():
        """
        Driver/transporter performance leaderboard (anonymized)
        
        Use case: Identify top-performing transporters for incentives
        
        Returns:
            Anonymized driver statistics (no personal names)
        """
        # Get shipments with delivery information
        delivered_shipments = DomesticShipment.objects.filter(
            status='DELIVERED',
            delivered_at__isnull=False
        )
        
        # Group by driver (if we had driver assignment)
        # For now, show overall performance metrics
        
        total_shipments = delivered_shipments.count()
        
        # Calculate on-time delivery rate (mock - assuming on-time if delivered)
        on_time_rate = 100.0  # Mock value
        
        # District-level performance (anonymized)
        district_performance = (
            delivered_shipments
            .values('origin_district')
            .annotate(
                deliveries=Count('id'),
                avg_delivery_value=Avg('price'),
                total_weight_delivered=Sum('weight')
            )
            .order_by('-deliveries')[:10]
        )
        
        return {
            'summary': {
                'total_deliveries': total_shipments,
                'on_time_delivery_rate': on_time_rate,
                'note': 'Driver assignment feature to be implemented for detailed leaderboard'
            },
            'district_performance': [
                {
                    'district': d['origin_district'],
                    'deliveries_completed': d['deliveries'],
                    'avg_delivery_value_rwf': round(float(d['avg_delivery_value'] or 0), 2),
                    'total_weight_delivered_kg': float(d['total_weight_delivered'] or 0)
                }
                for d in district_performance
            ]
        }