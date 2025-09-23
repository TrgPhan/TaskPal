"""
JWT Extension
Handles JSON Web Token authentication
"""
from flask_jwt_extended import JWTManager

# Initialize JWT Manager without app context
jwt_manager = JWTManager()

def init_jwt(app):
    """Initialize JWT with app"""
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens don't expire by default
    app.config['JWT_ALGORITHM'] = 'HS256'
    
    jwt_manager.init_app(app)
    
    # Optional: Add custom JWT claims
    @jwt_manager.additional_claims_loader
    def add_claims_to_access_token(identity):
        # You can add custom claims here
        return {
            'roles': []  # Example: user roles
        }
    
    # Error handlers
    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401
    
    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401
    
    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token is required'}, 401
