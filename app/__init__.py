from flask import Flask
from app.routes import user, auth
def create_app():
    app = Flask(__name__)
    app.register_blueprint(user)
    app.register_blueprint(auth)
    return app