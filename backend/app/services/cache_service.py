"""
Cache Service
Handles caching operations for improved performance
"""
from flask import current_app
from typing import Any, Optional
from app.extensions import cache


class CacheService:
    """Service for caching operations"""

    @staticmethod
    def get_cache_key(prefix: str, identifier: str) -> str:
        """Generate a cache key"""
        return f"{prefix}:{identifier}"

    @staticmethod
    def get_cached(key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            return cache.get(key)
        except Exception as e:
            current_app.logger.warning(f"Cache get error: {e}")
            return None

    @staticmethod
    def set_cached(key: str, value: Any, timeout: int = None) -> bool:
        """Set value in cache"""
        try:
            cache.set(key, value, timeout)
            return True
        except Exception as e:
            current_app.logger.warning(f"Cache set error: {e}")
            return False

    @staticmethod
    def delete_cached(key: str) -> bool:
        """Delete value from cache"""
        try:
            return cache.delete(key)
        except Exception as e:
            current_app.logger.warning(f"Cache delete error: {e}")
            return False

    @staticmethod
    def clear_cache(prefix: str = None) -> int:
        """Clear all cache or cache with prefix"""
        try:
            if cache.cache.type == 'redis' and hasattr(cache.cache, 'delete_many'):
                # Redis specific
                if prefix:
                    keys = cache.cache._read_client.keys(f"{prefix}*")
                    if keys:
                        cache.cache.delete_many(keys)
                        return len(keys)
                else:
                    # Clear all
                    keys = cache.cache._read_client.keys("*")
                    if keys:
                        cache.cache.delete_many(keys)
                        return len(keys)
            return 0
        except Exception as e:
            current_app.logger.warning(f"Cache clear error: {e}")
            return 0

    # User specific methods
    @staticmethod
    def cache_user(user_data: dict) -> bool:
        """Cache user data"""
        key = CacheService.get_cache_key('user', str(user_data.get('id')))
        return CacheService.set_cached(key, user_data, current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300))

    @staticmethod
    def get_cached_user(user_id: int) -> Optional[dict]:
        """Get cached user data"""
        key = CacheService.get_cache_key('user', str(user_id))
        return CacheService.get_cached(key)

    @staticmethod
    def invalidate_user_cache(user_id: int) -> bool:
        """Invalidate user cache"""
        key = CacheService.get_cache_key('user', str(user_id))
        return CacheService.delete_cached(key)

    # Workspace specific methods
    @staticmethod
    def cache_workspace(workspace_data: dict) -> bool:
        """Cache workspace data"""
        key = CacheService.get_cache_key('workspace', str(workspace_data.get('id')))
        return CacheService.set_cached(key, workspace_data, current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300))

    @staticmethod
    def get_cached_workspace(workspace_id: int) -> Optional[dict]:
        """Get cached workspace data"""
        key = CacheService.get_cache_key('workspace', str(workspace_id))
        return CacheService.get_cached(key)

    @staticmethod
    def invalidate_workspace_cache(workspace_id: int) -> bool:
        """Invalidate workspace cache"""
        key = CacheService.get_cache_key('workspace', str(workspace_id))
        return CacheService.delete_cached(key)

    # Generic methods
    @staticmethod
    def cache_data(key_prefix: str, data_id: str, data: Any) -> bool:
        """Cache any data with prefix and id"""
        key = CacheService.get_cache_key(key_prefix, data_id)
        return CacheService.set_cached(key, data, current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300))

    @staticmethod
    def get_cached_data(key_prefix: str, data_id: str) -> Optional[Any]:
        """Get cached data"""
        key = CacheService.get_cache_key(key_prefix, data_id)
        return CacheService.get_cached(key)

    @staticmethod
    def invalidate_data_cache(key_prefix: str, data_id: str) -> bool:
        """Invalidate specific data cache"""
        key = CacheService.get_cache_key(key_prefix, data_id)
        return CacheService.delete_cached(key)
