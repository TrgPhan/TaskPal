"""
Cache Extension
Handles application caching for improved performance
"""
from flask_caching import Cache

# Initialize Cache without app context
cache = Cache()

def init_cache(app):
    """Initialize Cache with app"""
    cache_config = {
        'CACHE_TYPE': 'simple',  # Use 'redis' for production
        'CACHE_DEFAULT_TIMEOUT': 300
    }
    
    # Use Redis in production
    if app.config.get('REDIS_URL'):
        cache_config.update({
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': app.config['REDIS_URL']
        })
    
    app.config.update(cache_config)
    cache.init_app(app)

# Utility functions
def cache_key(key_name, *args):
    """Generate cache key with arguments"""
    return f"{key_name}:{':'.join(map(str, args))}"

def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching pattern (Redis only)"""
    if hasattr(cache.cache, 'delete_many'):
        keys = cache.cache._read_client.keys(pattern)
        if keys:
            cache.cache.delete_many(*keys)
