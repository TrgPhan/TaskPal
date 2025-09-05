from flask import Flask, jsonify
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
        from app.extensions.database import db
        db.create_all()
    
    # Register blueprints
    from app.routes.user import user_bp
    from app.routes.auth import auth as auth_bp
    from app.routes.workspace import workspace_bp
    from app.routes.page import page_bp
    from app.routes.block import block_bp
    from app.routes.comment import comment_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(workspace_bp, url_prefix='/api/workspace')
    app.register_blueprint(page_bp, url_prefix='/api/page')
    app.register_blueprint(block_bp, url_prefix='/api/block')
    app.register_blueprint(comment_bp, url_prefix='/api/comment')
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found',
            'error': 'Not Found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error': 'Method Not Allowed'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': 'Internal Server Error'
        }), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'success': True,
            'message': 'TaskPal API is running',
            'status': 'healthy'
        })
    
    return app