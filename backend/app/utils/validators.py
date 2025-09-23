"""
Validation utilities for TaskPal API
"""
import re
from typing import Any, Tuple, List

# Regex patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

def _is_valid_string(value: Any) -> bool:
    """Check if value is a valid non-empty string"""
    return value and isinstance(value, str) and value.strip()

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not _is_valid_string(email):
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if not _is_valid_string(password):
        return False
    
    # At least 8 characters
    if len(password) < 8:
        return False
    
    # At least one letter and one number
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    
    return has_letter and has_number

def validate_strong_password(password: str) -> Tuple[bool, List[str]]:
    """Validate strong password with detailed requirements"""
    errors = []
    
    if not _is_valid_string(password):
        errors.append("Password is required")
        return False, errors
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors

def validate_username(username: str) -> bool:
    """Validate username format"""
    if not _is_valid_string(username):
        return False
    return bool(USERNAME_PATTERN.match(username.strip()))

def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    if not _is_valid_string(uuid_string):
        return False
    return bool(UUID_PATTERN.match(uuid_string.lower()))

def validate_required_fields(data: dict, required_fields: list) -> Tuple[bool, str]:
    """Validate that all required fields are present and not empty"""
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f'{field} is required'
    return True, ""

def validate_string_length(value: str, min_length: int = 0, max_length: int = None) -> bool:
    """Validate string length"""
    if not isinstance(value, str):
        return False
    
    length = len(value.strip())
    
    if length < min_length:
        return False
    
    if max_length and length > max_length:
        return False
    
    return True

def validate_workspace_name(name: str) -> Tuple[bool, str]:
    """Validate workspace name"""
    if not _is_valid_string(name):
        return False, "Workspace name is required"
    
    if not validate_string_length(name, 1, 255):
        return False, "Workspace name must be between 1 and 255 characters"
    
    return True, ""

def validate_page_title(title: str) -> Tuple[bool, str]:
    """Validate page title"""
    if not _is_valid_string(title):
        return False, "Page title is required"
    
    if not validate_string_length(title, 1, 500):
        return False, "Page title must be between 1 and 500 characters"
    
    return True, ""

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

def validate_pagination_params(page: int = 1, per_page: int = 20) -> Tuple[int, int]:
    """Validate and normalize pagination parameters"""
    try:
        page = max(1, int(page))
        per_page = max(1, min(100, int(per_page)))  # Limit to 100 items per page
    except (ValueError, TypeError):
        page = 1
        per_page = 20
    
    return page, per_page

def validate_sort_params(sort_by: str, valid_fields: List[str], 
                        sort_order: str = 'asc') -> Tuple[str, str]:
    """Validate sort parameters"""
    if sort_by not in valid_fields:
        sort_by = valid_fields[0] if valid_fields else 'created_at'
    
    sort_order = sort_order.lower()
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'
    
    return sort_by, sort_order
