from flask import Blueprint

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    return "Login successful"

@auth.route('/register', methods=['POST'])
def register():
    return "Registration successful"

@auth.route('/logout', methods=['POST'])
def logout():
    return "Logout successful"
