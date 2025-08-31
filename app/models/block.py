from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

class Block(db.Model):
    __tablename__ = 'blocks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content and type
    type = db.Column(db.Enum(
        'paragraph', 'heading_1', 'heading_2', 'heading_3', 
        'bulleted_list_item', 'numbered_list_item', 'to_do', 
        'toggle', 'quote', 'callout', 'code', 
        'image', 'video', 'audio', 'file',
        'bookmark', 'link_preview', 'embed',
        'divider', 'table_of_contents',
        'equation', 'breadcrumb',
        'table', 'column_list', 'column',
        'database', 'template',
        name='block_type'
    ), nullable=False, index=True)
    
    content = db.Column(db.JSON, default=dict, nullable=False)  # Rich content including text, formatting, properties
    plain_text = db.Column(db.Text, nullable=True, index=True)  # Plain text for search
    
    # Hierarchy and positioning
    page_id = db.Column(db.String(36), db.ForeignKey('pages.id'), nullable=False, index=True)
    parent_id = db.Column(db.String(36), db.ForeignKey('blocks.id'), nullable=True, index=True)  # For nested blocks
    order_index = db.Column(db.Integer, default=0, nullable=False, index=True)  # Order within parent
    depth = db.Column(db.Integer, default=0, nullable=False, index=True)  # Nesting depth
    
    # Properties and behavior
    properties = db.Column(db.JSON, default=dict)  # Block-specific properties (color, checked state, etc.)
    has_children = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_toggleable = db.Column(db.Boolean, default=False, nullable=False)  # Can be collapsed/expanded
    is_expanded = db.Column(db.Boolean, default=True, nullable=False)  # Current expanded state
    
    # Audit fields
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    last_edited_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    last_edited_at = db.Column(db.DateTime, nullable=True)
    
    # Version control
    version = db.Column(db.Integer, default=1, nullable=False)
    
    # Relationships
    page = db.relationship('Page', back_populates='blocks')
    created_by_user = db.relationship('User', foreign_keys=[created_by], back_populates='blocks')
    last_edited_by_user = db.relationship('User', foreign_keys=[last_edited_by])
    
    # Hierarchical relationships
    parent = db.relationship('Block', remote_side=[id], back_populates='children')
    children = db.relationship('Block', back_populates='parent', cascade='all, delete-orphan',
                             order_by='Block.order_index')
    
    # Comments on blocks
    comments = db.relationship('Comment', back_populates='block', cascade='all, delete-orphan')
    
    def update_has_children(self):
        """Update has_children flag based on actual children"""
        self.has_children = len(self.children) > 0
        db.session.add(self)
    
    def get_ancestors(self):
        """Get all ancestor blocks"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return reversed(ancestors)
    
    def get_descendants(self):
        """Get all descendant blocks"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def extract_plain_text(self):
        """Extract plain text from rich content for search indexing"""
        if not self.content:
            return ""
        
        # Handle different content structures based on block type
        if self.type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'quote', 'callout']:
            if 'rich_text' in self.content:
                return self._extract_from_rich_text(self.content['rich_text'])
        elif self.type == 'to_do':
            if 'rich_text' in self.content:
                text = self._extract_from_rich_text(self.content['rich_text'])
                checked = self.content.get('checked', False)
                return f"[{'x' if checked else ' '}] {text}"
        elif self.type == 'code':
            return self.content.get('rich_text', [{}])[0].get('plain_text', '')
        elif self.type in ['bulleted_list_item', 'numbered_list_item']:
            if 'rich_text' in self.content:
                return self._extract_from_rich_text(self.content['rich_text'])
        
        return ""
    
    def _extract_from_rich_text(self, rich_text_array):
        """Extract plain text from Notion's rich_text format"""
        if not rich_text_array:
            return ""
        return " ".join([item.get('plain_text', '') for item in rich_text_array])
    
    def to_dict(self, include_children=False):
        result = {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'plain_text': self.plain_text,
            'page_id': self.page_id,
            'parent_id': self.parent_id,
            'order_index': self.order_index,
            'depth': self.depth,
            'properties': self.properties,
            'has_children': self.has_children,
            'is_toggleable': self.is_toggleable,
            'is_expanded': self.is_expanded,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_edited_by': self.last_edited_by,
            'last_edited_at': self.last_edited_at.isoformat() if self.last_edited_at else None,
            'version': self.version
        }
        
        if include_children:
            result['children'] = [child.to_dict(include_children=True) for child in self.children]
            
        return result

class BlockHistory(db.Model):
    """Track block changes for version history"""
    __tablename__ = 'block_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    block_id = db.Column(db.String(36), db.ForeignKey('blocks.id'), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    content_snapshot = db.Column(db.JSON, nullable=False)  # Complete block content at this version
    change_type = db.Column(db.Enum('created', 'updated', 'deleted', 'moved', name='block_change_type'), 
                           nullable=False)
    changed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    block = db.relationship('Block')
    changed_by_user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'block_id': self.block_id,
            'version': self.version,
            'content_snapshot': self.content_snapshot,
            'change_type': self.change_type,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat()
        }
