"""
Redis Pub/Sub Service
Handles Redis publish/subscribe functionality for real-time messaging
"""
import json
import redis
import threading
from typing import Callable, Dict, List, Any
from flask import current_app

class PubSubService:
    """Service for managing Redis pub/sub operations"""

    def __init__(self):
        self.redis_client = None
        self.pubsub_client = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.thread = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis clients"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')

            # Remove redis:// prefix for redis-py
            if redis_url.startswith('redis://'):
                redis_url = redis_url.replace('redis://', '')

            self.redis_client = redis.Redis.from_url(f'redis://{redis_url}', decode_responses=True)
            self.pubsub_client = self.redis_client.pubsub()

            # Test connection
            self.redis_client.ping()
            current_app.logger.info("PubSub service connected to Redis successfully")

        except Exception as e:
            current_app.logger.error(f"Failed to connect to Redis for PubSub: {e}")
            raise

    def publish(self, channel: str, message: Any) -> bool:
        """Publish a message to a channel"""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            elif not isinstance(message, str):
                message = str(message)

            result = self.redis_client.publish(channel, message)
            current_app.logger.info(f"Published message to channel '{channel}': {message}")
            return result > 0  # Returns number of subscribers

        except Exception as e:
            current_app.logger.error(f"Failed to publish message to channel '{channel}': {e}")
            return False

    def subscribe(self, channel: str, callback: Callable[[str, Any], None]):
        """Subscribe to a channel with a callback function"""
        try:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
                self.pubsub_client.subscribe(channel)

            self.subscribers[channel].append(callback)
            current_app.logger.info(f"Subscribed to channel '{channel}'")

            # Start the listener thread if not already running
            if not self.running:
                self._start_listener()

        except Exception as e:
            current_app.logger.error(f"Failed to subscribe to channel '{channel}': {e}")

    def unsubscribe(self, channel: str, callback: Callable = None):
        """Unsubscribe from a channel"""
        try:
            if channel in self.subscribers:
                if callback:
                    if callback in self.subscribers[channel]:
                        self.subscribers[channel].remove(callback)
                    if not self.subscribers[channel]:
                        del self.subscribers[channel]
                        self.pubsub_client.unsubscribe(channel)
                else:
                    del self.subscribers[channel]
                    self.pubsub_client.unsubscribe(channel)

                current_app.logger.info(f"Unsubscribed from channel '{channel}'")
        except Exception as e:
            current_app.logger.error(f"Failed to unsubscribe from channel '{channel}': {e}")

    def _start_listener(self):
        """Start the pub/sub listener thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        current_app.logger.info("PubSub listener thread started")

    def _listen_loop(self):
        """Main listener loop"""
        try:
            for message in self.pubsub_client.listen():
                if not self.running:
                    break

                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']

                    # Parse JSON message if possible
                    try:
                        parsed_data = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        parsed_data = data

                    # Call all callbacks for this channel
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                callback(channel, parsed_data)
                            except Exception as e:
                                current_app.logger.error(f"Error in PubSub callback for channel '{channel}': {e}")
        except Exception as e:
            current_app.logger.error(f"PubSub listener error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Stop the pub/sub service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

        try:
            if self.pubsub_client:
                self.pubsub_client.close()
            if self.redis_client:
                self.redis_client.close()
        except Exception as e:
            current_app.logger.error(f"Error closing PubSub connections: {e}")

    # Channel-specific methods for common use cases

    def publish_workspace_update(self, workspace_id: int, update_data: dict):
        """Publish workspace update"""
        channel = f'workspace:{workspace_id}'
        return self.publish(channel, {
            'type': 'update',
            'workspace_id': workspace_id,
            **update_data
        })

    def publish_user_notification(self, user_id: int, notification: dict):
        """Publish user notification"""
        channel = f'user:{user_id}:notifications'
        return self.publish(channel, notification)

    def publish_page_update(self, page_id: int, update_data: dict):
        """Publish page update"""
        channel = f'page:{page_id}'
        return self.publish(channel, {
            'type': 'update',
            'page_id': page_id,
            **update_data
        })

    def publish_block_update(self, block_id: int, update_data: dict):
        """Publish block update"""
        channel = f'block:{block_id}'
        return self.publish(channel, {
            'type': 'update',
            'block_id': block_id,
            **update_data
        })

    def publish_comment_update(self, page_id: int, comment_data: dict):
        """Publish comment update"""
        channel = f'page:{page_id}:comments'
        return self.publish(channel, comment_data)

# Global instance - lazy initialization
_pubsub_service = None

def get_pubsub_service():
    """Get the global pub/sub service instance"""
    global _pubsub_service
    if _pubsub_service is None:
        _pubsub_service = PubSubService()
    return _pubsub_service
