# Extensions initialization
# Import all extensions here for easy access
from .database import db
from .migrate import migrate
from .cors import cors
from .jwt import jwt_manager
from .cache import cache
from .mail import mail

# Import initialization functions
from .database import init_db
from .migrate import init_migrate
from .cors import init_cors
from .jwt import init_jwt
from .cache import init_cache
from .mail import init_mail

# List of extensions with their init functions
EXTENSIONS = [
    (db, lambda app: db.init_app(app)),
    (migrate, lambda app: init_migrate(app, db)),
    (cors, init_cors),
    (jwt_manager, init_jwt),
    (cache, init_cache),
    (mail, init_mail),
]

def init_app(app):
    """Initialize all extensions with the Flask app"""
    for extension, init_func in EXTENSIONS:
        try:
            init_func(app)
            print(f"✅ Initialized {extension.__class__.__name__}")
        except Exception as e:
            print(f"❌ Failed to initialize {extension.__class__.__name__}: {e}")

# Export all extensions for easy import
__all__ = ['db', 'migrate', 'cors', 'jwt_manager', 'cache', 'mail', 'init_app']
