"""
Rwanda-specific validation utilities
Handles phone numbers and National ID validation
"""
import re
from typing import Tuple


def validate_rwanda_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate Rwanda phone number format
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        
    Valid formats:
        - +250788123456
        - +250 788 123 456
        - +250 7 88 123 456
    """
   
    clean_phone = phone.replace(" ", "")
    
    # Must start with +250
    if not clean_phone.startswith("+250"):
        return False, "Phone number must start with +250"
    
    # Must be followed by 7 (all Rwanda mobile numbers start with 7)
    if len(clean_phone) < 5 or clean_phone[4] != "7":
        return False, "Rwanda mobile numbers must start with +250 7"
    
    # Total length must be 13 digits (+250 + 9 digits)
    if len(clean_phone) != 13:
        return False, "Phone number must have 9 digits after +250"
    
    # Must be all digits after +250
    if not clean_phone[4:].isdigit():
        return False, "Phone number must contain only digits after +250"
    
    return True, ""


def validate_rwanda_nid(nid: str) -> Tuple[bool, str]:
    """
    Validate Rwanda National ID format
    
    Args:
        nid: National ID string to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        
    Rules:
        - Must be exactly 16 digits
        - Must start with 1 (as per Rwanda ID format)
        - Must be all numeric
    """
    # Remove any spaces
    clean_nid = nid.replace(" ", "")
    
    # Must be 16 characters
    if len(clean_nid) != 16:
        return False, "National ID must be exactly 16 digits"
    
    # Must be all digits
    if not clean_nid.isdigit():
        return False, "National ID must contain only digits"
    
    # Must start with 1 (Rwanda ID format)
    if not clean_nid.startswith("1"):
        return False, "Invalid NID format. Must start with 1."
    
    return True, ""


def format_rwanda_phone(phone: str) -> str:
    """
    Format phone number to standard format: +250 7XX XXX XXX
    
    Args:
        phone: Phone number to format
        
    Returns:
        Formatted phone number string
    """
    # Remove all spaces and non-digit characters except +
    clean = re.sub(r'[^\d+]', '', phone)
    
    # Ensure it starts with +250
    if not clean.startswith('+250'):
        if clean.startswith('250'):
            clean = '+' + clean
        elif clean.startswith('0'):
            clean = '+250' + clean[1:]
        else:
            clean = '+250' + clean
    
    # Format as +250 7XX XXX XXX
    if len(clean) >= 13:
        return f"{clean[:4]} {clean[4:7]} {clean[7:10]} {clean[10:13]}"
    
    return clean