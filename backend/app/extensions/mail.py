"""
Mail Extension
Handles email sending functionality
"""
from flask_mail import Mail

# Initialize Mail without app context
mail = Mail()

def init_mail(app):
    """Initialize Mail with app"""
    mail_config = {
        'MAIL_SERVER': app.config.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(app.config.get('MAIL_PORT', '587')),
        'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS', True),
        'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': app.config.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER')
    }
    
    app.config.update(mail_config)
    mail.init_app(app)

def send_async_email(app, msg):
    """Send email asynchronously"""
    import threading
    from flask_mail import Message
    
    def send_async_mail(app, msg):
        with app.app_context():
            mail.send(msg)
    
    thread = threading.Thread(target=send_async_mail, args=[app, msg])
    thread.start()
    return thread
