"""
Booking Service
Unified service for creating bookings with integrated payment
"""
import logging
import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from domestic.models import DomesticShipment
from domestic.tariff_service import TariffService
from payments.models import Payment
from payments.momo_service import MobileMoneyService
from .models import Booking

logger = logging.getLogger(__name__)


class BookingService:
    """
    Unified service for creating bookings with integrated payment
    
    Flow:
    1. Calculate tariff based on weight and distance
    2. Create shipment (status: AWAITING_PAYMENT)
    3. Create booking record
    4. Initiate payment
    5. Return booking details with payment info
    
    Payment webhook will activate shipment when payment succeeds
    """
    
    @staticmethod
    def generate_booking_reference():
        """Generate unique booking reference"""
        return f"BK-{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    @transaction.atomic
    def create_booking(user, booking_data):
        """
        Create a complete booking with payment
        
        Args:
            user: Authenticated user (sender)
            booking_data: Dict with shipment and payment details
            
        Returns:
            Dict with booking, shipment, and payment info
        """
        # Extract data
        receiver_name = booking_data['receiver_name']
        receiver_phone = booking_data['receiver_phone']
        receiver_address = booking_data.get('receiver_address', '')
        delivery_address = booking_data.get('delivery_address', receiver_address)
        origin_district = booking_data['origin_district']
        origin_sector = booking_data['origin_sector']
        destination_district = booking_data['destination_district']
        destination_sector = booking_data['destination_sector']
        weight = booking_data['weight']
        description = booking_data.get('description', '')
        transport_mode = booking_data.get('transport_mode', 'BUS')
        payment_method = booking_data.get('payment_method', 'MTN_MOMO')
        payment_phone = booking_data.get('payment_phone', user.phone)
        
        # Convert weight to Decimal
        weight_decimal = Decimal(str(weight))
        
        # Step 1: Calculate tariff
        tariff_result = TariffService.calculate_tariff(
            weight=weight_decimal,
            origin_district=origin_district,
            destination_district=destination_district,
            transport_mode=transport_mode
        )
        
        if not tariff_result['success']:
            return {
                'success': False,
                'error': tariff_result.get('error', 'Failed to calculate tariff')
            }
        
        price = Decimal(str(tariff_result['price']))
        
        logger.info(f"Creating booking for {user.phone}")
        logger.info(f"Route: {origin_district} to {destination_district}")
        logger.info(f"Price: {price} RWF")
        
        # Step 2: Create shipment (AWAITING_PAYMENT status)
        shipment = DomesticShipment.objects.create(
            sender=user,
            sender_phone=user.phone,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            delivery_address=delivery_address,
            origin_district=origin_district,
            origin_sector=origin_sector,
            destination_district=destination_district,
            destination_sector=destination_sector,
            weight=weight_decimal,
            description=description,
            transport_mode=transport_mode,
            price=price,
            status='AWAITING_PAYMENT'
        )
        
        logger.info(f"Shipment created: {shipment.tracking_code}")
        
        # Step 3: Create booking record
        booking_reference = BookingService.generate_booking_reference()
        booking = Booking.objects.create(
            user=user,
            shipment=shipment,
            booking_reference=booking_reference,
            status='PENDING_PAYMENT',
            total_amount=price
        )
        
        logger.info(f"Booking created: {booking_reference}")
        
        # Step 4: Initiate payment
        try:
            momo_response = MobileMoneyService.initiate_payment(
                phone=payment_phone,
                amount=float(price),
                payment_method=payment_method
            )
            
            if not momo_response['success']:
                return {
                    'success': False,
                    'error': 'Failed to initiate payment'
                }
            
            # Create payment record
            payment = Payment.objects.create(
                user=user,
                shipment=shipment,
                transaction_ref=momo_response['transaction_ref'],
                amount=price,
                payment_method=payment_method,
                phone_number=payment_phone,
                status='PENDING',
                provider_response=momo_response
            )
            
            # Link payment to booking
            booking.payment = payment
            booking.save()
            
            logger.info(f"Payment initiated: {payment.transaction_ref}")
            
            # Return booking details
            return {
                'success': True,
                'booking': {
                    'booking_reference': booking_reference,
                    'shipment_id': shipment.id,
                    'tracking_code': shipment.tracking_code,
                    'status': booking.status,
                    'price': float(price),
                    'origin': f"{origin_sector}, {origin_district}",
                    'destination': f"{destination_sector}, {destination_district}",
                    'weight': float(weight_decimal),
                    'transport_mode': transport_mode,
                    'created_at': booking.created_at.isoformat()
                },
                'payment': {
                    'payment_id': str(payment.payment_id),
                    'transaction_ref': payment.transaction_ref,
                    'amount': float(payment.amount),
                    'payment_method': payment.payment_method,
                    'status': payment.status,
                    'message': momo_response['message']
                },
                'next_steps': [
                    'Enter your Mobile Money PIN on your phone',
                    'Payment will be confirmed automatically',
                    'Shipment will be activated for pickup'
                ]
            }
            
        except Exception as e:
            logger.error(f"Booking error: {e}")
            return {
                'success': False,
                'error': 'Booking failed. Please try again.'
            }
    
    @staticmethod
    def get_booking_status(booking_reference):
        """
        Get complete booking status
        
        Returns booking + shipment + payment status
        """
        try:
            booking = Booking.objects.select_related('shipment', 'payment').get(
                booking_reference=booking_reference
            )
            
            result = {
                'booking_reference': booking_reference,
                'status': booking.status,
                'total_amount': float(booking.total_amount),
                'created_at': booking.created_at.isoformat(),
                'shipment': {
                    'tracking_code': booking.shipment.tracking_code,
                    'status': booking.shipment.status,
                    'origin': f"{booking.shipment.origin_sector}, {booking.shipment.origin_district}",
                    'destination': f"{booking.shipment.destination_sector}, {booking.shipment.destination_district}"
                }
            }
            
            if booking.payment:
                result['payment'] = {
                    'transaction_ref': booking.payment.transaction_ref,
                    'status': booking.payment.status,
                    'amount': float(booking.payment.amount),
                    'initiated_at': booking.payment.initiated_at.isoformat(),
                    'completed_at': booking.payment.completed_at.isoformat() if booking.payment.completed_at else None
                }
            
            return {
                'success': True,
                'booking': result
            }
            
        except Booking.DoesNotExist:
            return {
                'success': False,
                'error': 'Booking not found'
            }