"""
Tariff API Views
Endpoints for tariff calculation and management
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAdminUser
from decimal import Decimal
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .tariff_service import TariffService


class TariffCalculateSerializer(serializers.Serializer):
    """Serializer for tariff calculation request"""
    weight = serializers.DecimalField(max_digits=6, decimal_places=2, required=True)
    origin_district = serializers.CharField(max_length=100, required=True)
    destination_district = serializers.CharField(max_length=100, required=True)
    transport_mode = serializers.ChoiceField(choices=['MOTO', 'BUS'], required=True)


class TariffCalculateView(APIView):
    """
    POST /api/domestic/tariff/calculate/
    Calculate shipping price with caching
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=TariffCalculateSerializer,
        responses={200: dict}
    )
    def post(self, request):
        """
        Calculate tariff for a shipment
        
        Request body:
        {
            "weight": 5.5,
            "origin_district": "Kigali",
            "destination_district": "Huye",
            "transport_mode": "BUS"
        }
        """
        serializer = TariffCalculateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Calculate tariff (with caching)
            result = TariffService.calculate_tariff(
                weight=serializer.validated_data['weight'],
                origin_district=serializer.validated_data['origin_district'],
                destination_district=serializer.validated_data['destination_district'],
                transport_mode=serializer.validated_data['transport_mode']
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': f'Calculation error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TariffCacheClearView(APIView):
    """
    POST /api/domestic/tariff/clear-cache/
    Clear tariff cache (admin only)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Clear all tariff caches"""
        TariffService.clear_tariff_cache()
        
        return Response({
            'message': 'Tariff cache cleared successfully'
        }, status=status.HTTP_200_OK)