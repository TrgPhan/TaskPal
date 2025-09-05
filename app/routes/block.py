from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions.database import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.page import Page, PagePermission
from app.models.block import Block, BlockHistory
from app.utils.responses import success_response, error_response
from datetime import datetime
import uuid

block_bp = Blueprint('block', __name__)

def check_page_access(user_id, page_id, required_permission=None):
    """Check if user has access to page"""
    page = Page.query.get(page_id)
    if not page:
        return False, None, None
    
    # Check workspace access
    membership = WorkspaceMember.query.filter_by(
        workspace_id=page.workspace_id,
        user_id=user_id,
        is_active=True
    ).first()
    
    if not membership:
        return False, None, None
    
    # Check page permission
    permission = PagePermission.query.filter_by(
        page_id=page_id,
        user_id=user_id
    ).first()
    
    user_permission = None
    if permission:
        user_permission = permission.permission_type
    elif membership.role in ['owner', 'admin']:
        user_permission = 'full_access'
    
    if not user_permission:
        return False, None, None
    
    if required_permission and user_permission not in required_permission:
        return False, user_permission, membership.role
    
    return True, user_permission, membership.role

@block_bp.route('/', methods=['POST'])
@jwt_required()
def create_block():
    """Create a new block"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('page_id'):
            return error_response('Page ID is required', 400)
        
        if not data.get('type'):
            return error_response('Block type is required', 400)
        
        page_id = data['page_id']
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, page_id, ['write', 'full_access'])
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Check parent block access if specified
        parent_id = data.get('parent_id')
        if parent_id:
            parent_block = Block.query.get(parent_id)
            if not parent_block or parent_block.page_id != page_id:
                return error_response('Parent block not found', 404)
        
        # Create block
        block = Block(
            type=data['type'],
            content=data.get('content', {}),
            page_id=page_id,
            parent_id=parent_id,
            order_index=data.get('order_index', 0),
            depth=data.get('depth', 0),
            properties=data.get('properties', {}),
            has_children=data.get('has_children', False),
            is_toggleable=data.get('is_toggleable', False),
            is_expanded=data.get('is_expanded', True),
            created_by=current_user_id
        )
        
        # Extract plain text for search
        block.plain_text = block.extract_plain_text()
        
        db.session.add(block)
        db.session.flush()  # Get the block ID
        
        # Update parent's has_children flag
        if parent_id:
            parent_block.update_has_children()
        
        # Create history entry
        history = BlockHistory(
            block_id=block.id,
            version=block.version,
            content_snapshot=block.to_dict(),
            change_type='created',
            changed_by=current_user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return success_response({
            'message': 'Block created successfully',
            'block': block.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create block', 500)

@block_bp.route('/', methods=['GET'])
@jwt_required()
def get_blocks():
    """Get blocks for a page"""
    try:
        current_user_id = get_jwt_identity()
        page_id = request.args.get('page_id')
        
        if not page_id:
            return error_response('Page ID is required', 400)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, page_id)
        if not has_access:
            return error_response('Page not found or access denied', 404)
        
        # Get query parameters
        parent_id = request.args.get('parent_id')
        include_children = request.args.get('include_children', 'false').lower() == 'true'
        block_type = request.args.get('type')
        
        # Build query
        query = Block.query.filter_by(page_id=page_id)
        
        if parent_id:
            query = query.filter_by(parent_id=parent_id)
        else:
            query = query.filter_by(parent_id=None)  # Root blocks only
        
        if block_type:
            query = query.filter_by(type=block_type)
        
        # Order by order_index, then by created_at
        blocks = query.order_by(Block.order_index, Block.created_at).all()
        
        blocks_data = []
        for block in blocks:
            block_dict = block.to_dict(include_children=include_children)
            blocks_data.append(block_dict)
        
        return success_response({
            'blocks': blocks_data
        })
        
    except Exception as e:
        return error_response('Failed to get blocks', 500)

@block_bp.route('/<block_id>', methods=['GET'])
@jwt_required()
def get_block(block_id):
    """Get block details"""
    try:
        current_user_id = get_jwt_identity()
        
        block = Block.query.get(block_id)
        if not block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, block.page_id)
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        include_children = request.args.get('include_children', 'false').lower() == 'true'
        
        return success_response({
            'block': block.to_dict(include_children=include_children)
        })
        
    except Exception as e:
        return error_response('Failed to get block', 500)

@block_bp.route('/<block_id>', methods=['PUT'])
@jwt_required()
def update_block(block_id):
    """Update block"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        block = Block.query.get(block_id)
        if not block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, block.page_id, ['write', 'full_access'])
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        # Store old content for history
        old_content = block.to_dict()
        
        # Update allowed fields
        if 'type' in data:
            block.type = data['type']
        
        if 'content' in data:
            block.content = data['content']
        
        if 'properties' in data:
            block.properties = data['properties']
        
        if 'order_index' in data:
            block.order_index = data['order_index']
        
        if 'depth' in data:
            block.depth = data['depth']
        
        if 'is_toggleable' in data:
            block.is_toggleable = data['is_toggleable']
        
        if 'is_expanded' in data:
            block.is_expanded = data['is_expanded']
        
        # Update parent if specified
        if 'parent_id' in data:
            new_parent_id = data['parent_id']
            if new_parent_id:
                parent_block = Block.query.get(new_parent_id)
                if not parent_block or parent_block.page_id != block.page_id:
                    return error_response('Parent block not found', 404)
            
            old_parent_id = block.parent_id
            block.parent_id = new_parent_id
            
            # Update has_children flags
            if old_parent_id:
                old_parent = Block.query.get(old_parent_id)
                if old_parent:
                    old_parent.update_has_children()
            
            if new_parent_id:
                parent_block.update_has_children()
        
        # Extract plain text for search
        block.plain_text = block.extract_plain_text()
        
        block.last_edited_by = current_user_id
        block.last_edited_at = datetime.utcnow()
        block.updated_at = datetime.utcnow()
        block.version += 1
        
        # Create history entry
        history = BlockHistory(
            block_id=block.id,
            version=block.version,
            content_snapshot=block.to_dict(),
            change_type='updated',
            changed_by=current_user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return success_response({
            'message': 'Block updated successfully',
            'block': block.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update block', 500)

@block_bp.route('/<block_id>', methods=['DELETE'])
@jwt_required()
def delete_block(block_id):
    """Delete block"""
    try:
        current_user_id = get_jwt_identity()
        
        block = Block.query.get(block_id)
        if not block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, block.page_id, ['write', 'full_access'])
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        # Create history entry before deletion
        history = BlockHistory(
            block_id=block.id,
            version=block.version,
            content_snapshot=block.to_dict(),
            change_type='deleted',
            changed_by=current_user_id
        )
        
        db.session.add(history)
        
        # Update parent's has_children flag
        if block.parent_id:
            parent_block = Block.query.get(block.parent_id)
            if parent_block:
                parent_block.update_has_children()
        
        # Delete block (cascade will handle children)
        db.session.delete(block)
        db.session.commit()
        
        return success_response({
            'message': 'Block deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete block', 500)

@block_bp.route('/<block_id>/move', methods=['POST'])
@jwt_required()
def move_block(block_id):
    """Move block to different position or parent"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        block = Block.query.get(block_id)
        if not block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, block.page_id, ['write', 'full_access'])
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        # Validate required fields
        if 'order_index' not in data:
            return error_response('Order index is required', 400)
        
        old_parent_id = block.parent_id
        old_order_index = block.order_index
        
        # Update block position
        block.order_index = data['order_index']
        
        if 'parent_id' in data:
            new_parent_id = data['parent_id']
            if new_parent_id:
                parent_block = Block.query.get(new_parent_id)
                if not parent_block or parent_block.page_id != block.page_id:
                    return error_response('Parent block not found', 404)
            
            block.parent_id = new_parent_id
        
        if 'depth' in data:
            block.depth = data['depth']
        
        # Update has_children flags
        if old_parent_id != block.parent_id:
            if old_parent_id:
                old_parent = Block.query.get(old_parent_id)
                if old_parent:
                    old_parent.update_has_children()
            
            if block.parent_id:
                parent_block = Block.query.get(block.parent_id)
                if parent_block:
                    parent_block.update_has_children()
        
        block.last_edited_by = current_user_id
        block.last_edited_at = datetime.utcnow()
        block.updated_at = datetime.utcnow()
        block.version += 1
        
        # Create history entry
        history = BlockHistory(
            block_id=block.id,
            version=block.version,
            content_snapshot=block.to_dict(),
            change_type='moved',
            changed_by=current_user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return success_response({
            'message': 'Block moved successfully',
            'block': block.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to move block', 500)

@block_bp.route('/<block_id>/duplicate', methods=['POST'])
@jwt_required()
def duplicate_block(block_id):
    """Duplicate block"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        original_block = Block.query.get(block_id)
        if not original_block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, original_block.page_id, ['write', 'full_access'])
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        # Create duplicate block
        duplicate_block = Block(
            type=original_block.type,
            content=original_block.content,
            page_id=original_block.page_id,
            parent_id=data.get('parent_id', original_block.parent_id),
            order_index=data.get('order_index', original_block.order_index + 1),
            depth=data.get('depth', original_block.depth),
            properties=original_block.properties,
            has_children=False,  # Will be updated if children are duplicated
            is_toggleable=original_block.is_toggleable,
            is_expanded=original_block.is_expanded,
            created_by=current_user_id
        )
        
        # Extract plain text for search
        duplicate_block.plain_text = duplicate_block.extract_plain_text()
        
        db.session.add(duplicate_block)
        db.session.flush()  # Get the duplicate block ID
        
        # Duplicate children if requested
        include_children = data.get('include_children', True)
        if include_children and original_block.children:
            for child in original_block.children:
                duplicate_child = Block(
                    type=child.type,
                    content=child.content,
                    page_id=child.page_id,
                    parent_id=duplicate_block.id,
                    order_index=child.order_index,
                    depth=child.depth,
                    properties=child.properties,
                    has_children=child.has_children,
                    is_toggleable=child.is_toggleable,
                    is_expanded=child.is_expanded,
                    created_by=current_user_id
                )
                duplicate_child.plain_text = duplicate_child.extract_plain_text()
                db.session.add(duplicate_child)
        
        # Update parent's has_children flag
        if duplicate_block.parent_id:
            parent_block = Block.query.get(duplicate_block.parent_id)
            if parent_block:
                parent_block.update_has_children()
        
        # Create history entry
        history = BlockHistory(
            block_id=duplicate_block.id,
            version=duplicate_block.version,
            content_snapshot=duplicate_block.to_dict(),
            change_type='created',
            changed_by=current_user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return success_response({
            'message': 'Block duplicated successfully',
            'block': duplicate_block.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to duplicate block', 500)

@block_bp.route('/<block_id>/history', methods=['GET'])
@jwt_required()
def get_block_history(block_id):
    """Get block version history"""
    try:
        current_user_id = get_jwt_identity()
        
        block = Block.query.get(block_id)
        if not block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, block.page_id)
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        # Get history entries
        history_entries = BlockHistory.query.filter_by(block_id=block_id).order_by(BlockHistory.changed_at.desc()).all()
        
        history_data = []
        for entry in history_entries:
            entry_dict = entry.to_dict()
            # Add user information
            user = User.query.get(entry.changed_by)
            entry_dict['changed_by_user'] = user.to_dict() if user else None
            history_data.append(entry_dict)
        
        return success_response({
            'history': history_data
        })
        
    except Exception as e:
        return error_response('Failed to get block history', 500)

@block_bp.route('/<block_id>/restore/<version>', methods=['POST'])
@jwt_required()
def restore_block_version(block_id, version):
    """Restore block to a specific version"""
    try:
        current_user_id = get_jwt_identity()
        
        block = Block.query.get(block_id)
        if not block:
            return error_response('Block not found', 404)
        
        # Check page access
        has_access, user_permission, user_role = check_page_access(current_user_id, block.page_id, ['write', 'full_access'])
        if not has_access:
            return error_response('Block not found or access denied', 404)
        
        # Find history entry
        history_entry = BlockHistory.query.filter_by(
            block_id=block_id,
            version=int(version)
        ).first()
        
        if not history_entry:
            return error_response('Version not found', 404)
        
        # Store current content for history
        old_content = block.to_dict()
        
        # Restore from history
        content_snapshot = history_entry.content_snapshot
        block.type = content_snapshot['type']
        block.content = content_snapshot['content']
        block.properties = content_snapshot['properties']
        block.is_toggleable = content_snapshot['is_toggleable']
        block.is_expanded = content_snapshot['is_expanded']
        
        # Extract plain text for search
        block.plain_text = block.extract_plain_text()
        
        block.last_edited_by = current_user_id
        block.last_edited_at = datetime.utcnow()
        block.updated_at = datetime.utcnow()
        block.version += 1
        
        # Create history entry for restoration
        history = BlockHistory(
            block_id=block.id,
            version=block.version,
            content_snapshot=block.to_dict(),
            change_type='updated',
            changed_by=current_user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return success_response({
            'message': f'Block restored to version {version}',
            'block': block.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to restore block version', 500)

@block_bp.route('/search', methods=['GET'])
@jwt_required()
def search_blocks():
    """Search blocks by content"""
    try:
        current_user_id = get_jwt_identity()
        query = request.args.get('q')
        page_id = request.args.get('page_id')
        workspace_id = request.args.get('workspace_id')
        
        if not query:
            return error_response('Search query is required', 400)
        
        # Build search query
        search_query = Block.query.filter(Block.plain_text.contains(query))
        
        if page_id:
            # Check page access
            has_access, user_permission, user_role = check_page_access(current_user_id, page_id)
            if not has_access:
                return error_response('Page not found or access denied', 404)
            search_query = search_query.filter_by(page_id=page_id)
        
        elif workspace_id:
            # Check workspace access
            membership = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                user_id=current_user_id,
                is_active=True
            ).first()
            
            if not membership:
                return error_response('Workspace not found or access denied', 404)
            
            # Get accessible pages in workspace
            accessible_pages = db.session.query(Page.id).join(PagePermission).filter(
                Page.workspace_id == workspace_id,
                PagePermission.user_id == current_user_id
            ).union(
                db.session.query(Page.id).join(WorkspaceMember).filter(
                    Page.workspace_id == workspace_id,
                    WorkspaceMember.user_id == current_user_id,
                    WorkspaceMember.role.in_(['owner', 'admin']),
                    WorkspaceMember.is_active == True
                )
            ).subquery()
            
            search_query = search_query.filter(Block.page_id.in_(accessible_pages))
        
        # Execute search
        blocks = search_query.order_by(Block.updated_at.desc()).limit(50).all()
        
        blocks_data = []
        for block in blocks:
            block_dict = block.to_dict()
            # Add page information
            page = Page.query.get(block.page_id)
            block_dict['page'] = {
                'id': page.id,
                'title': page.title,
                'workspace_id': page.workspace_id
            } if page else None
            blocks_data.append(block_dict)
        
        return success_response({
            'blocks': blocks_data,
            'query': query,
            'total': len(blocks_data)
        })
        
    except Exception as e:
        return error_response('Failed to search blocks', 500)
