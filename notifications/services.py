"""
Notification Service
Sends SMS and Email notifications
"""
import logging
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications
    Mock implementation - replace with real SMS/Email providers
    """
    
    @staticmethod
    def send_sms(phone: str, message: str, event: str, metadata: dict = None):
        """
        Send SMS notification
        
        In production: Integrate with Africa's Talking, Twilio, etc.
        """
        try:
            # Mock SMS sending
            logger.info(f"📱 Sending SMS to {phone}")
            logger.info(f"   Message: {message}")
            
            # Simulate API call
            provider_response = {
                'success': True,
                'message_id': f"sms_{timezone.now().timestamp()}",
                'provider': 'AfricasTalking',
                'cost': 'RWF 10'
            }
            
            # Create notification record
            notification = Notification.objects.create(
                recipient_phone=phone,
                notification_type='SMS',
                event=event,
                message=message,
                status='SENT',
                provider='AfricasTalking',
                provider_response=provider_response,
                external_id=provider_response['message_id'],
                sent_at=timezone.now(),
                metadata=metadata or {}
            )
            
            logger.info(f"✅ SMS sent successfully: {notification.id}")
            
            return {
                'success': True,
                'notification_id': notification.id,
                'provider_response': provider_response
            }
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            
            # Create failed notification record
            Notification.objects.create(
                recipient_phone=phone,
                notification_type='SMS',
                event=event,
                message=message,
                status='FAILED',
                failed_at=timezone.now(),
                metadata={'error': str(e)}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_email(email: str, subject: str, message: str, event: str, metadata: dict = None):
        """
        Send Email notification
        
        In production: Integrate with SendGrid, Mailgun, etc.
        """
        try:
            # Mock Email sending
            logger.info(f"📧 Sending Email to {email}")
            logger.info(f"   Subject: {subject}")
            logger.info(f"   Message: {message[:50]}...")
            
            # Simulate API call
            provider_response = {
                'success': True,
                'message_id': f"email_{timezone.now().timestamp()}",
                'provider': 'SendGrid'
            }
            
            # Create notification record
            notification = Notification.objects.create(
                recipient_email=email,
                notification_type='EMAIL',
                event=event,
                subject=subject,
                message=message,
                status='SENT',
                provider='SendGrid',
                provider_response=provider_response,
                external_id=provider_response['message_id'],
                sent_at=timezone.now(),
                metadata=metadata or {}
            )
            
            logger.info(f"✅ Email sent successfully: {notification.id}")
            
            return {
                'success': True,
                'notification_id': notification.id,
                'provider_response': provider_response
            }
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            
            # Create failed notification record
            Notification.objects.create(
                recipient_email=email,
                notification_type='EMAIL',
                event=event,
                subject=subject,
                message=message,
                status='FAILED',
                failed_at=timezone.now(),
                metadata={'error': str(e)}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def notify_booking_created(booking):
        """Send notification when booking is created"""
        message = f"IshemaLink: Booking {booking.booking_reference} created. " \
                  f"Track: {booking.shipment.tracking_code}. " \
                  f"Pay {booking.total_amount} RWF via Mobile Money. Thank you!"
        
        return NotificationService.send_sms(
            phone=booking.user.phone,
            message=message,
            event='BOOKING_CREATED',
            metadata={
                'booking_id': booking.id,
                'tracking_code': booking.shipment.tracking_code
            }
        )
    
    @staticmethod
    def notify_payment_success(payment):
        """Send notification when payment is successful"""
        message = f"IshemaLink: Payment confirmed! {payment.amount} RWF received. " \
                  f"Track shipment: {payment.shipment.tracking_code}. " \
                  f"Pickup within 24 hours."
        
        return NotificationService.send_sms(
            phone=payment.phone_number,
            message=message,
            event='PAYMENT_SUCCESS',
            metadata={
                'payment_id': payment.id,
                'transaction_ref': payment.transaction_ref,
                'amount': str(payment.amount)
            }
        )
    
    @staticmethod
    def notify_shipment_status(shipment, new_status):
        """Send notification when shipment status changes"""
        status_messages = {
            'PICKED_UP': f"Your package {shipment.tracking_code} has been picked up and is on its way!",
            'IN_TRANSIT': f"Your package {shipment.tracking_code} is in transit to {shipment.destination_district}.",
            'OUT_FOR_DELIVERY': f"Your package {shipment.tracking_code} is out for delivery. Expect it today!",
            'DELIVERED': f"Delivered! Package {shipment.tracking_code} has been delivered. Thank you for using IshemaLink!",
            'CANCELLED': f"Package {shipment.tracking_code} has been cancelled. Contact support for details."
        }
        
        message = status_messages.get(new_status, f"Status update: {shipment.tracking_code} - {new_status}")
        
        # Send to sender
        NotificationService.send_sms(
            phone=shipment.sender_phone,
            message=message,
            event=f'SHIPMENT_{new_status}',
            metadata={
                'shipment_id': shipment.id,
                'tracking_code': shipment.tracking_code,
                'status': new_status
            }
        )
        
        # Send to receiver
        NotificationService.send_sms(
            phone=shipment.receiver_phone,
            message=message,
            event=f'SHIPMENT_{new_status}',
            metadata={
                'shipment_id': shipment.id,
                'tracking_code': shipment.tracking_code,
                'status': new_status
            }
        )