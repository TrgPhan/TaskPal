from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions.database import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.utils.responses import success_response, error_response
from datetime import datetime
import uuid

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/', methods=['POST'])
@jwt_required()
def create_workspace():
    """Create a new workspace"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return error_response('Workspace name is required', 400)
        
        # Create workspace
        workspace = Workspace(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            icon=data.get('icon'),
            cover_image=data.get('cover_image'),
            owner_id=current_user_id,
            is_public=data.get('is_public', False),
            settings=data.get('settings', {})
        )
        
        # Generate invite code if public
        if workspace.is_public:
            workspace.generate_invite_code()
        
        db.session.add(workspace)
        db.session.flush()  # Get the workspace ID
        
        # Add owner as workspace member
        owner_member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user_id,
            role='owner',
            permissions={},
            invited_by=None
        )
        
        db.session.add(owner_member)
        db.session.commit()
        
        return success_response({
            'message': 'Workspace created successfully',
            'workspace': workspace.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create workspace', 500)

@workspace_bp.route('/', methods=['GET'])
@jwt_required()
def get_workspaces():
    """Get user's workspaces"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get workspaces where user is a member
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
        
        return success_response({
            'workspaces': workspace_data
        })
        
    except Exception as e:
        return error_response('Failed to get workspaces', 500)

@workspace_bp.route('/<workspace_id>', methods=['GET'])
@jwt_required()
def get_workspace(workspace_id):
    """Get workspace details"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user has access to workspace
        membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not membership:
            return error_response('Workspace not found or access denied', 404)
        
        workspace = Workspace.query.get(workspace_id)
        if not workspace:
            return error_response('Workspace not found', 404)
        
        workspace_data = workspace.to_dict()
        workspace_data['user_role'] = membership.role
        workspace_data['user_permissions'] = membership.permissions
        
        return success_response({
            'workspace': workspace_data
        })
        
    except Exception as e:
        return error_response('Failed to get workspace', 500)

@workspace_bp.route('/<workspace_id>', methods=['PUT'])
@jwt_required()
def update_workspace(workspace_id):
    """Update workspace"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if user has permission to update workspace
        membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not membership or membership.role not in ['owner', 'admin']:
            return error_response('Insufficient permissions', 403)
        
        workspace = Workspace.query.get(workspace_id)
        if not workspace:
            return error_response('Workspace not found', 404)
        
        # Update allowed fields
        if 'name' in data:
            workspace.name = data['name'].strip()
        
        if 'description' in data:
            workspace.description = data['description'].strip()
        
        if 'icon' in data:
            workspace.icon = data['icon']
        
        if 'cover_image' in data:
            workspace.cover_image = data['cover_image']
        
        if 'is_public' in data:
            workspace.is_public = data['is_public']
            # Generate invite code if becoming public
            if workspace.is_public and not workspace.invite_code:
                workspace.generate_invite_code()
        
        if 'settings' in data:
            workspace.settings = data['settings']
        
        workspace.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response({
            'message': 'Workspace updated successfully',
            'workspace': workspace.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update workspace', 500)

@workspace_bp.route('/<workspace_id>', methods=['DELETE'])
@jwt_required()
def delete_workspace(workspace_id):
    """Delete workspace (only owner can delete)"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user is the owner
        workspace = Workspace.query.get(workspace_id)
        if not workspace:
            return error_response('Workspace not found', 404)
        
        if workspace.owner_id != current_user_id:
            return error_response('Only workspace owner can delete workspace', 403)
        
        db.session.delete(workspace)
        db.session.commit()
        
        return success_response({
            'message': 'Workspace deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete workspace', 500)

@workspace_bp.route('/<workspace_id>/members', methods=['GET'])
@jwt_required()
def get_workspace_members(workspace_id):
    """Get workspace members"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user has access to workspace
        membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not membership:
            return error_response('Workspace not found or access denied', 404)
        
        # Get all active members
        members = db.session.query(WorkspaceMember, User).join(User).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).all()
        
        members_data = []
        for member, user in members:
            member_data = member.to_dict()
            member_data['user'] = user.to_dict()
            members_data.append(member_data)
        
        return success_response({
            'members': members_data
        })
        
    except Exception as e:
        return error_response('Failed to get workspace members', 500)

@workspace_bp.route('/<workspace_id>/members', methods=['POST'])
@jwt_required()
def invite_member(workspace_id):
    """Invite user to workspace"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if user has permission to invite
        membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not membership or membership.role not in ['owner', 'admin']:
            return error_response('Insufficient permissions', 403)
        
        # Validate required fields
        if not data.get('email') and not data.get('user_id'):
            return error_response('Email or user_id is required', 400)
        
        # Find user to invite
        if data.get('user_id'):
            user = User.query.get(data['user_id'])
        else:
            user = User.query.filter_by(email=data['email'].lower().strip()).first()
        
        if not user:
            return error_response('User not found', 404)
        
        # Check if user is already a member
        existing_member = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=user.id
        ).first()
        
        if existing_member:
            if existing_member.is_active:
                return error_response('User is already a member', 409)
            else:
                # Reactivate existing membership
                existing_member.is_active = True
                existing_member.role = data.get('role', 'member')
                existing_member.invited_by = current_user_id
                existing_member.joined_at = datetime.utcnow()
                db.session.commit()
                
                return success_response({
                    'message': 'User re-invited successfully',
                    'member': existing_member.to_dict()
                })
        
        # Create new membership
        new_member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.id,
            role=data.get('role', 'member'),
            permissions=data.get('permissions', {}),
            invited_by=current_user_id
        )
        
        db.session.add(new_member)
        db.session.commit()
        
        return success_response({
            'message': 'User invited successfully',
            'member': new_member.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to invite user', 500)

@workspace_bp.route('/<workspace_id>/members/<user_id>', methods=['PUT'])
@jwt_required()
def update_member_role(workspace_id, user_id):
    """Update member role"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if current user has permission to update roles
        current_membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not current_membership or current_membership.role not in ['owner', 'admin']:
            return error_response('Insufficient permissions', 403)
        
        # Find member to update
        member = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not member:
            return error_response('Member not found', 404)
        
        # Prevent non-owners from changing owner role
        if member.role == 'owner' and current_membership.role != 'owner':
            return error_response('Only owner can change owner role', 403)
        
        # Update role and permissions
        if 'role' in data:
            member.role = data['role']
        
        if 'permissions' in data:
            member.permissions = data['permissions']
        
        db.session.commit()
        
        return success_response({
            'message': 'Member role updated successfully',
            'member': member.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update member role', 500)

@workspace_bp.route('/<workspace_id>/members/<user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(workspace_id, user_id):
    """Remove member from workspace"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if current user has permission to remove members
        current_membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not current_membership or current_membership.role not in ['owner', 'admin']:
            return error_response('Insufficient permissions', 403)
        
        # Find member to remove
        member = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not member:
            return error_response('Member not found', 404)
        
        # Prevent removing owner
        if member.role == 'owner':
            return error_response('Cannot remove workspace owner', 403)
        
        # Deactivate membership instead of deleting
        member.is_active = False
        db.session.commit()
        
        return success_response({
            'message': 'Member removed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to remove member', 500)

@workspace_bp.route('/join/<invite_code>', methods=['POST'])
@jwt_required()
def join_workspace(invite_code):
    """Join workspace using invite code"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find workspace by invite code
        workspace = Workspace.query.filter_by(invite_code=invite_code).first()
        if not workspace:
            return error_response('Invalid invite code', 404)
        
        # Check if user is already a member
        existing_member = WorkspaceMember.query.filter_by(
            workspace_id=workspace.id,
            user_id=current_user_id
        ).first()
        
        if existing_member:
            if existing_member.is_active:
                return error_response('You are already a member of this workspace', 409)
            else:
                # Reactivate membership
                existing_member.is_active = True
                existing_member.role = 'member'
                existing_member.joined_at = datetime.utcnow()
                db.session.commit()
                
                return success_response({
                    'message': 'Successfully rejoined workspace',
                    'workspace': workspace.to_dict()
                })
        
        # Create new membership
        new_member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user_id,
            role='member',
            permissions={}
        )
        
        db.session.add(new_member)
        db.session.commit()
        
        return success_response({
            'message': 'Successfully joined workspace',
            'workspace': workspace.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to join workspace', 500)

@workspace_bp.route('/<workspace_id>/leave', methods=['POST'])
@jwt_required()
def leave_workspace(workspace_id):
    """Leave workspace"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find membership
        membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not membership:
            return error_response('You are not a member of this workspace', 404)
        
        # Prevent owner from leaving
        if membership.role == 'owner':
            return error_response('Workspace owner cannot leave. Transfer ownership or delete workspace.', 403)
        
        # Deactivate membership
        membership.is_active = False
        db.session.commit()
        
        return success_response({
            'message': 'Successfully left workspace'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to leave workspace', 500)
