"""
Notification Service
Handles SMS and Email notifications (simulated for development)
"""
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending SMS and Email notifications
    In production, this would integrate with real SMS/Email gateways
    """
    
    @staticmethod
    def send_sms(phone: str, message: str) -> Dict[str, Any]:
        """
        Send SMS notification
        
        Args:
            phone: Recipient phone number
            message: SMS message content
            
        Returns:
            Dict with success status and details
        """
        logger.info(f" Sending SMS to {phone}")
        logger.info(f"Message: {message}")
        
        # Simulate API call delay (1-3 seconds)
        time.sleep(2)
        
        # Simulate successful send
        result = {
            'success': True,
            'recipient': phone,
            'message': message,
            'provider': 'IshemaLink SMS Gateway',
            'cost': 50,  # RWF
            'timestamp': time.time()
        }
        
        logger.info(f"SMS sent successfully to {phone}")
        return result
    
    @staticmethod
    def send_email(recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send Email notification
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            
        Returns:
            Dict with success status and details
        """
        logger.info(f"Sending email to {recipient}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body[:100]}...")
        
        # Simulate API call delay
        time.sleep(1.5)
        
        result = {
            'success': True,
            'recipient': recipient,
            'subject': subject,
            'provider': 'IshemaLink Email Service',
            'timestamp': time.time()
        }
        
        logger.info(f"Email sent successfully to {recipient}")
        return result
    
    @staticmethod
    def send_shipment_notification(
        shipment_tracking: str,
        phone: str,
        status: str,
        recipient_name: str = "Customer"
    ) -> Dict[str, Any]:
        """
        Send shipment status update notification
        
        Args:
            shipment_tracking: Tracking code
            phone: Recipient phone
            status: New shipment status
            recipient_name: Name of recipient
            
        Returns:
            Notification result
        """
        # Create user-friendly message based on status
        status_messages = {
            'PENDING': f"Hello {recipient_name}! Your package {shipment_tracking} is awaiting pickup.",
            'PICKED_UP': f"Hello {recipient_name}! Your package {shipment_tracking} has been picked up.",
            'IN_TRANSIT': f"Hello {recipient_name}! Your package {shipment_tracking} is on the way.",
            'AT_HUB': f"Hello {recipient_name}! Your package {shipment_tracking} has arrived at our hub.",
            'OUT_FOR_DELIVERY': f"Hello {recipient_name}! Your package {shipment_tracking} is out for delivery today!",
            'DELIVERED': f"Hello {recipient_name}! Your package {shipment_tracking} has been delivered. Thank you for using IshemaLink!",
            'CANCELLED': f"Hello {recipient_name}! Your package {shipment_tracking} has been cancelled."
        }
        
        message = status_messages.get(status, f"Your package {shipment_tracking} status: {status}")
        
        return NotificationService.send_sms(phone, message)