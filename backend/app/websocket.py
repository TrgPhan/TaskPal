"""
WebSocket Events for TaskPal
Handles real-time communication between clients
"""
import json
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token, get_jwt_identity
from flask import request, current_app
from app import socketio
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.services.pubsub_service import get_pubsub_service
import threading

# Store active WebSocket connections
active_connections = {}

def authenticate_socket(token):
    """Authenticate WebSocket connection using JWT token"""
    try:
        if not token:
            return None
        
        # Decode JWT token
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return None
            
        return user_id
    except Exception as e:
        current_app.logger.error(f"WebSocket authentication error: {e}")
        return None

@socketio.on('connect', namespace='/ws/pubsub')
def handle_connect(auth):
    """Handle WebSocket connection"""
    try:
        # Get token from query parameters or auth data
        token = request.args.get('token') or (auth.get('token') if auth else None)
        
        user_id = authenticate_socket(token)
        if not user_id:
            current_app.logger.warning("Unauthorized WebSocket connection attempt")
            disconnect()
            return False
        
        # Store connection
        active_connections[request.sid] = {
            'user_id': user_id,
            'channels': set()
        }
        
        current_app.logger.info(f"User {user_id} connected via WebSocket (sid: {request.sid})")
        
        emit('connected', {
            'message': 'Successfully connected to TaskPal real-time service',
            'user_id': str(user_id)
        })
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"WebSocket connection error: {e}")
        disconnect()
        return False

@socketio.on('disconnect', namespace='/ws/pubsub')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    try:
        if request.sid in active_connections:
            user_id = active_connections[request.sid]['user_id']
            
            # Leave all rooms
            channels = active_connections[request.sid]['channels'].copy()
            for channel in channels:
                leave_room(channel)
            
            # Remove connection
            del active_connections[request.sid]
            
            current_app.logger.info(f"User {user_id} disconnected from WebSocket (sid: {request.sid})")
        
    except Exception as e:
        current_app.logger.error(f"WebSocket disconnection error: {e}")

@socketio.on('subscribe', namespace='/ws/pubsub')
def handle_subscribe(data):
    """Subscribe to a channel"""
    try:
        if request.sid not in active_connections:
            emit('error', {'message': 'Not authenticated'})
            return
        
        channel = data.get('channel')
        if not channel:
            emit('error', {'message': 'Channel is required'})
            return
        
        user_id = active_connections[request.sid]['user_id']
        
        # Verify user has access to the channel
        if not verify_channel_access(user_id, channel):
            emit('error', {'message': 'Access denied to channel'})
            return
        
        # Join the room
        join_room(channel)
        active_connections[request.sid]['channels'].add(channel)
        
        current_app.logger.info(f"User {user_id} subscribed to channel: {channel}")
        
        emit('subscribed', {
            'channel': channel,
            'message': f'Successfully subscribed to {channel}'
        })
        
    except Exception as e:
        current_app.logger.error(f"WebSocket subscribe error: {e}")
        emit('error', {'message': 'Failed to subscribe to channel'})

@socketio.on('unsubscribe', namespace='/ws/pubsub')
def handle_unsubscribe(data):
    """Unsubscribe from a channel"""
    try:
        if request.sid not in active_connections:
            emit('error', {'message': 'Not authenticated'})
            return
        
        channel = data.get('channel')
        if not channel:
            emit('error', {'message': 'Channel is required'})
            return
        
        user_id = active_connections[request.sid]['user_id']
        
        # Leave the room
        leave_room(channel)
        active_connections[request.sid]['channels'].discard(channel)
        
        current_app.logger.info(f"User {user_id} unsubscribed from channel: {channel}")
        
        emit('unsubscribed', {
            'channel': channel,
            'message': f'Successfully unsubscribed from {channel}'
        })
        
    except Exception as e:
        current_app.logger.error(f"WebSocket unsubscribe error: {e}")
        emit('error', {'message': 'Failed to unsubscribe from channel'})

def verify_channel_access(user_id, channel):
    """Verify user has access to a specific channel"""
    try:
        # User notification channels
        if channel.startswith(f'user:{user_id}:'):
            return True
        
        # Workspace channels
        if channel.startswith('workspace:'):
            workspace_id = channel.split(':')[1]
            membership = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                user_id=user_id,
                is_active=True
            ).first()
            return membership is not None
        
        # Global or other channels (add more logic as needed)
        return False
        
    except Exception as e:
        current_app.logger.error(f"Channel access verification error: {e}")
        return False

def broadcast_to_channel(channel, message):
    """Broadcast message to all clients in a channel"""
    try:
        socketio.emit('message', {
            'channel': channel,
            'data': message,
            'timestamp': message.get('timestamp')
        }, room=channel, namespace='/ws/pubsub')
        
        current_app.logger.debug(f"Broadcasted message to channel {channel}")
        
    except Exception as e:
        current_app.logger.error(f"Broadcast error: {e}")

# Redis message handler for bridging Redis pub/sub to WebSocket
def setup_redis_to_websocket_bridge():
    """Setup Redis pub/sub listener that forwards messages to WebSocket clients"""
    try:
        pubsub_service = get_pubsub_service()
        
        def redis_message_handler(channel, message):
            """Handle Redis messages and broadcast to WebSocket clients"""
            try:
                # Parse message if it's a string
                if isinstance(message, str):
                    try:
                        message = json.loads(message)
                    except json.JSONDecodeError:
                        message = {'content': message}
                
                # Broadcast to WebSocket clients
                broadcast_to_channel(channel, message)
                
            except Exception as e:
                current_app.logger.error(f"Redis message handler error: {e}")
        
        # Subscribe to all workspace and user channels
        # This is a simplified approach - in production, you might want to
        # dynamically subscribe based on active connections
        
        # Subscribe to pattern for workspace channels
        pubsub_service.subscribe_pattern('workspace:*', redis_message_handler)
        pubsub_service.subscribe_pattern('user:*', redis_message_handler)
        pubsub_service.subscribe_pattern('page:*', redis_message_handler)
        pubsub_service.subscribe_pattern('block:*', redis_message_handler)
        
        current_app.logger.info("Redis to WebSocket bridge started")
        
    except Exception as e:
        current_app.logger.error(f"Failed to setup Redis to WebSocket bridge: {e}")

# Initialize the bridge when the app starts
@socketio.on_error_default
def default_error_handler(e):
    current_app.logger.error(f"SocketIO error: {e}")

# Initialize the bridge
def init_websocket_bridge():
    """Initialize the WebSocket bridge - call this after app creation"""
    setup_redis_to_websocket_bridge()

# Flag to indicate this module is loaded
websocket_events = True