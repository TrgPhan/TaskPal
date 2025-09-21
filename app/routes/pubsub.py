"""
Redis Pub/Sub Routes
Provides API endpoints for real-time messaging and notifications
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import get_pubsub_service
from app.utils.responses import success_response, error_response
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.extensions.database import db
import json
import uuid

pubsub_bp = Blueprint('pubsub', __name__)

# Global subscription storage for demo purposes
# In production, you'd want to store this in a database or Redis
user_subscriptions = {}

@pubsub_bp.route('/publish/<channel>', methods=['POST'])
@jwt_required()
def publish_message(channel):
    """Publish a message to a channel"""
    try:
        current_user_id = get_jwt_identity()
        pubsub_service = get_pubsub_service()
        data = request.get_json()

        if not data:
            return error_response('Message data is required', 400)

        # Add sender information to the message
        message_data = {
            **data,
            'sender_id': str(current_user_id),
            'timestamp': data.get('timestamp', None)  # Client can provide timestamp or we can add server timestamp
        }

        # Publish to Redis channel
        success = pubsub_service.publish(channel, message_data)

        if success:
            return success_response({
                'message': 'Message published successfully',
                'channel': channel,
                'data': message_data
            })
        else:
            return error_response('Failed to publish message', 500)

    except Exception as e:
        current_app.logger.error(f"Error publishing message: {e}")
        return error_response('Failed to publish message', 500)

@pubsub_bp.route('/workspace/<workspace_id>/publish', methods=['POST'])
@jwt_required()
def publish_workspace_message(workspace_id):
    """Publish a message to workspace channel (members only)"""
    try:
        current_user_id = get_jwt_identity()
        pubsub_service = get_pubsub_service()
        data = request.get_json()

        if not data:
            return error_response('Message data is required', 400)

        # Verify user has access to workspace
        membership = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=current_user_id,
            is_active=True
        ).first()

        if not membership:
            return error_response('Workspace not found or access denied', 403)

        channel = f'workspace:{workspace_id}'

        # Add sender information to the message
        message_data = {
            **data,
            'sender_id': str(current_user_id),
            'workspace_id': workspace_id,
            'timestamp': data.get('timestamp', None)
        }

        # Publish to workspace channel
        success = pubsub_service.publish(channel, message_data)

        if success:
            return success_response({
                'message': 'Message published to workspace successfully',
                'channel': channel,
                'data': message_data
            })
        else:
            return error_response('Failed to publish message', 500)

    except Exception as e:
        current_app.logger.error(f"Error publishing workspace message: {e}")
        return error_response('Failed to publish message', 500)

@pubsub_bp.route('/user/<user_id>/notify', methods=['POST'])
@jwt_required()
def send_user_notification(user_id):
    """Send notification to specific user"""
    try:
        current_user_id = get_jwt_identity()
        pubsub_service = get_pubsub_service()
        data = request.get_json()

        if not data:
            return error_response('Notification data is required', 400)

        # Verify target user exists
        target_user = User.query.get(user_id)
        if not target_user:
            return error_response('Target user not found', 404)

        channel = f'user:{user_id}:notifications'

        # Add sender and notification metadata
        notification_data = {
            'type': 'notification',
            'title': data.get('title', 'Notification'),
            'message': data.get('message', ''),
            'sender_id': str(current_user_id),
            'user_id': user_id,
            'data': data.get('data', {}),
            'timestamp': data.get('timestamp', None)
        }

        # Publish notification
        success = pubsub_service.publish(channel, notification_data)

        if success:
            return success_response({
                'message': 'Notification sent successfully',
                'notification': notification_data
            })
        else:
            return error_response('Failed to send notification', 500)

    except Exception as e:
        current_app.logger.error(f"Error sending notification: {e}")
        return error_response('Failed to send notification', 500)

@pubsub_bp.route('/subscribe/<channel>', methods=['POST'])
@jwt_required()
def subscribe_to_channel(channel):
    """Subscribe to a channel (for demo purposes - returns subscription info)"""
    try:
        current_user_id = get_jwt_identity()
        pubsub_service = get_pubsub_service()

        # Store user subscription for demo purposes
        if channel not in user_subscriptions:
            user_subscriptions[channel] = []

        if current_user_id not in user_subscriptions[channel]:
            user_subscriptions[channel].append(current_user_id)

        # Define a callback for this channel
        def channel_callback(channel_name, message):
            """Handle incoming messages for this channel"""
            current_app.logger.info(f"Channel {channel_name} received: {message}")

            # In a real application, you might store messages in a database
            # or forward them via WebSocket/Server-Sent Events

        # Subscribe to the channel
        pubsub_service.subscribe(channel, channel_callback)

        return success_response({
            'message': f'Subscribed to channel {channel} successfully',
            'channel': channel,
            'subscription_id': str(uuid.uuid4())
        })

    except Exception as e:
        current_app.logger.error(f"Error subscribing to channel {channel}: {e}")
        return error_response('Failed to subscribe to channel', 500)

@pubsub_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
def get_subscriptions():
    """Get current user's subscriptions"""
    try:
        current_user_id = get_jwt_identity()

        # Find all channels the user is subscribed to
        user_channels = []
        for channel, subscribers in user_subscriptions.items():
            if current_user_id in subscribers:
                user_channels.append(channel)

        return success_response({
            'subscriptions': user_channels
        })

    except Exception as e:
        current_app.logger.error(f"Error getting subscriptions: {e}")
        return error_response('Failed to get subscriptions', 500)

@pubsub_bp.route('/channels', methods=['GET'])
@jwt_required()
def get_available_channels():
    """Get available channels user can subscribe to"""
    try:
        current_user_id = get_jwt_identity()

        # Get user's workspaces
        workspaces = db.session.query(Workspace).join(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user_id,
            WorkspaceMember.is_active == True
        ).all()

        channels = []

        # User-specific channels
        channels.append(f'user:{current_user_id}:notifications')

        # Workspace channels
        for workspace in workspaces:
            channels.append(f'workspace:{workspace.id}')
            channels.append(f'workspace:{workspace.id}:members')

        return success_response({
            'channels': channels,
            'user_id': str(current_user_id)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting available channels: {e}")
        return error_response('Failed to get channels', 500)
