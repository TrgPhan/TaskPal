from datetime import datetime
import uuid
from app.extensions.database import db

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.Text, nullable=True)  # Emoji or URL
    cover_image = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    invite_code = db.Column(db.String(20), unique=True, nullable=True, index=True)
    domain = db.Column(db.String(100), unique=True, nullable=True, index=True)  # Custom domain for public workspaces
    settings = db.Column(db.JSON, default=dict)  # Store workspace preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], back_populates='owned_workspaces')
    members = db.relationship('User', secondary='workspace_members', 
                             primaryjoin='Workspace.id == WorkspaceMember.workspace_id',
                             secondaryjoin='User.id == WorkspaceMember.user_id',
                             back_populates='workspaces')
    pages = db.relationship('Page', back_populates='workspace', cascade='all, delete-orphan')
    
    def generate_invite_code(self):
        import secrets
        import string
        alphabet = string.ascii_uppercase + string.digits
        self.invite_code = ''.join(secrets.choice(alphabet) for _ in range(8))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'cover_image': self.cover_image,
            'owner_id': str(self.owner_id),
            'is_public': self.is_public,
            'domain': self.domain,
            'settings': self.settings,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class WorkspaceMember(db.Model):
    __tablename__ = 'workspace_members'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('workspaces.id'), nullable=False, index=True)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.Enum('owner', 'admin', 'member', 'guest', name='workspace_role'), 
                    default='member', nullable=False)
    permissions = db.Column(db.JSON, default=dict)  # Custom permissions
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    invited_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (db.UniqueConstraint('workspace_id', 'user_id', name='unique_workspace_member'),)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'user_id': str(self.user_id),
            'role': self.role,
            'permissions': self.permissions,
            'joined_at': self.joined_at.isoformat(),
            'invited_by': str(self.invited_by) if self.invited_by else None,
            'is_active': self.is_active
        }
