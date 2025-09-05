from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions.database import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.page import Page, PagePermission
from app.models.block import Block
from app.models.comment import Comment, CommentReaction, CommentMention
from app.utils.responses import success_response, error_response
from datetime import datetime
import uuid
import re

comment_bp = Blueprint('comment', __name__)

def check_comment_access(user_id, page_id=None, block_id=None):
    """Check if user has access to comment on page or block"""
    if page_id:
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
        
        return bool(user_permission), user_permission, membership.role
    
    elif block_id:
        block = Block.query.get(block_id)
        if not block:
            return False, None, None
        
        # Check page access through block
        return check_comment_access(user_id, page_id=block.page_id)
    
    return False, None, None

def extract_mentions(content):
    """Extract @mentions from comment content"""
    mentions = []
    if isinstance(content, dict) and 'rich_text' in content:
        for text_item in content['rich_text']:
            if 'plain_text' in text_item:
                text = text_item['plain_text']
                # Find @username patterns
                mention_pattern = r'@(\w+)'
                matches = re.findall(mention_pattern, text)
                for username in matches:
                    mentions.append(username)
    return mentions

@comment_bp.route('/', methods=['POST'])
@jwt_required()
def create_comment():
    """Create a new comment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('content'):
            return error_response('Comment content is required', 400)
        
        page_id = data.get('page_id')
        block_id = data.get('block_id')
        
        if not page_id and not block_id:
            return error_response('Either page_id or block_id is required', 400)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, page_id, block_id)
        if not has_access:
            return error_response('Access denied', 403)
        
        # Check if user has comment permission
        if user_permission not in ['comment', 'write', 'full_access']:
            return error_response('Insufficient permissions to comment', 403)
        
        # Get thread_id (for replies, use parent's thread_id)
        parent_id = data.get('parent_id')
        thread_id = None
        
        if parent_id:
            parent_comment = Comment.query.get(parent_id)
            if not parent_comment:
                return error_response('Parent comment not found', 404)
            
            # Ensure parent comment is on same page/block
            if parent_comment.page_id != page_id or parent_comment.block_id != block_id:
                return error_response('Parent comment must be on same page/block', 400)
            
            thread_id = parent_comment.thread_id
        else:
            thread_id = str(uuid.uuid4())  # New thread
        
        # Create comment
        comment = Comment(
            content=data['content'],
            page_id=page_id,
            block_id=block_id,
            parent_id=parent_id,
            thread_id=thread_id,
            author_id=current_user_id
        )
        
        # Extract plain text for search
        comment.plain_text = comment.extract_plain_text()
        
        db.session.add(comment)
        db.session.flush()  # Get the comment ID
        
        # Handle mentions
        mentions = extract_mentions(data['content'])
        for username in mentions:
            # Find user by username
            user = User.query.filter_by(username=username.lower()).first()
            if user and user.id != current_user_id:
                mention = CommentMention(
                    comment_id=comment.id,
                    mentioned_user_id=user.id,
                    mention_text=f'@{username}'
                )
                db.session.add(mention)
        
        db.session.commit()
        
        return success_response({
            'message': 'Comment created successfully',
            'comment': comment.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create comment', 500)

@comment_bp.route('/', methods=['GET'])
@jwt_required()
def get_comments():
    """Get comments for a page or block"""
    try:
        current_user_id = get_jwt_identity()
        page_id = request.args.get('page_id')
        block_id = request.args.get('block_id')
        
        if not page_id and not block_id:
            return error_response('Either page_id or block_id is required', 400)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, page_id, block_id)
        if not has_access:
            return error_response('Access denied', 403)
        
        # Get query parameters
        thread_id = request.args.get('thread_id')
        include_replies = request.args.get('include_replies', 'true').lower() == 'true'
        resolved_only = request.args.get('resolved_only', 'false').lower() == 'true'
        
        # Build query
        query = Comment.query
        
        if page_id:
            query = query.filter_by(page_id=page_id)
        if block_id:
            query = query.filter_by(block_id=block_id)
        
        if thread_id:
            query = query.filter_by(thread_id=thread_id)
        else:
            # Only top-level comments (no parent)
            query = query.filter_by(parent_id=None)
        
        if resolved_only:
            query = query.filter_by(is_resolved=True)
        
        # Order by creation time
        comments = query.order_by(Comment.created_at.asc()).all()
        
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict(include_replies=include_replies)
            # Add author information
            author = User.query.get(comment.author_id)
            comment_dict['author'] = author.to_dict() if author else None
            
            # Add mentions
            mentions = CommentMention.query.filter_by(comment_id=comment.id).all()
            comment_dict['mentions'] = [mention.to_dict() for mention in mentions]
            
            comments_data.append(comment_dict)
        
        return success_response({
            'comments': comments_data
        })
        
    except Exception as e:
        return error_response('Failed to get comments', 500)

@comment_bp.route('/<comment_id>', methods=['GET'])
@jwt_required()
def get_comment(comment_id):
    """Get comment details"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return error_response('Comment not found', 404)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, comment.page_id, comment.block_id)
        if not has_access:
            return error_response('Comment not found or access denied', 404)
        
        include_replies = request.args.get('include_replies', 'true').lower() == 'true'
        
        comment_dict = comment.to_dict(include_replies=include_replies)
        
        # Add author information
        author = User.query.get(comment.author_id)
        comment_dict['author'] = author.to_dict() if author else None
        
        # Add mentions
        mentions = CommentMention.query.filter_by(comment_id=comment.id).all()
        comment_dict['mentions'] = [mention.to_dict() for mention in mentions]
        
        # Add reactions
        reactions = CommentReaction.query.filter_by(comment_id=comment.id).all()
        comment_dict['reactions'] = [reaction.to_dict() for reaction in reactions]
        
        return success_response({
            'comment': comment_dict
        })
        
    except Exception as e:
        return error_response('Failed to get comment', 500)

@comment_bp.route('/<comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Update comment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return error_response('Comment not found', 404)
        
        # Check if user is the author
        if comment.author_id != current_user_id:
            return error_response('Only comment author can edit comment', 403)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, comment.page_id, comment.block_id)
        if not has_access:
            return error_response('Comment not found or access denied', 404)
        
        # Update content
        if 'content' in data:
            comment.content = data['content']
            comment.plain_text = comment.extract_plain_text()
            comment.last_edited_at = datetime.utcnow()
        
        comment.updated_at = datetime.utcnow()
        
        # Update mentions if content changed
        if 'content' in data:
            # Remove old mentions
            CommentMention.query.filter_by(comment_id=comment.id).delete()
            
            # Add new mentions
            mentions = extract_mentions(data['content'])
            for username in mentions:
                user = User.query.filter_by(username=username.lower()).first()
                if user and user.id != current_user_id:
                    mention = CommentMention(
                        comment_id=comment.id,
                        mentioned_user_id=user.id,
                        mention_text=f'@{username}'
                    )
                    db.session.add(mention)
        
        db.session.commit()
        
        return success_response({
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update comment', 500)

@comment_bp.route('/<comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete comment"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return error_response('Comment not found', 404)
        
        # Check if user is the author or has admin access
        has_access, user_permission, user_role = check_comment_access(current_user_id, comment.page_id, comment.block_id)
        if not has_access:
            return error_response('Comment not found or access denied', 404)
        
        can_delete = False
        if comment.author_id == current_user_id:
            can_delete = True
        elif user_permission in ['write', 'full_access'] or user_role in ['owner', 'admin']:
            can_delete = True
        
        if not can_delete:
            return error_response('Insufficient permissions to delete comment', 403)
        
        # Delete comment (cascade will handle replies, reactions, mentions)
        db.session.delete(comment)
        db.session.commit()
        
        return success_response({
            'message': 'Comment deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete comment', 500)

@comment_bp.route('/<comment_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_comment(comment_id):
    """Resolve/unresolve comment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return error_response('Comment not found', 404)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, comment.page_id, comment.block_id)
        if not has_access:
            return error_response('Comment not found or access denied', 404)
        
        # Check if user can resolve comments
        can_resolve = False
        if user_permission in ['write', 'full_access'] or user_role in ['owner', 'admin']:
            can_resolve = True
        
        if not can_resolve:
            return error_response('Insufficient permissions to resolve comment', 403)
        
        # Toggle resolved status
        is_resolved = data.get('is_resolved', not comment.is_resolved)
        comment.is_resolved = is_resolved
        
        if is_resolved:
            comment.resolved_by = current_user_id
            comment.resolved_at = datetime.utcnow()
        else:
            comment.resolved_by = None
            comment.resolved_at = None
        
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        
        action = 'resolved' if is_resolved else 'unresolved'
        return success_response({
            'message': f'Comment {action} successfully',
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to resolve comment', 500)

@comment_bp.route('/<comment_id>/reactions', methods=['POST'])
@jwt_required()
def add_reaction(comment_id):
    """Add reaction to comment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return error_response('Comment not found', 404)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, comment.page_id, comment.block_id)
        if not has_access:
            return error_response('Comment not found or access denied', 404)
        
        # Validate emoji
        emoji = data.get('emoji')
        if not emoji:
            return error_response('Emoji is required', 400)
        
        # Check if reaction already exists
        existing_reaction = CommentReaction.query.filter_by(
            comment_id=comment_id,
            user_id=current_user_id,
            emoji=emoji
        ).first()
        
        if existing_reaction:
            return error_response('Reaction already exists', 409)
        
        # Create reaction
        reaction = CommentReaction(
            comment_id=comment_id,
            user_id=current_user_id,
            emoji=emoji
        )
        
        db.session.add(reaction)
        db.session.commit()
        
        return success_response({
            'message': 'Reaction added successfully',
            'reaction': reaction.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to add reaction', 500)

@comment_bp.route('/<comment_id>/reactions/<reaction_id>', methods=['DELETE'])
@jwt_required()
def remove_reaction(comment_id, reaction_id):
    """Remove reaction from comment"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return error_response('Comment not found', 404)
        
        # Check access
        has_access, user_permission, user_role = check_comment_access(current_user_id, comment.page_id, comment.block_id)
        if not has_access:
            return error_response('Comment not found or access denied', 404)
        
        # Find reaction
        reaction = CommentReaction.query.get(reaction_id)
        if not reaction or reaction.comment_id != comment_id:
            return error_response('Reaction not found', 404)
        
        # Check if user owns the reaction
        if reaction.user_id != current_user_id:
            return error_response('Only reaction owner can remove reaction', 403)
        
        db.session.delete(reaction)
        db.session.commit()
        
        return success_response({
            'message': 'Reaction removed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to remove reaction', 500)

@comment_bp.route('/mentions', methods=['GET'])
@jwt_required()
def get_mentions():
    """Get user's mentions"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get unread mentions
        mentions = db.session.query(CommentMention, Comment, User).join(
            Comment, CommentMention.comment_id == Comment.id
        ).join(
            User, Comment.author_id == User.id
        ).filter(
            CommentMention.mentioned_user_id == current_user_id,
            CommentMention.is_read == False
        ).order_by(CommentMention.created_at.desc()).all()
        
        mentions_data = []
        for mention, comment, author in mentions:
            mention_dict = mention.to_dict()
            mention_dict['comment'] = comment.to_dict()
            mention_dict['author'] = author.to_dict()
            mentions_data.append(mention_dict)
        
        return success_response({
            'mentions': mentions_data
        })
        
    except Exception as e:
        return error_response('Failed to get mentions', 500)

@comment_bp.route('/mentions/<mention_id>/read', methods=['POST'])
@jwt_required()
def mark_mention_read(mention_id):
    """Mark mention as read"""
    try:
        current_user_id = get_jwt_identity()
        
        mention = CommentMention.query.get(mention_id)
        if not mention:
            return error_response('Mention not found', 404)
        
        # Check if user is the mentioned user
        if mention.mentioned_user_id != current_user_id:
            return error_response('Access denied', 403)
        
        mention.is_read = True
        db.session.commit()
        
        return success_response({
            'message': 'Mention marked as read'
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to mark mention as read', 500)

@comment_bp.route('/search', methods=['GET'])
@jwt_required()
def search_comments():
    """Search comments by content"""
    try:
        current_user_id = get_jwt_identity()
        query = request.args.get('q')
        page_id = request.args.get('page_id')
        workspace_id = request.args.get('workspace_id')
        
        if not query:
            return error_response('Search query is required', 400)
        
        # Build search query
        search_query = Comment.query.filter(Comment.plain_text.contains(query))
        
        if page_id:
            # Check page access
            has_access, user_permission, user_role = check_comment_access(current_user_id, page_id)
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
            
            search_query = search_query.filter(Comment.page_id.in_(accessible_pages))
        
        # Execute search
        comments = search_query.order_by(Comment.created_at.desc()).limit(50).all()
        
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict()
            # Add author information
            author = User.query.get(comment.author_id)
            comment_dict['author'] = author.to_dict() if author else None
            
            # Add page information
            if comment.page_id:
                page = Page.query.get(comment.page_id)
                comment_dict['page'] = {
                    'id': page.id,
                    'title': page.title,
                    'workspace_id': page.workspace_id
                } if page else None
            
            comments_data.append(comment_dict)
        
        return success_response({
            'comments': comments_data,
            'query': query,
            'total': len(comments_data)
        })
        
    except Exception as e:
        return error_response('Failed to search comments', 500)
