from app import create_app
import os

# Create app with environment configuration
config_name = os.getenv('FLASK_ENV', 'development')
app, socketio = create_app(config_name)

if __name__ == '__main__':
    socketio.run(
        app,
        host=os.getenv('FLASK_HOST', '0.0.0.0'), 
        port=int(os.getenv('FLASK_PORT', '8000')), 
        debug=app.config.get('DEBUG', False)
    )

