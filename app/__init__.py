from flask import Flask
import os

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize all extensions
    from app.extensions import init_app as init_extensions
    init_extensions(app)
    
    # Create tables
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from app.models import user, workspace, page, block, comment, database as db_models
        db.create_all()
    
    # Register blueprints
    from app.routes import user, auth
    app.register_blueprint(user)
    app.register_blueprint(auth)
    
    return app