"""
Response utilities for TaskPal API
"""
from flask import jsonify
from typing import Any, Dict, Optional

def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
    """Create a standardized success response"""
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    
    return jsonify(response_data), status_code

def error_response(message: str = "An error occurred", status_code: int = 400, errors: Optional[Dict] = None) -> tuple:
    """Create a standardized error response"""
    response_data = {
        "success": False,
        "message": message,
        "errors": errors or {}
    }
    
    return jsonify(response_data), status_code

def validation_error_response(errors: Dict[str, str], message: str = "Validation failed") -> tuple:
    """Create a validation error response"""
    return error_response(message, 400, errors)

def not_found_response(resource: str = "Resource") -> tuple:
    """Create a not found error response"""
    return error_response(f"{resource} not found", 404)

def unauthorized_response(message: str = "Unauthorized access") -> tuple:
    """Create an unauthorized error response"""
    return error_response(message, 401)

def forbidden_response(message: str = "Access forbidden") -> tuple:
    """Create a forbidden error response"""
    return error_response(message, 403)

def server_error_response(message: str = "Internal server error") -> tuple:
    """Create a server error response"""
    return error_response(message, 500)

def created_response(data: Any = None, message: str = "Resource created successfully") -> tuple:
    """Create a created response"""
    return success_response(data, message, 201)

def updated_response(data: Any = None, message: str = "Resource updated successfully") -> tuple:
    """Create an updated response"""
    return success_response(data, message, 200)

def deleted_response(message: str = "Resource deleted successfully") -> tuple:
    """Create a deleted response"""
    return success_response(None, message, 200)
