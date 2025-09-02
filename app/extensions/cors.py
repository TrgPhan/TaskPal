"""
CORS Extension
Handles Cross-Origin Resource Sharing for API access
"""
from flask_cors import CORS

# Initialize CORS without app context
cors = CORS()

def init_cors(app):
    """Initialize CORS with app"""
    cors_config = {
        'origins': ['http://localhost:3000', 'http://127.0.0.1:3000'],  # React dev server
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
        'supports_credentials': True
    }
    
    cors.init_app(app, **cors_config)
