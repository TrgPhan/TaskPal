from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.extensions.database import db
from app.models.user import User
from app.utils.validators import validate_email, validate_password, validate_username
from app.utils.responses import success_response, error_response
import uuid

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'username', 'full_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} is required', 400)
        
        # Validate email format
        if not validate_email(data['email']):
            return error_response('Invalid email format', 400)
        
        # Validate password strength
        if not validate_password(data['password']):
            return error_response('Password must be at least 8 characters long', 400)
        
        # Validate username
        if not validate_username(data['username']):
            return error_response('Username must be 3-20 characters and contain only letters, numbers, and underscores', 400)
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return error_response('Email already registered', 409)
        
        if User.query.filter_by(username=data['username']).first():
            return error_response('Username already taken', 409)
        
        # Create new user
        user = User(
            email=data['email'].lower().strip(),
            username=data['username'].lower().strip(),
            full_name=data['full_name'].strip(),
            timezone=data.get('timezone', 'UTC'),
            language=data.get('language', 'vi')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return success_response({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Registration failed', 500)

@auth.route('/login', methods=['POST'])
def login():
    """Authenticate user and return access token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return error_response('Email and password are required', 400)
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].lower().strip()).first()
        
        if not user or not user.check_password(data['password']):
            return error_response('Invalid email or password', 401)
        
        if not user.is_active:
            return error_response('Account is deactivated', 403)
        
        # Update last active
        from datetime import datetime
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return success_response({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        })
        
    except Exception as e:
        return error_response('Login failed', 500)

@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard token)"""
    try:
        # In a more advanced setup, you could blacklist the token
        # For now, we'll just return success and let the client discard the token
        return success_response({'message': 'Logout successful'})
        
    except Exception as e:
        return error_response('Logout failed', 500)
    # It's seem a little bit useless but it's for symmetry

@auth.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return error_response('User not found or inactive', 404)
        
        # Create new access token
        access_token = create_access_token(identity=str(user.id))
        
        return success_response({
            'access_token': access_token
        })
        
    except Exception as e:
        return error_response('Token refresh failed', 500)

@auth.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        return success_response({
            'user': user.to_dict()
        })
        
    except Exception as e:
        return error_response('Failed to get user information', 500)
