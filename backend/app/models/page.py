from datetime import datetime
import uuid
from app.extensions.database import db

class Page(db.Model):
    __tablename__ = 'pages'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(500), nullable=False, default='Untitled')
    icon = db.Column(db.Text, nullable=True)  # Emoji or URL
    cover_image = db.Column(db.Text, nullable=True)
    slug = db.Column(db.String(255), nullable=True, index=True)  # URL-friendly version of title
    
    # Hierarchy and organization
    workspace_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('workspaces.id'), nullable=False, index=True)
    parent_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('pages.id'), nullable=True, index=True)  # Self-referential for nested pages
    path = db.Column(db.Text, nullable=True, index=True)  # Materialized path for quick tree queries (e.g., "/parent/child/grandchild")
    level = db.Column(db.Integer, default=0, nullable=False, index=True)  # Depth level in hierarchy
    order_index = db.Column(db.Integer, default=0, nullable=False, index=True)  # Order among siblings
    
    # Content and metadata
    content_text = db.Column(db.Text, nullable=True)  # Plain text version for search
    template_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('page_templates.id'), nullable=True)
    properties = db.Column(db.JSON, default=dict)  # Custom properties (like Notion database properties)
    
    # Access and permissions
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    is_template = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Audit fields
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    last_edited_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    last_edited_at = db.Column(db.DateTime, nullable=True)
    
    # Version control
    version = db.Column(db.Integer, default=1, nullable=False)
    
    # Relationships - optimized with lazy loading
    workspace = db.relationship('Workspace', back_populates='pages', lazy='select')
    created_by_user = db.relationship('User', foreign_keys=[created_by], 
                                    back_populates='pages', lazy='select')
    last_edited_by_user = db.relationship('User', foreign_keys=[last_edited_by], lazy='select')
    
    # Hierarchical relationships
    parent = db.relationship('Page', remote_side=[id], back_populates='children', lazy='select')
    children = db.relationship('Page', back_populates='parent', cascade='all, delete-orphan', 
                              lazy='select', order_by='Page.order_index')
    
    # Content relationships - use lazy loading for better performance
    blocks = db.relationship('Block', back_populates='page', cascade='all, delete-orphan', 
                           order_by='Block.order_index', lazy='select')
    comments = db.relationship('Comment', back_populates='page', cascade='all, delete-orphan', 
                              lazy='dynamic')
    page_permissions = db.relationship('PagePermission', back_populates='page', 
                                     cascade='all, delete-orphan', lazy='select')
    
    # Add composite indexes for better query performance
    __table_args__ = (
        db.Index('idx_page_workspace_parent', 'workspace_id', 'parent_id'),
        db.Index('idx_page_workspace_order', 'workspace_id', 'order_index'),
        db.Index('idx_page_workspace_deleted', 'workspace_id', 'is_deleted'),
        db.Index('idx_page_workspace_archived', 'workspace_id', 'is_archived'),
        db.Index('idx_page_created_at', 'created_at'),
        db.Index('idx_page_updated_at', 'updated_at'),
    )
    
    def update_path(self):
        """Update materialized path based on parent hierarchy"""
        if self.parent:
            self.parent.update_path()
            self.path = f"{self.parent.path}/{self.slug or self.id}"
            self.level = self.parent.level + 1
        else:
            self.path = f"/{self.slug or self.id}"
            self.level = 0
    
    def get_ancestors(self):
        """Get all ancestor pages"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return reversed(ancestors)
    
    def get_descendants(self):
        """Get all descendant pages"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def to_dict(self, include_blocks=False):
        result = {
            'id': self.id,
            'title': self.title,
            'icon': self.icon,
            'cover_image': self.cover_image,
            'slug': self.slug,
            'workspace_id': self.workspace_id,
            'parent_id': self.parent_id,
            'path': self.path,
            'level': self.level,
            'order_index': self.order_index,
            'properties': self.properties,
            'is_public': self.is_public,
            'is_template': self.is_template,
            'is_deleted': self.is_deleted,
            'is_archived': self.is_archived,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_edited_by': self.last_edited_by,
            'last_edited_at': self.last_edited_at.isoformat() if self.last_edited_at else None,
            'version': self.version
        }
        
        if include_blocks:
            result['blocks'] = [block.to_dict() for block in self.blocks]
            
        return result

class PageTemplate(db.Model):
    __tablename__ = 'page_templates'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.Text, nullable=True)
    template_data = db.Column(db.JSON, nullable=False)  # Store the template structure
    category = db.Column(db.String(100), nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'template_data': self.template_data,
            'category': self.category,
            'is_public': self.is_public,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class PagePermission(db.Model):
    __tablename__ = 'page_permissions'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('pages.id'), nullable=False, index=True)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True, index=True)
    role = db.Column(db.String(50), nullable=True)  # For role-based permissions
    permission_type = db.Column(db.Enum('read', 'write', 'comment', 'full_access', name='page_permission_type'), 
                               nullable=False)
    granted_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    page = db.relationship('Page', back_populates='page_permissions')
    user = db.relationship('User', foreign_keys=[user_id])
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
    
    # Unique constraint to prevent duplicate permissions
    __table_args__ = (
        db.UniqueConstraint('page_id', 'user_id', 'permission_type', name='unique_page_user_permission'),
        db.CheckConstraint('user_id IS NOT NULL OR role IS NOT NULL', name='check_user_or_role')
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'page_id': self.page_id,
            'user_id': self.user_id,
            'role': self.role,
            'permission_type': self.permission_type,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat()
        }
