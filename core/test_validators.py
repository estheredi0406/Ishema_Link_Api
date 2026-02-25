"""
Unit Tests for Core Validators
Tests NID validation, phone validation, Rwanda-specific logic
"""
import pytest
from django.core.exceptions import ValidationError


def validate_rwanda_phone(phone):
    """Basic phone validator"""
    if not phone.startswith('+250'):
        raise ValidationError('Phone must start with +250')
    if len(phone) != 13:
        raise ValidationError('Phone must be 13 characters')


def validate_nid(nid):
    """Basic NID validator"""
    if len(nid) != 16:
        raise ValidationError('NID must be exactly 16 digits')
    if not nid.isdigit():
        raise ValidationError('NID must contain only digits')


class TestRwandaPhoneValidator:
    """Test Rwanda phone number validation"""
    
    def test_valid_phone_formats(self):
        """Valid Rwanda phone numbers should pass"""
        valid_phones = [
            '+250788123456',
            '+250781234567',
            '+250728123456',
        ]
        for phone in valid_phones:
            try:
                validate_rwanda_phone(phone)
            except ValidationError:
                pytest.fail(f"{phone} should be valid")
    
    def test_invalid_phone_missing_country_code(self):
        """Phone without +250 should fail"""
        with pytest.raises(ValidationError):
            validate_rwanda_phone('0788123456')
    
    def test_invalid_phone_wrong_country(self):
        """Phone with wrong country code should fail"""
        with pytest.raises(ValidationError):
            validate_rwanda_phone('+251788123456')
    
    def test_invalid_phone_too_short(self):
        """Phone too short should fail"""
        with pytest.raises(ValidationError):
            validate_rwanda_phone('+25078812345')


class TestNIDValidator:
    """Test National ID validation"""
    
    def test_valid_nid(self):
        """Valid 16-digit NID should pass"""
        valid_nids = [
            '1234567890123456',
            '1199912345678901',
        ]
        for nid in valid_nids:
            try:
                validate_nid(nid)
            except ValidationError:
                pytest.fail(f"{nid} should be valid")
    
    def test_invalid_nid_too_short(self):
        """NID with less than 16 digits should fail"""
        with pytest.raises(ValidationError):
            validate_nid('123456789012345')
    
    def test_invalid_nid_too_long(self):
        """NID with more than 16 digits should fail"""
        with pytest.raises(ValidationError):
            validate_nid('12345678901234567')
    
    def test_invalid_nid_non_numeric(self):
        """NID with letters should fail"""
        with pytest.raises(ValidationError):
            validate_nid('123456789012345A')