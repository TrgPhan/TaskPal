"""
Cache Service
Handles caching operations for improved performance using Redis
"""
from flask import current_app
from typing import Any, Optional, List
from app.extensions import cache
import json
import pickle


class CacheService:
    """Service for caching operations with Redis optimization"""

    @staticmethod
    def get_cache_key(prefix: str, identifier: str) -> str:
        """Generate a cache key"""
        return f"{prefix}:{identifier}"

    @staticmethod
    def get_cached(key: str) -> Optional[Any]:
        """Get value from cache with error handling"""
        try:
            cached_value = cache.get(key)
            if cached_value is not None:
                current_app.logger.debug(f"Cache HIT for key: {key}")
                return cached_value
            else:
                current_app.logger.debug(f"Cache MISS for key: {key}")
                return None
        except Exception as e:
            current_app.logger.warning(f"Cache get error for key {key}: {e}")
            return None

    @staticmethod
    def set_cached(key: str, value: Any, timeout: int = None) -> bool:
        """Set value in cache with error handling"""
        try:
            if timeout is None:
                timeout = current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
            
            cache.set(key, value, timeout)
            current_app.logger.debug(f"Cache SET for key: {key} (timeout: {timeout}s)")
            return True
        except Exception as e:
            current_app.logger.warning(f"Cache set error for key {key}: {e}")
            return False

    @staticmethod
    def delete_cached(key: str) -> bool:
        """Delete value from cache"""
        try:
            result = cache.delete(key)
            if result:
                current_app.logger.debug(f"Cache DELETE for key: {key}")
            return result
        except Exception as e:
            current_app.logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    @staticmethod
    def delete_many_cached(keys: List[str]) -> int:
        """Delete multiple cache keys"""
        try:
            deleted_count = 0
            for key in keys:
                if CacheService.delete_cached(key):
                    deleted_count += 1
            return deleted_count
        except Exception as e:
            current_app.logger.warning(f"Cache delete many error: {e}")
            return 0

    @staticmethod
    def clear_cache_pattern(pattern: str) -> int:
        """Clear cache keys matching pattern (Redis only)"""
        try:
            if cache.config.get('CACHE_TYPE') == 'redis':
                from app.extensions.cache import invalidate_cache_pattern
                return invalidate_cache_pattern(pattern)
            else:
                current_app.logger.warning("Pattern clearing only supported with Redis cache")
                return 0
        except Exception as e:
            current_app.logger.warning(f"Cache pattern clear error: {e}")
            return 0

    @staticmethod
    def get_cache_stats() -> dict:
        """Get cache statistics (Redis only)"""
        try:
            if cache.config.get('CACHE_TYPE') == 'redis' and hasattr(cache.cache, '_read_client'):
                info = cache.cache._read_client.info()
                return {
                    'redis_version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'cache_type': 'redis'
                }
            else:
                return {'cache_type': cache.config.get('CACHE_TYPE', 'unknown')}
        except Exception as e:
            current_app.logger.warning(f"Cache stats error: {e}")
            return {'error': str(e)}

    # User specific methods with improved key management
    @staticmethod
    def cache_user_profile(user_id: str, user_data: dict, timeout: int = 900) -> bool:
        """Cache user profile data (15 minutes default)"""
        key = CacheService.get_cache_key('user_profile', user_id)
        return CacheService.set_cached(key, user_data, timeout)

    @staticmethod
    def get_cached_user_profile(user_id: str) -> Optional[dict]:
        """Get cached user profile data"""
        key = CacheService.get_cache_key('user_profile', user_id)
        return CacheService.get_cached(key)

    @staticmethod
    def invalidate_user_cache(user_id: str) -> int:
        """Invalidate all user-related cache"""
        keys = [
            f"user_profile:{user_id}",
            f"user_settings:{user_id}",
            f"user_workspaces:{user_id}"
        ]
        return CacheService.delete_many_cached(keys)

    # Workspace specific methods
    @staticmethod
    def cache_workspace_detail(workspace_id: str, user_id: str, workspace_data: dict, timeout: int = 300) -> bool:
        """Cache workspace detail data (5 minutes default)"""
        key = f"workspace_detail:{workspace_id}:{user_id}"
        return CacheService.set_cached(key, workspace_data, timeout)

    @staticmethod
    def get_cached_workspace_detail(workspace_id: str, user_id: str) -> Optional[dict]:
        """Get cached workspace detail data"""
        key = f"workspace_detail:{workspace_id}:{user_id}"
        return CacheService.get_cached(key)

    @staticmethod
    def invalidate_workspace_cache(workspace_id: str) -> int:
        """Invalidate all workspace-related cache"""
        pattern = f"workspace_detail:{workspace_id}:*"
        return CacheService.clear_cache_pattern(pattern)

    # Page specific methods
    @staticmethod
    def cache_page_detail(page_id: str, user_id: str, include_blocks: bool, page_data: dict, timeout: int = 180) -> bool:
        """Cache page detail data (3 minutes default)"""
        key = f"page_detail:{page_id}:{user_id}:{include_blocks}"
        return CacheService.set_cached(key, page_data, timeout)

    @staticmethod
    def get_cached_page_detail(page_id: str, user_id: str, include_blocks: bool) -> Optional[dict]:
        """Get cached page detail data"""
        key = f"page_detail:{page_id}:{user_id}:{include_blocks}"
        return CacheService.get_cached(key)

    @staticmethod
    def invalidate_page_cache(page_id: str) -> int:
        """Invalidate all page-related cache"""
        pattern = f"page_detail:{page_id}:*"
        return CacheService.clear_cache_pattern(pattern)
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
