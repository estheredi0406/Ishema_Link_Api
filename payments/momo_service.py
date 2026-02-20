"""
Mobile Money Integration Service
Mock implementation for MTN Momo and Airtel Money
"""
import random
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MobileMoneyService:
    """
    Mock Mobile Money service for development
    In production: Replace with actual MTN Momo/Airtel API
    """
    
    @staticmethod
    def initiate_payment(phone: str, amount: float, payment_method: str = 'MTN_MOMO') -> dict:
        """
        Initiate a mobile money payment
        Simulates sending a push prompt to user's phone
        
        Args:
            phone: Customer phone number
            amount: Payment amount in RWF
            payment_method: MTN_MOMO or AIRTEL_MONEY
            
        Returns:
            Dict with transaction reference and status
        """
        # Generate transaction reference
        transaction_ref = f"MM-{uuid.uuid4().hex[:12].upper()}"
        
        logger.info(f"📱 Initiating {payment_method} payment: {transaction_ref}")
        logger.info(f"   Phone: {phone}, Amount: {amount} RWF")
        
        # Simulate API call to provider
        response = {
            'success': True,
            'transaction_ref': transaction_ref,
            'status': 'PENDING',
            'message': f'Payment prompt sent to {phone}. Please enter PIN on your phone.',
            'amount': amount,
            'phone': phone,
            'provider': payment_method,
            'initiated_at': datetime.now().isoformat()
        }
        
        return response
    
    @staticmethod
    def check_payment_status(transaction_ref: str) -> dict:
        """
        Check payment status with provider
        Mock: Randomly returns success/pending/failed
        
        Args:
            transaction_ref: Transaction reference from initiate_payment
            
        Returns:
            Dict with current payment status
        """
        # Simulate checking with provider API
        # In reality: Make HTTP request to MTN/Airtel API
        
        # Mock logic: 70% success, 20% pending, 10% failed
        rand = random.random()
        
        if rand < 0.7:
            status = 'SUCCESSFUL'
            message = 'Payment completed successfully'
        elif rand < 0.9:
            status = 'PENDING'
            message = 'Waiting for user to enter PIN'
        else:
            status = 'FAILED'
            message = 'Payment failed - insufficient balance'
        
        response = {
            'transaction_ref': transaction_ref,
            'status': status,
            'message': message,
            'checked_at': datetime.now().isoformat()
        }
        
        logger.info(f"💳 Payment status check: {transaction_ref} → {status}")
        
        return response
    
    @staticmethod
    def simulate_webhook_callback(transaction_ref: str, status: str = 'SUCCESSFUL') -> dict:
        """
        Simulate webhook callback from payment provider
        In production: This would be called by MTN/Airtel servers
        
        Args:
            transaction_ref: Transaction reference
            status: Payment status (SUCCESSFUL, FAILED)
            
        Returns:
            Dict with webhook payload
        """
        webhook_payload = {
            'event': 'payment.completed',
            'transaction_ref': transaction_ref,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'signature': f"sig_{uuid.uuid4().hex[:16]}",  # Mock signature
            'data': {
                'amount': 5000.00,
                'currency': 'RWF',
                'payer_phone': '+250788123456',
                'message': 'Payment successful' if status == 'SUCCESSFUL' else 'Payment failed'
            }
        }
        
        logger.info(f"🔔 Webhook callback simulated: {transaction_ref} → {status}")
        
        return webhook_payload