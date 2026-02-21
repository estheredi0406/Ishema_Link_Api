"""
Tariff Service Tests
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from domestic.models import TariffZone, DomesticTariff
from domestic.tariff_service import TariffService


@pytest.mark.django_db
class TestTariffCalculation:
    """Test tariff calculation logic"""
    
    def setup_method(self):
        # Create zones (remove zone_code - field doesn't exist)
        self.zone_kigali = TariffZone.objects.create(
            name='Kigali Zone',
            districts=['Kigali', 'Gasabo', 'Kicukiro', 'Nyarugenge']
        )
        
        self.zone_south = TariffZone.objects.create(
            name='Southern Zone',
            districts=['Huye', 'Nyanza']
        )
        
        # Create tariff
        self.tariff = DomesticTariff.objects.create(
            origin_zone=self.zone_kigali,
            destination_zone=self.zone_south,
            transport_mode='BUS',
            base_price=Decimal('2000.00'),
            price_per_kg=Decimal('500.00'),
            min_weight=Decimal('0.00'),
            max_weight=Decimal('100.00'),
            is_active=True,
            effective_date=timezone.now().date()
        )
    
    def test_tariff_calculation_correct(self):
        """Test tariff calculates correctly"""
        result = TariffService.calculate_tariff(
            weight=Decimal('5.00'),
            origin_district='Kigali',
            destination_district='Huye',
            transport_mode='BUS'
        )
        
        assert result['success'] is True
        # 2000 base + (5kg * 500) = 4500
        assert result['price'] == 4500.0
        assert result['breakdown']['base_price'] == 2000.0
        assert result['breakdown']['weight_charge'] == 2500.0
    
    def test_invalid_district_returns_error(self):
        """Test invalid district returns error"""
        result = TariffService.calculate_tariff(
            weight=Decimal('5.00'),
            origin_district='InvalidDistrict',
            destination_district='Huye',
            transport_mode='BUS'
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_no_tariff_for_route(self):
        """Test route with no tariff returns error"""
        result = TariffService.calculate_tariff(
            weight=Decimal('5.00'),
            origin_district='Kigali',
            destination_district='Huye',
            transport_mode='AIRPLANE'  # No tariff for this mode
        )
        
        assert result['success'] is False
        assert 'error' in result