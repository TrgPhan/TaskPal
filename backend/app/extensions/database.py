"""
Database extension
Handles SQLAlchemy database connection and models
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without app context
# This will be attached to the app in create_app()
db = SQLAlchemy()

def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    # Import all models after db is initialized to avoid circular imports
    with app.app_context():
        from app.models import user, workspace, page, block, comment, database as db_models
        
        # Create all tables if they don't exist
        db.create_all()
        
def reset_db(app):
    """Reset database - useful for testing"""
    with app.app_context():
        db.drop_all()
        db.create_all() 
