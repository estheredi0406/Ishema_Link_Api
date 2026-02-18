"""
Field-Level Encryption
Encrypts sensitive data before storing in database
Uses Fernet symmetric encryption (AES-128)
"""
import base64
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet


class EncryptionService:
    """
    Service for encrypting/decrypting sensitive data
    Uses Fernet (symmetric encryption based on AES)
    """
    
    @staticmethod
    def get_cipher():
        """Get Fernet cipher instance"""
        key = settings.FIELD_ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    
    @staticmethod
    def encrypt(value: str) -> str:
        """
        Encrypt a string value
        
        Args:
            value: Plain text string
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not value:
            return value
        
        cipher = EncryptionService.get_cipher()
        encrypted = cipher.encrypt(value.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt(value: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            value: Encrypted string
            
        Returns:
            Decrypted plain text string
        """
        if not value:
            return value
        
        cipher = EncryptionService.get_cipher()
        decrypted = cipher.decrypt(value.encode())
        return decrypted.decode()


class EncryptedCharField(models.CharField):
    """
    CharField that automatically encrypts data before saving to database
    and decrypts when reading from database
    
    Usage:
        national_id = EncryptedCharField(max_length=255)
    
    Note: max_length should be larger than plain text to account for encryption overhead
    """
    
    description = "Encrypted CharField"
    
    def __init__(self, *args, **kwargs):
        # Encryption adds overhead, ensure max_length is sufficient
        if 'max_length' in kwargs:
            kwargs['max_length'] = max(kwargs['max_length'], 255)
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """Called when loading data from database"""
        if value is None:
            return value
        return EncryptionService.decrypt(value)
    
    def to_python(self, value):
        """Called during deserialization and in forms"""
        if isinstance(value, str) or value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """Called when saving to database"""
        if value is None:
            return value
        return EncryptionService.encrypt(str(value))


class EncryptedTextField(models.TextField):
    """
    TextField that automatically encrypts data before saving to database
    and decrypts when reading from database
    
    Usage:
        tax_details = EncryptedTextField()
    """
    
    description = "Encrypted TextField"
    
    def from_db_value(self, value, expression, connection):
        """Called when loading data from database"""
        if value is None:
            return value
        return EncryptionService.decrypt(value)
    
    def to_python(self, value):
        """Called during deserialization and in forms"""
        if isinstance(value, str) or value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """Called when saving to database"""
        if value is None:
            return value
        return EncryptionService.encrypt(str(value))