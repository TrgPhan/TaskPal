from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions.database import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.page import Page, PageTemplate, PagePermission
from app.utils.responses import success_response, error_response
from datetime import datetime
import uuid
import re

page_bp = Blueprint('page', __name__)

def check_workspace_access(user_id, workspace_id, required_role=None):
    """Check if user has access to workspace"""
    membership = WorkspaceMember.query.filter_by(
        workspace_id=workspace_id,
        user_id=user_id,
        is_active=True
    ).first()
    
    if not membership:
        return False, None
    
    if required_role and membership.role not in required_role:
        return False, membership.role
    
    return True, membership.role

def generate_slug(title):
    """Generate URL-friendly slug from title"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

@page_bp.route('/', methods=['POST'])
@jwt_required()
def create_page():
    """Create a new page"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('workspace_id'):
            return error_response('Workspace ID is required', 400)
        
        if not data.get('title'):
            return error_response('Page title is required', 400)
        
        workspace_id = data['workspace_id']
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, workspace_id)
        if not has_access:
            return error_response('Workspace not found or access denied', 404)
        
        # Check parent page access if specified
        parent_id = data.get('parent_id')
        if parent_id:
            parent_page = Page.query.get(parent_id)
            if not parent_page or parent_page.workspace_id != workspace_id:
                return error_response('Parent page not found', 404)
        
        # Create page
        page = Page(
            title=data['title'].strip(),
            icon=data.get('icon'),
            cover_image=data.get('cover_image'),
            workspace_id=workspace_id,
            parent_id=parent_id,
            slug=generate_slug(data['title']),
            content_text=data.get('content_text', ''),
            template_id=data.get('template_id'),
            properties=data.get('properties', {}),
            is_public=data.get('is_public', False),
            is_template=data.get('is_template', False),
            created_by=current_user_id
        )
        
        # Update path and level
        page.update_path()
        
        db.session.add(page)
        db.session.flush()  # Get the page ID
        
        # Create page permission for creator
        permission = PagePermission(
            page_id=page.id,
            user_id=current_user_id,
            permission_type='full_access',
            granted_by=current_user_id
        )
        
        db.session.add(permission)
        db.session.commit()
        
        return success_response({
            'message': 'Page created successfully',
            'page': page.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create page', 500)

@page_bp.route('/', methods=['GET'])
@jwt_required()
def get_pages():
    """Get pages for a workspace"""
    try:
        current_user_id = get_jwt_identity()
        workspace_id = request.args.get('workspace_id')
        
        if not workspace_id:
            return error_response('Workspace ID is required', 400)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, workspace_id)
        if not has_access:
            return error_response('Workspace not found or access denied', 404)
        
        # Get query parameters
        parent_id = request.args.get('parent_id')
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        
        # Build query
        query = Page.query.filter_by(workspace_id=workspace_id)
        
        if parent_id:
            query = query.filter_by(parent_id=parent_id)
        else:
            query = query.filter_by(parent_id=None)  # Root pages only
        
        if not include_archived:
            query = query.filter_by(is_archived=False)
        
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        
        # Order by order_index, then by created_at
        pages = query.order_by(Page.order_index, Page.created_at).all()
        
        pages_data = []
        for page in pages:
            # Check if user has permission to view this page
            has_permission = PagePermission.query.filter_by(
                page_id=page.id,
                user_id=current_user_id
            ).first()
            
            # If no specific permission, check workspace role
            if not has_permission and user_role in ['owner', 'admin']:
                has_permission = True
            
            if has_permission:
                pages_data.append(page.to_dict())
        
        return success_response({
            'pages': pages_data
        })
        
    except Exception as e:
        return error_response('Failed to get pages', 500)

@page_bp.route('/<page_id>', methods=['GET'])
@jwt_required()
def get_page(page_id):
    """Get page details"""
    try:
        current_user_id = get_jwt_identity()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check page permission
        has_permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        if not has_permission and user_role not in ['owner', 'admin']:
            return error_response('Page not found or access denied', 404)
        
        include_blocks = request.args.get('include_blocks', 'false').lower() == 'true'
        
        return success_response({
            'page': page.to_dict(include_blocks=include_blocks)
        })
        
    except Exception as e:
        return error_response('Failed to get page', 500)

@page_bp.route('/<page_id>', methods=['PUT'])
@jwt_required()
def update_page(page_id):
    """Update page"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check page permission
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_edit = False
        if permission and permission.permission_type in ['write', 'full_access']:
            can_edit = True
        elif user_role in ['owner', 'admin']:
            can_edit = True
        
        if not can_edit:
            return error_response('Insufficient permissions to edit page', 403)
        
        # Update allowed fields
        if 'title' in data:
            page.title = data['title'].strip()
            page.slug = generate_slug(data['title'])
        
        if 'icon' in data:
            page.icon = data['icon']
        
        if 'cover_image' in data:
            page.cover_image = data['cover_image']
        
        if 'content_text' in data:
            page.content_text = data['content_text']
        
        if 'properties' in data:
            page.properties = data['properties']
        
        if 'is_public' in data:
            page.is_public = data['is_public']
        
        if 'is_template' in data:
            page.is_template = data['is_template']
        
        # Update parent if specified
        if 'parent_id' in data:
            new_parent_id = data['parent_id']
            if new_parent_id:
                parent_page = Page.query.get(new_parent_id)
                if not parent_page or parent_page.workspace_id != page.workspace_id:
                    return error_response('Parent page not found', 404)
            page.parent_id = new_parent_id
            page.update_path()
        
        # Update order index
        if 'order_index' in data:
            page.order_index = data['order_index']
        
        page.last_edited_by = current_user_id
        page.last_edited_at = datetime.utcnow()
        page.updated_at = datetime.utcnow()
        page.version += 1
        
        db.session.commit()
        
        return success_response({
            'message': 'Page updated successfully',
            'page': page.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update page', 500)

@page_bp.route('/<page_id>', methods=['DELETE'])
@jwt_required()
def delete_page(page_id):
    """Delete page (soft delete)"""
    try:
        current_user_id = get_jwt_identity()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check page permission
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_delete = False
        if permission and permission.permission_type == 'full_access':
            can_delete = True
        elif user_role in ['owner', 'admin']:
            can_delete = True
        
        if not can_delete:
            return error_response('Insufficient permissions to delete page', 403)
        
        # Soft delete
        page.is_deleted = True
        page.updated_at = datetime.utcnow()
        page.last_edited_by = current_user_id
        page.last_edited_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response({
            'message': 'Page deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete page', 500)

@page_bp.route('/<page_id>/restore', methods=['POST'])
@jwt_required()
def restore_page(page_id):
    """Restore deleted page"""
    try:
        current_user_id = get_jwt_identity()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check page permission
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_restore = False
        if permission and permission.permission_type == 'full_access':
            can_restore = True
        elif user_role in ['owner', 'admin']:
            can_restore = True
        
        if not can_restore:
            return error_response('Insufficient permissions to restore page', 403)
        
        # Restore page
        page.is_deleted = False
        page.updated_at = datetime.utcnow()
        page.last_edited_by = current_user_id
        page.last_edited_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response({
            'message': 'Page restored successfully',
            'page': page.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to restore page', 500)

@page_bp.route('/<page_id>/archive', methods=['POST'])
@jwt_required()
def archive_page(page_id):
    """Archive page"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check page permission
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_archive = False
        if permission and permission.permission_type in ['write', 'full_access']:
            can_archive = True
        elif user_role in ['owner', 'admin']:
            can_archive = True
        
        if not can_archive:
            return error_response('Insufficient permissions to archive page', 403)
        
        # Archive/unarchive page
        is_archived = data.get('is_archived', True)
        page.is_archived = is_archived
        page.updated_at = datetime.utcnow()
        page.last_edited_by = current_user_id
        page.last_edited_at = datetime.utcnow()
        
        db.session.commit()
        
        action = 'archived' if is_archived else 'unarchived'
        return success_response({
            'message': f'Page {action} successfully',
            'page': page.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to archive page', 500)

@page_bp.route('/<page_id>/permissions', methods=['GET'])
@jwt_required()
def get_page_permissions(page_id):
    """Get page permissions"""
    try:
        current_user_id = get_jwt_identity()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check if user can manage permissions
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_manage = False
        if permission and permission.permission_type == 'full_access':
            can_manage = True
        elif user_role in ['owner', 'admin']:
            can_manage = True
        
        if not can_manage:
            return error_response('Insufficient permissions to view page permissions', 403)
        
        # Get all permissions for this page
        permissions = PagePermission.query.filter_by(page_id=page_id).all()
        
        permissions_data = []
        for perm in permissions:
            perm_data = perm.to_dict()
            if perm.user_id:
                user = User.query.get(perm.user_id)
                perm_data['user'] = user.to_dict() if user else None
            permissions_data.append(perm_data)
        
        return success_response({
            'permissions': permissions_data
        })
        
    except Exception as e:
        return error_response('Failed to get page permissions', 500)

@page_bp.route('/<page_id>/permissions', methods=['POST'])
@jwt_required()
def grant_page_permission(page_id):
    """Grant permission to user for page"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check if user can manage permissions
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_manage = False
        if permission and permission.permission_type == 'full_access':
            can_manage = True
        elif user_role in ['owner', 'admin']:
            can_manage = True
        
        if not can_manage:
            return error_response('Insufficient permissions to manage page permissions', 403)
        
        # Validate required fields
        if not data.get('user_id'):
            return error_response('User ID is required', 400)
        
        if not data.get('permission_type'):
            return error_response('Permission type is required', 400)
        
        # Check if user exists
        user = User.query.get(data['user_id'])
        if not user:
            return error_response('User not found', 404)
        
        # Check if permission already exists
        existing_permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=data['user_id']
        ).first()
        
        if existing_permission:
            # Update existing permission
            existing_permission.permission_type = data['permission_type']
            existing_permission.granted_by = current_user_id
            existing_permission.granted_at = datetime.utcnow()
            db.session.commit()
            
            return success_response({
                'message': 'Permission updated successfully',
                'permission': existing_permission.to_dict()
            })
        
        # Create new permission
        new_permission = PagePermission(
            page_id=page_id,
            user_id=data['user_id'],
            permission_type=data['permission_type'],
            granted_by=current_user_id
        )
        
        db.session.add(new_permission)
        db.session.commit()
        
        return success_response({
            'message': 'Permission granted successfully',
            'permission': new_permission.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to grant permission', 500)

@page_bp.route('/<page_id>/permissions/<permission_id>', methods=['DELETE'])
@jwt_required()
def revoke_page_permission(page_id, permission_id):
    """Revoke page permission"""
    try:
        current_user_id = get_jwt_identity()
        
        page = Page.query.get(page_id)
        if not page:
            return error_response('Page not found', 404)
        
        # Check workspace access
        has_access, user_role = check_workspace_access(current_user_id, page.workspace_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check if user can manage permissions
        permission = PagePermission.query.filter_by(
            page_id=page_id,
            user_id=current_user_id
        ).first()
        
        can_manage = False
        if permission and permission.permission_type == 'full_access':
            can_manage = True
        elif user_role in ['owner', 'admin']:
            can_manage = True
        
        if not can_manage:
            return error_response('Insufficient permissions to manage page permissions', 403)
        
        # Find permission to revoke
        permission_to_revoke = PagePermission.query.get(permission_id)
        if not permission_to_revoke or permission_to_revoke.page_id != page_id:
            return error_response('Permission not found', 404)
        
        db.session.delete(permission_to_revoke)
        db.session.commit()
        
        return success_response({
            'message': 'Permission revoked successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to revoke permission', 500)

@page_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_page_templates():
    """Get page templates"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get public templates and user's own templates
        templates = PageTemplate.query.filter(
            (PageTemplate.is_public == True) | (PageTemplate.created_by == current_user_id)
        ).all()
        
        templates_data = [template.to_dict() for template in templates]
        
        return success_response({
            'templates': templates_data
        })
        
    except Exception as e:
        return error_response('Failed to get page templates', 500)

@page_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_page_template():
    """Create page template"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return error_response('Template name is required', 400)
        
        if not data.get('template_data'):
            return error_response('Template data is required', 400)
        
        # Create template
        template = PageTemplate(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            icon=data.get('icon'),
            template_data=data['template_data'],
            category=data.get('category'),
            is_public=data.get('is_public', False),
            created_by=current_user_id
        )
        
        db.session.add(template)
        db.session.commit()
        
        return success_response({
            'message': 'Template created successfully',
            'template': template.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create template', 500)
