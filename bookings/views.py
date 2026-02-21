"""
Unified Booking Views
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from .services import BookingService
from .serializers import UnifiedBookingSerializer, BookingSerializer
from .models import Booking
import logging

logger = logging.getLogger(__name__)


class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Booking ViewSet
    List and retrieve user's bookings
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        """User can only see their own bookings"""
        return Booking.objects.filter(user=self.request.user)


@extend_schema(
    request=UnifiedBookingSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'booking': {'type': 'object'},
                'payment': {'type': 'object'},
                'next_steps': {'type': 'array'}
            }
        }
    },
    tags=['Bookings']
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_unified_booking(request):
    """
    POST /api/bookings/create/
    
    Create shipment + Calculate tariff + Initiate payment
    ALL IN ONE CALL
    
    Body:
    {
        "receiver_name": "John Doe",
        "receiver_phone": "+250788999999",
        "receiver_address": "House #45, Tumba",
        "origin_district": "Kigali",
        "origin_sector": "Nyarugenge",
        "destination_district": "Huye",
        "destination_sector": "Tumba",
        "weight": "5.00",
        "description": "Books",
        "transport_mode": "BUS",
        "payment_method": "MTN_MOMO",
        "payment_phone": "+250788123456"
    }
    
    Returns:
    - Booking reference
    - Tracking code
    - Payment instructions
    """
    serializer = UnifiedBookingSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Create unified booking
    result = BookingService.create_booking(
        user=request.user,
        booking_data=serializer.validated_data
    )
    
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={200: {'type': 'object'}},
    tags=['Bookings']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_booking_status(request, booking_reference):
    """
    GET /api/bookings/status/{booking_reference}/
    
    Get complete booking status (booking + shipment + payment)
    """
    result = BookingService.get_booking_status(booking_reference)
    
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_404_NOT_FOUND)