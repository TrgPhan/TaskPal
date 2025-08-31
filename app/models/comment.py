from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content
    content = db.Column(db.JSON, nullable=False)  # Rich text content
    plain_text = db.Column(db.Text, nullable=True, index=True)  # Plain text for search
    
    # Target - can be on page or specific block
    page_id = db.Column(db.String(36), db.ForeignKey('pages.id'), nullable=True, index=True)
    block_id = db.Column(db.String(36), db.ForeignKey('blocks.id'), nullable=True, index=True)
    
    # Threading
    parent_id = db.Column(db.String(36), db.ForeignKey('comments.id'), nullable=True, index=True)
    thread_id = db.Column(db.String(36), nullable=False, index=True)  # Top-level comment ID for grouping
    
    # Status
    is_resolved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    resolved_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Audit fields
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_edited_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    author = db.relationship('User', foreign_keys=[author_id], back_populates='comments')
    resolved_by_user = db.relationship('User', foreign_keys=[resolved_by])
    page = db.relationship('Page', back_populates='comments')
    block = db.relationship('Block', back_populates='comments')
    
    # Threading relationships
    parent = db.relationship('Comment', remote_side=[id], back_populates='replies')
    replies = db.relationship('Comment', back_populates='parent', cascade='all, delete-orphan')
    
    # Reactions and mentions
    reactions = db.relationship('CommentReaction', back_populates='comment', cascade='all, delete-orphan')
    mentions = db.relationship('CommentMention', back_populates='comment', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('page_id IS NOT NULL OR block_id IS NOT NULL', name='check_comment_target'),
    )
    
    def extract_plain_text(self):
        """Extract plain text from rich content"""
        if not self.content:
            return ""
        
        if 'rich_text' in self.content:
            return " ".join([item.get('plain_text', '') for item in self.content['rich_text']])
        
        return ""
    
    def to_dict(self, include_replies=False):
        result = {
            'id': self.id,
            'content': self.content,
            'plain_text': self.plain_text,
            'page_id': self.page_id,
            'block_id': self.block_id,
            'parent_id': self.parent_id,
            'thread_id': self.thread_id,
            'is_resolved': self.is_resolved,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_edited_at': self.last_edited_at.isoformat() if self.last_edited_at else None
        }
        
        if include_replies:
            result['replies'] = [reply.to_dict(include_replies=True) for reply in self.replies]
            
        return result

class CommentReaction(db.Model):
    __tablename__ = 'comment_reactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    comment_id = db.Column(db.String(36), db.ForeignKey('comments.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    emoji = db.Column(db.String(10), nullable=False)  # Unicode emoji
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    comment = db.relationship('Comment', back_populates='reactions')
    user = db.relationship('User')
    
    # Unique constraint - one reaction per user per comment
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id', 'emoji', name='unique_comment_reaction'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'user_id': self.user_id,
            'emoji': self.emoji,
            'created_at': self.created_at.isoformat()
        }

class CommentMention(db.Model):
    __tablename__ = 'comment_mentions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    comment_id = db.Column(db.String(36), db.ForeignKey('comments.id'), nullable=False, index=True)
    mentioned_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    mention_text = db.Column(db.String(255), nullable=False)  # The text that was mentioned (e.g., "@username")
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    comment = db.relationship('Comment', back_populates='mentions')
    mentioned_user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'mentioned_user_id': self.mentioned_user_id,
            'mention_text': self.mention_text,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
