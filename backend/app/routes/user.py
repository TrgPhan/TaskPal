from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions.database import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.utils.validators import validate_email, validate_username, validate_password
from app.utils.responses import success_response, error_response
from app.services.cache_service import CacheService
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile with caching"""
    try:
        current_user_id = get_jwt_identity()
        
        # Try to get from cache first
        cache_key = f"user_profile:{current_user_id}"
        cached_profile = CacheService.get_cached(cache_key)
        
        if cached_profile:
            return success_response({
                'profile': cached_profile
            })
        
        # If not in cache, get from database
        user = User.query.get(current_user_id)
        if not user:
            return error_response('User not found', 404)
        
        # Get user's workspaces
        workspaces = db.session.query(Workspace).join(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user_id,
            WorkspaceMember.is_active == True
        ).all()
        
        profile_data = user.to_dict()
        profile_data['workspaces'] = [workspace.to_dict() for workspace in workspaces]
        
        # Cache the profile data for 15 minutes
        CacheService.set_cached(cache_key, profile_data, 900)
        
        return success_response({
            'profile': profile_data
        })
        
    except Exception as e:
        return error_response('Failed to get profile', 500)

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile and invalidate cache"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name'].strip()
        
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url'].strip()
        
        if 'timezone' in data:
            user.timezone = data['timezone']
        
        if 'language' in data:
            user.language = data['language']
        
        if 'email' in data:
            if not validate_email(data['email']):
                return error_response('Invalid email format', 400)
            
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email'].lower().strip()).first()
            if existing_user and existing_user.id != user.id:
                return error_response('Email already in use', 409)
            
            user.email = data['email'].lower().strip()
        
        if 'username' in data:
            if not validate_username(data['username']):
                return error_response('Username must be 3-20 characters and contain only letters, numbers, and underscores', 400)
            
            # Check if username is already taken by another user
            existing_user = User.query.filter_by(username=data['username'].lower().strip()).first()
            if existing_user and existing_user.id != user.id:
                return error_response('Username already taken', 409)
            
            user.username = data['username'].lower().strip()
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache after update
        cache_key = f"user_profile:{current_user_id}"
        CacheService.delete_cached(cache_key)
        
        # Also invalidate user settings cache
        settings_cache_key = f"user_settings:{current_user_id}"
        CacheService.delete_cached(settings_cache_key)
        
        return success_response({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update profile', 500)

@user_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get user settings with caching"""
    try:
        current_user_id = get_jwt_identity()
        
        # Try to get from cache first
        cache_key = f"user_settings:{current_user_id}"
        cached_settings = CacheService.get_cached(cache_key)
        
        if cached_settings:
            return success_response({
                'settings': cached_settings
            })
        
        # If not in cache, get from database
        user = User.query.get(current_user_id)
        if not user:
            return error_response('User not found', 404)
        
        settings = {
            'timezone': user.timezone,
            'language': user.language,
            'email_notifications': True,  # Default, can be extended
            'theme': 'light',  # Default, can be extended
            'created_at': user.created_at.isoformat(),
            'last_active': user.last_active.isoformat() if user.last_active else None
        }
        
        # Cache settings for 30 minutes
        CacheService.set_cached(cache_key, settings, 1800)
        
        return success_response({
            'settings': settings
        })
        
    except Exception as e:
        return error_response('Failed to get settings', 500)

@user_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update user settings and invalidate cache"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json()
        
        # Update allowed settings
        if 'timezone' in data:
            user.timezone = data['timezone']
        
        if 'language' in data:
            user.language = data['language']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate caches after update
        settings_cache_key = f"user_settings:{current_user_id}"
        CacheService.delete_cached(settings_cache_key)
        
        # Also invalidate profile cache since it contains user data
        profile_cache_key = f"user_profile:{current_user_id}"
        CacheService.delete_cached(profile_cache_key)
        
        return success_response({
            'message': 'Settings updated successfully',
            'settings': {
                'timezone': user.timezone,
                'language': user.language
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update settings', 500)

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return error_response('Current password and new password are required', 400)
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return error_response('Current password is incorrect', 401)
        
        # Validate new password
        if not validate_password(data['new_password']):
            return error_response('New password must be at least 8 characters long', 400)
        
        # Update password
        user.set_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate all user caches after password change
        profile_cache_key = f"user_profile:{current_user_id}"
        settings_cache_key = f"user_settings:{current_user_id}"
        CacheService.delete_cached(profile_cache_key)
        CacheService.delete_cached(settings_cache_key)
        
        return success_response({
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to change password', 500)

@user_bp.route('/workspaces', methods=['GET'])
@jwt_required()
def get_user_workspaces():
    """Get user's workspaces with caching"""
    try:
        current_user_id = get_jwt_identity()
        
        # Try to get from cache first
        cache_key = f"user_workspaces:{current_user_id}"
        cached_workspaces = CacheService.get_cached(cache_key)
        
        if cached_workspaces:
            return success_response({
                'workspaces': cached_workspaces
            })
        
        # If not in cache, get from database
        workspaces = db.session.query(Workspace).join(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user_id,
            WorkspaceMember.is_active == True
        ).all()
        
        workspace_data = []
        for workspace in workspaces:
            # Get user's role in this workspace
            membership = WorkspaceMember.query.filter_by(
                workspace_id=workspace.id,
                user_id=current_user_id
            ).first()
            
            workspace_info = workspace.to_dict()
            workspace_info['user_role'] = membership.role if membership else None
            workspace_data.append(workspace_info)
        
        # Cache workspaces for 10 minutes
        CacheService.set_cached(cache_key, workspace_data, 600)
        
        return success_response({
            'workspaces': workspace_data
        })
        
    except Exception as e:
        return error_response('Failed to get workspaces', 500)

