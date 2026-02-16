"""
Tariff Calculation Service with Redis Caching
Calculates shipping prices based on weight, zones, and transport mode
"""
import hashlib
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.utils import timezone
from .models import DomesticTariff, TariffZone

logger = logging.getLogger(__name__)


class TariffService:
    """
    Service for calculating tariffs with intelligent caching
    """
    
    CACHE_PREFIX = "tariff"
    CACHE_TTL = 60 * 60 * 24 * 7  # 7 days
    
    @staticmethod
    def _generate_cache_key(
        weight: Decimal,
        origin_district: str,
        destination_district: str,
        transport_mode: str
    ) -> str:
        """
        Generate unique cache key for tariff calculation
        """
        key_string = f"{weight}:{origin_district}:{destination_district}:{transport_mode}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{TariffService.CACHE_PREFIX}:{key_hash}"
    
    @staticmethod
    def get_zone_for_district(district: str) -> Optional[TariffZone]:
        """
        Get tariff zone for a district (with caching)
        Works with SQLite - uses Python iteration instead of JSONField __contains
        """
        cache_key = f"zone:{district}"
        
        # Try cache first
        zone = cache.get(cache_key)
        if zone is not None:
            logger.info(f"✅ Cache HIT: Zone for {district}")
            return zone
        
        # Cache miss - query database
        logger.info(f"❌ Cache MISS: Querying zone for {district}")
        
        try:
            # Iterate through zones (SQLite-compatible approach)
            for zone in TariffZone.objects.all():
                if district in zone.districts:
                    # Cache for 30 days
                    cache.set(cache_key, zone, timeout=60 * 60 * 24 * 30)
                    return zone
            
            logger.warning(f"No zone found for district: {district}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding zone: {e}")
            return None
    
    @staticmethod
    def calculate_tariff(
        weight: Decimal,
        origin_district: str,
        destination_district: str,
        transport_mode: str
    ) -> Dict[str, Any]:
        """
        Calculate tariff with intelligent caching
        """
        # Generate cache key
        cache_key = TariffService._generate_cache_key(
            weight, origin_district, destination_district, transport_mode
        )
        
        # Try cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"✅ Cache HIT: Tariff calculation")
            cached_result['cache_hit'] = True
            return cached_result
        
        # Cache miss - calculate tariff
        logger.info(f"❌ Cache MISS: Calculating tariff")
        
        # Get zones
        origin_zone = TariffService.get_zone_for_district(origin_district)
        destination_zone = TariffService.get_zone_for_district(destination_district)
        
        if not origin_zone or not destination_zone:
            return {
                'success': False,
                'error': 'Invalid district - zone not found',
                'cache_hit': False
            }
        
        # Find applicable tariff
        try:
            tariff = DomesticTariff.objects.get(
                origin_zone=origin_zone,
                destination_zone=destination_zone,
                transport_mode=transport_mode,
                min_weight__lte=weight,
                max_weight__gte=weight,
                is_active=True,
                effective_date__lte=timezone.now().date()
            )
        except DomesticTariff.DoesNotExist:
            return {
                'success': False,
                'error': 'No tariff found for this route',
                'cache_hit': False
            }
        
        # Calculate price
        base_price = tariff.base_price
        weight_charge = tariff.price_per_kg * weight
        total_price = base_price + weight_charge
        
        result = {
            'success': True,
            'price': float(total_price),
            'breakdown': {
                'base_price': float(base_price),
                'weight_charge': float(weight_charge),
                'weight': float(weight),
                'price_per_kg': float(tariff.price_per_kg)
            },
            'origin_zone': origin_zone.name,
            'destination_zone': destination_zone.name,
            'transport_mode': transport_mode,
            'tariff_id': tariff.id,
            'cache_hit': False
        }
        
        # Cache the result
        cache.set(cache_key, result, timeout=TariffService.CACHE_TTL)
        logger.info(f"💾 Cached tariff result")
        
        return result
    
    @staticmethod
    def clear_tariff_cache():
        """Clear all tariff-related caches"""
        logger.info("🗑️ Clearing tariff cache")
        cache.clear()