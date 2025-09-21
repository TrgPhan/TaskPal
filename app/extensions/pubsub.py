"""
Pub/Sub Extension
Handles Redis pub/sub service initialization for the application
"""

def init_pubsub(app):
    """Initialize pub/sub service with app context"""
    try:
        # Test Redis connection is available
        redis_url = app.config.get('REDIS_URL')
        if not redis_url:
            app.logger.warning("REDIS_URL not configured - PubSub features will be disabled")
            return

        # Import here to avoid circular imports and ensure Flask context
        import redis

        # Test Redis connection
        if redis_url.startswith('redis://'):
            redis_url = redis_url.replace('redis://', '')
        test_client = redis.Redis.from_url(f'redis://{redis_url}')

        # Try to ping Redis
        test_client.ping()
        test_client.close()

        app.logger.info("PubSub extension initialized successfully - Redis is available")
    except redis.ConnectionError as e:
        app.logger.warning(f"PubSub extension - Redis connection failed: {e}")
        app.logger.warning("PubSub features will be disabled")
    except Exception as e:
        app.logger.error(f"PubSub extension initialization error: {e}")
        app.logger.warning("PubSub features will be disabled")
