"""
Validation utilities for TaskPal API
"""
import re
from typing import Any

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if not password or not isinstance(password, str):
        return False
    
    # At least 8 characters
    if len(password) < 8:
        return False
    
    # At least one letter and one number
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    
    return has_letter and has_number

def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username or not isinstance(username, str):
        return False
    
    # 3-20 characters, letters, numbers, and underscores only
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username.strip()))

def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string.lower()))

def validate_required_fields(data: dict, required_fields: list) -> tuple[bool, str]:
    """Validate that all required fields are present and not empty"""
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f'{field} is required'
    
    return True, ""

def validate_string_length(value: str, min_length: int = 0, max_length: int = None) -> bool:
    """Validate string length"""
    if not isinstance(value, str):
        return False
    
    if len(value) < min_length:
        return False
    
    if max_length and len(value) > max_length:
        return False
    
    return True

def sanitize_string(value: str) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        return ""
    
    return value.strip()

def validate_json_data(data: Any) -> bool:
    """Validate that data is JSON serializable"""
    try:
        import json
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False
