from flask import Blueprint

app = Blueprint('user', __name__)

@app.route('/get_profile', methods=['GET'])
def profile():
    return ""

@app.route('/get_settings', methods=['GET'])
def settings():
    return ""

@app.route('/update_profile', methods=['POST'])
def update_profile():
    return ""



