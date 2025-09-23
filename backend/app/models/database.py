from datetime import datetime
import uuid
from app.extensions.database import db

class Database(db.Model):
    __tablename__ = 'databases'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.Text, nullable=True)  # Emoji or URL
    cover_image = db.Column(db.Text, nullable=True)
    
    # Location
    workspace_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('workspaces.id'), nullable=False, index=True)
    page_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('pages.id'), nullable=True, index=True)  # If database is on a page
    
    # Configuration
    is_inline = db.Column(db.Boolean, default=False, nullable=False)  # Inline vs full-page database
    view_config = db.Column(db.JSON, default=dict)  # Default view settings
    
    # Audit fields
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    workspace = db.relationship('Workspace')
    page = db.relationship('Page')
    created_by_user = db.relationship('User')
    properties = db.relationship('DatabaseProperty', back_populates='database', cascade='all, delete-orphan',
                                order_by='DatabaseProperty.order_index')
    rows = db.relationship('DatabaseRow', back_populates='database', cascade='all, delete-orphan')
    views = db.relationship('DatabaseView', back_populates='database', cascade='all, delete-orphan')
    
    def to_dict(self, include_properties=True):
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'cover_image': self.cover_image,
            'workspace_id': self.workspace_id,
            'page_id': self.page_id,
            'is_inline': self.is_inline,
            'view_config': self.view_config,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_properties:
            result['properties'] = [prop.to_dict() for prop in self.properties]
            
        return result

class DatabaseProperty(db.Model):
    __tablename__ = 'database_properties'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('databases.id'), nullable=False, index=True)
    
    # Property definition
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(
        'title', 'rich_text', 'number', 'select', 'multi_select',
        'date', 'person', 'file', 'checkbox', 'url', 'email', 'phone_number',
        'formula', 'relation', 'rollup', 'created_time', 'created_by',
        'last_edited_time', 'last_edited_by', 'status',
        name='property_type'
    ), nullable=False, index=True)
    
    # Configuration based on type
    config = db.Column(db.JSON, default=dict)  # Type-specific configuration (options, format, etc.)
    
    # Display and ordering
    order_index = db.Column(db.Integer, default=0, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    width = db.Column(db.Integer, nullable=True)  # Column width in pixels
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    database = db.relationship('Database', back_populates='properties')
    values = db.relationship('DatabasePropertyValue', back_populates='property', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'database_id': self.database_id,
            'name': self.name,
            'type': self.type,
            'config': self.config,
            'order_index': self.order_index,
            'is_visible': self.is_visible,
            'width': self.width,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class DatabaseRow(db.Model):
    __tablename__ = 'database_rows'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('databases.id'), nullable=False, index=True)
    page_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('pages.id'), nullable=False, index=True)  # Each row is a page
    
    # Row metadata
    order_index = db.Column(db.Integer, default=0, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    database = db.relationship('Database', back_populates='rows')
    page = db.relationship('Page')
    created_by_user = db.relationship('User')
    property_values = db.relationship('DatabasePropertyValue', back_populates='row', cascade='all, delete-orphan')
    
    def to_dict(self, include_values=True):
        result = {
            'id': self.id,
            'database_id': self.database_id,
            'page_id': self.page_id,
            'order_index': self.order_index,
            'is_archived': self.is_archived,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_values:
            result['property_values'] = {val.property.name: val.to_dict() for val in self.property_values}
            
        return result

class DatabasePropertyValue(db.Model):
    __tablename__ = 'database_property_values'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    row_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('database_rows.id'), nullable=False, index=True)
    property_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('database_properties.id'), nullable=False, index=True)
    
    # Value storage - different columns for different types
    text_value = db.Column(db.Text, nullable=True, index=True)
    number_value = db.Column(db.Numeric(precision=20, scale=6), nullable=True, index=True)
    boolean_value = db.Column(db.Boolean, nullable=True, index=True)
    date_value = db.Column(db.DateTime, nullable=True, index=True)
    json_value = db.Column(db.JSON, nullable=True)  # For complex types (select options, files, etc.)
    
    # Audit
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    row = db.relationship('DatabaseRow', back_populates='property_values')
    property = db.relationship('DatabaseProperty', back_populates='values')
    
    # Unique constraint - one value per property per row
    __table_args__ = (
        db.UniqueConstraint('row_id', 'property_id', name='unique_row_property_value'),
    )
    
    def get_value(self):
        """Get the actual value based on property type"""
        prop_type = self.property.type
        
        if prop_type in ['title', 'rich_text', 'url', 'email', 'phone_number']:
            return self.text_value
        elif prop_type == 'number':
            return float(self.number_value) if self.number_value else None
        elif prop_type == 'checkbox':
            return self.boolean_value
        elif prop_type == 'date':
            return self.date_value.isoformat() if self.date_value else None
        elif prop_type in ['select', 'multi_select', 'person', 'file', 'relation', 'rollup', 'formula', 'status']:
            return self.json_value
        else:
            return self.text_value
    
    def to_dict(self):
        return {
            'id': self.id,
            'row_id': self.row_id,
            'property_id': self.property_id,
            'value': self.get_value(),
            'updated_at': self.updated_at.isoformat()
        }

class DatabaseView(db.Model):
    __tablename__ = 'database_views'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('databases.id'), nullable=False, index=True)
    
    # View definition
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum('table', 'board', 'timeline', 'calendar', 'gallery', 'list', name='view_type'), 
                    nullable=False)
    
    # Configuration
    filter_config = db.Column(db.JSON, default=dict)  # Filter rules
    sort_config = db.Column(db.JSON, default=dict)    # Sort rules  
    group_config = db.Column(db.JSON, default=dict)   # Grouping rules
    format_config = db.Column(db.JSON, default=dict)  # View-specific formatting
    
    # Properties visibility and order
    visible_properties = db.Column(db.JSON, default=list)  # List of property IDs to show
    property_order = db.Column(db.JSON, default=list)      # Custom property order
    
    # Access
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    database = db.relationship('Database', back_populates='views')
    created_by_user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'database_id': self.database_id,
            'name': self.name,
            'type': self.type,
            'filter_config': self.filter_config,
            'sort_config': self.sort_config,
            'group_config': self.group_config,
            'format_config': self.format_config,
            'visible_properties': self.visible_properties,
            'property_order': self.property_order,
            'is_default': self.is_default,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
