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
    Service for calculating tariffs with robust matching and caching
    """
    
    CACHE_PREFIX = "tariff"
    CACHE_TTL = 60 * 60 * 24 * 7  # 7 days
    
    @staticmethod
    def _generate_cache_key(weight: Decimal, origin: str, dest: str, mode: str) -> str:
        # Normalize to uppercase to avoid duplicate cache keys for same locations
        key_string = f"{weight}:{origin.upper()}:{dest.upper()}:{mode.upper()}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{TariffService.CACHE_PREFIX}:{key_hash}"
    
    @staticmethod
    def get_zone_for_district(district: str) -> Optional[TariffZone]:
        """
        Finds the zone for a district using case-insensitive matching.
        """
        if not district:
            return None

        clean_name = district.strip().upper()
        cache_key = f"zone_lookup:{clean_name}"
        
        zone = cache.get(cache_key)
        if zone is not None:
            return zone
        
        # Iterate through zones and normalize the list for comparison
        for zone in TariffZone.objects.all():
            # zone.districts is expected to be a list of strings
            normalized_districts = [d.strip().upper() for d in zone.districts]
            if clean_name in normalized_districts:
                cache.set(cache_key, zone, timeout=60 * 60 * 24 * 30)
                return zone
        
        # Log specifically what failed to find a match
        logger.warning(f"No TariffZone found containing district: '{clean_name}'")
        return None
    
    @staticmethod
    def calculate_tariff(
        weight: Decimal,
        origin_district: str,
        destination_district: str,
        transport_mode: str
    ) -> Dict[str, Any]:
        """
        Calculates price with robust error reporting and normalization.
        """
        # Ensure numeric values are clean
        weight = Decimal(str(weight))
        
        cache_key = TariffService._generate_cache_key(
            weight, origin_district, destination_district, transport_mode
        )
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return {**cached_result, 'cache_hit': True}

        # 1. Resolve Zones with normalization
        origin_zone = TariffService.get_zone_for_district(origin_district)
        destination_zone = TariffService.get_zone_for_district(destination_district)
        
        if not origin_zone or not destination_zone:
            missing = []
            if not origin_zone: missing.append(f"Origin({origin_district})")
            if not destination_zone: missing.append(f"Dest({destination_district})")
            
            return {
                'success': False,
                'error': f"Zone lookup failed for: {', '.join(missing)}",
                'price': 0.0
            }
        
        # 2. Query for the specific Tariff
        try:
            # We use .upper() on transport_mode to match choices like 'MOTO', 'TRUCK'
            tariff = DomesticTariff.objects.get(
                origin_zone=origin_zone,
                destination_zone=destination_zone,
                transport_mode=transport_mode.upper(),
                min_weight__lte=weight,
                max_weight__gte=weight,
                is_active=True,
                effective_date__lte=timezone.now().date()
            )
        except DomesticTariff.DoesNotExist:
            return {
                'success': False,
                'error': f"No active tariff for {origin_zone.name}->{destination_zone.name} ({transport_mode}) at {weight}kg",
                'price': 0.0
            }
        
        # 3. Perform Calculation
        base_price = tariff.base_price
        weight_charge = tariff.price_per_kg * weight
        total_price = base_price + weight_charge
        
        result = {
            'success': True,
            'price': float(total_price),
            'breakdown': {
                'base': float(base_price),
                'per_kg': float(tariff.price_per_kg),
                'weight': float(weight),
            },
            'origin_zone': origin_zone.name,
            'destination_zone': destination_zone.name,
            'tariff_id': tariff.id,
            'cache_hit': False
        }
        
        cache.set(cache_key, result, timeout=TariffService.CACHE_TTL)
        return result