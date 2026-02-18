"""
OTP (One-Time Password) Service
Handles OTP generation, storage, and validation for phone verification
"""
import random
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class OTPService:
    """
    Service for generating and validating OTPs
    Uses Redis cache for temporary storage (5-minute expiry)
    """
    
    OTP_LENGTH = 6
    OTP_EXPIRY = 60 * 5  # 5 minutes in seconds
    MAX_ATTEMPTS = 3  # Max verification attempts
    
    @staticmethod
    def generate_otp() -> str:
        """
        Generate a random 6-digit OTP
        
        Returns:
            6-digit string (e.g., "123456")
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(OTPService.OTP_LENGTH)])
    
    @staticmethod
    def _get_cache_key(phone: str, purpose: str = 'verification') -> str:
        """Generate cache key for OTP storage"""
        return f"otp:{purpose}:{phone}"
    
    @staticmethod
    def _get_attempts_key(phone: str, purpose: str = 'verification') -> str:
        """Generate cache key for attempt tracking"""
        return f"otp_attempts:{purpose}:{phone}"
    
    @staticmethod
    def send_otp(phone: str, purpose: str = 'verification') -> dict:
        """
        Generate and "send" OTP to phone number
        
        In production: Would integrate with real SMS gateway (Africa's Talking, Twilio, etc.)
        In development: Stores in cache and returns OTP (for testing)
        
        Args:
            phone: Phone number to send OTP to
            purpose: 'verification' or 'recovery'
            
        Returns:
            Dict with success status and OTP (only in development)
        """
        # Generate OTP
        otp = OTPService.generate_otp()
        
        # Store in cache with 5-minute expiry
        cache_key = OTPService._get_cache_key(phone, purpose)
        cache.set(cache_key, otp, timeout=OTPService.OTP_EXPIRY)
        
        # Reset attempt counter
        attempts_key = OTPService._get_attempts_key(phone, purpose)
        cache.set(attempts_key, 0, timeout=OTPService.OTP_EXPIRY)
        
        # In production: Send via SMS gateway
        # from core.notifications import NotificationService
        # NotificationService.send_sms(phone, f"Your IshemaLink OTP is: {otp}. Valid for 5 minutes.")
        
        logger.info(f"OTP generated for {phone}: {otp} (Purpose: {purpose})")
        
        return {
            'success': True,
            'message': f'OTP sent to {phone}',
            'expires_in': OTPService.OTP_EXPIRY,
            'otp': otp,  # ONLY return in development! Remove in production
        }
    
    @staticmethod
    def verify_otp(phone: str, otp: str, purpose: str = 'verification') -> dict:
        """
        Verify OTP code
        
        Args:
            phone: Phone number
            otp: OTP code to verify
            purpose: 'verification' or 'recovery'
            
        Returns:
            Dict with success status and message
        """
        cache_key = OTPService._get_cache_key(phone, purpose)
        attempts_key = OTPService._get_attempts_key(phone, purpose)
        
        # Get stored OTP
        stored_otp = cache.get(cache_key)
        
        if not stored_otp:
            return {
                'success': False,
                'error': 'OTP expired or not found. Please request a new one.',
            }
        
        # Get attempt count
        attempts = cache.get(attempts_key, 0)
        
        if attempts >= OTPService.MAX_ATTEMPTS:
            # Clear OTP after max attempts
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return {
                'success': False,
                'error': 'Too many failed attempts. Please request a new OTP.',
            }
        
        # Verify OTP
        if stored_otp == otp:
            # Success - clear OTP
            cache.delete(cache_key)
            cache.delete(attempts_key)
            logger.info(f"OTP verified for {phone}")
            return {
                'success': True,
                'message': 'OTP verified successfully',
            }
        else:
            # Increment attempts
            cache.set(attempts_key, attempts + 1, timeout=OTPService.OTP_EXPIRY)
            remaining = OTPService.MAX_ATTEMPTS - (attempts + 1)
            
            logger.warning(f"Invalid OTP for {phone}. Attempts: {attempts + 1}/{OTPService.MAX_ATTEMPTS}")
            
            return {
                'success': False,
                'error': f'Invalid OTP. {remaining} attempts remaining.',
                'attempts_remaining': remaining,
            }
    
    @staticmethod
    def check_otp_exists(phone: str, purpose: str = 'verification') -> bool:
        """Check if an OTP exists for this phone"""
        cache_key = OTPService._get_cache_key(phone, purpose)
        return cache.get(cache_key) is not None