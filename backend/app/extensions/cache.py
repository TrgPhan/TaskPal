"""
Cache Extension
Handles application caching for improved performance using Redis
"""
from flask_caching import Cache
from flask import current_app
import redis

# Initialize Cache without app context
cache = Cache()

def init_cache(app):
    """Initialize Cache with app - prioritize Redis"""
    redis_url = app.config.get('REDIS_URL')
    
    if redis_url:
        # Use Redis configuration
        cache_config = {
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': redis_url,
            'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
            'CACHE_KEY_PREFIX': 'taskpal:',
            'CACHE_REDIS_DB': 0,
            'CACHE_OPTIONS': {
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True
            }
        }
        
        try:
            # Test Redis connection
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            app.logger.info("✅ Redis cache initialized successfully")
        except Exception as e:
            app.logger.warning(f"⚠️ Redis connection failed: {e}. Falling back to simple cache.")
            cache_config = {
                'CACHE_TYPE': 'simple',
                'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
            }
    else:
        # Fallback to simple cache
        app.logger.warning("⚠️ No Redis URL found. Using simple cache.")
        cache_config = {
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
        }
    
    app.config.update(cache_config)
    cache.init_app(app)
    
    # Log cache type being used
    app.logger.info(f"Cache initialized with type: {cache_config['CACHE_TYPE']}")

def get_cache_info():
    """Get information about current cache configuration"""
    return {
        'type': cache.config.get('CACHE_TYPE'),
        'timeout': cache.config.get('CACHE_DEFAULT_TIMEOUT'),
        'redis_url': cache.config.get('CACHE_REDIS_URL', 'Not configured')
    }

# Utility functions
def cache_key(key_name, *args):
    """Generate cache key with arguments"""
    return f"{key_name}:{':'.join(map(str, args))}"

def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching pattern (Redis only)"""
    try:
        if cache.config.get('CACHE_TYPE') == 'redis' and hasattr(cache.cache, '_read_client'):
            keys = cache.cache._read_client.keys(f"taskpal:{pattern}")
            if keys:
                # Remove prefix for deletion
                keys_to_delete = [key.replace('taskpal:', '') for key in keys]
                cache.delete_many(*keys_to_delete)
                current_app.logger.info(f"Invalidated {len(keys_to_delete)} cache keys with pattern: {pattern}")
                return len(keys_to_delete)
    except Exception as e:
        current_app.logger.warning(f"Cache pattern invalidation failed: {e}")
    return 0
