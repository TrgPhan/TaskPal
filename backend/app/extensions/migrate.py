"""
Database Migration extension
Handles Flask-Migrate for database schema changes
"""
from flask_migrate import Migrate

# Initialize Flask-Migrate without app context
migrate = Migrate()

def init_migrate(app, db):
    """Initialize Flask-Migrate with app and database"""
    migrate.init_app(app, db)
