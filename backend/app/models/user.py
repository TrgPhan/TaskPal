from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from app.extensions.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active = db.Column(db.DateTime, nullable=True)
    
    # Relationships - optimized with lazy loading
    workspaces = db.relationship('Workspace', secondary='workspace_members', 
                                primaryjoin='User.id == WorkspaceMember.user_id',
                                secondaryjoin='Workspace.id == WorkspaceMember.workspace_id',
                                back_populates='members', lazy='select')
    owned_workspaces = db.relationship('Workspace', foreign_keys='Workspace.owner_id', 
                                     back_populates='owner', lazy='select')
    pages = db.relationship('Page', foreign_keys='Page.created_by', 
                           back_populates='created_by_user', lazy='dynamic')
    blocks = db.relationship('Block', foreign_keys='Block.created_by', 
                            back_populates='created_by_user', lazy='dynamic')
    comments = db.relationship('Comment', foreign_keys='Comment.author_id', 
                              back_populates='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'timezone': self.timezone,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }
