"""
Debug routes for cache testing and monitoring
Only available in development mode
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.cache_service import CacheService
from app.extensions.cache import get_cache_info
from app.utils.responses import api_response
import os

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')


@debug_bp.before_request
def check_debug_mode():
    """Ensure debug routes are only available in development"""
    if os.getenv('FLASK_ENV') != 'development':
        return api_response(
            success=False,
            message="Debug routes are only available in development mode",
            status_code=403
        )


@debug_bp.route('/cache/info', methods=['GET'])
@jwt_required()
def cache_info():
    """Get cache information and statistics"""
    try:
        cache_stats = CacheService.get_cache_stats()
        cache_config = get_cache_info()
        
        return api_response(
            success=True,
            data={
                'config': cache_config,
                'stats': cache_stats
            },
            message="Cache information retrieved successfully"
        )
    except Exception as e:
        return api_response(
            success=False,
            message=f"Error getting cache info: {str(e)}",
            status_code=500
        )


@debug_bp.route('/cache/test', methods=['POST'])
@jwt_required()
def test_cache():
    """Test cache operations"""
    try:
        user_id = get_jwt_identity()
        test_data = request.get_json() or {}
        
        # Test basic cache operations
        test_key = f"debug_test:{user_id}"
        test_value = {
            "message": test_data.get("message", "Cache test"),
            "timestamp": test_data.get("timestamp", "2024"),
            "user_id": user_id
        }
        
        # Set cache
        set_success = CacheService.set_cached(test_key, test_value, timeout=300)
        
        # Get cache
        cached_value = CacheService.get_cached(test_key)
        
        # Test user-specific caching
        user_profile_success = CacheService.cache_user_profile(
            str(user_id), 
            {"id": user_id, "test": True}, 
            timeout=60
        )
        
        cached_profile = CacheService.get_cached_user_profile(str(user_id))
        
        return api_response(
            success=True,
            data={
                'basic_cache': {
                    'set_success': set_success,
                    'get_success': cached_value == test_value,
                    'cached_value': cached_value
                },
                'user_cache': {
                    'set_success': user_profile_success,
                    'get_success': cached_profile is not None,
                    'cached_profile': cached_profile
                }
            },
            message="Cache test completed"
        )
        
    except Exception as e:
        return api_response(
            success=False,
            message=f"Cache test failed: {str(e)}",
            status_code=500
        )


@debug_bp.route('/cache/clear', methods=['POST'])
@jwt_required()
def clear_cache():
    """Clear cache by pattern or all"""
    try:
        data = request.get_json() or {}
        pattern = data.get('pattern')
        
        if pattern:
            # Clear specific pattern
            cleared_count = CacheService.clear_cache_pattern(pattern)
            message = f"Cleared {cleared_count} cache entries matching pattern: {pattern}"
        else:
            # Clear all cache (dangerous!)
            from app.extensions.cache import clear_all_cache
            cleared_count = clear_all_cache()
            message = f"Cleared all cache: {cleared_count} entries"
        
        return api_response(
            success=True,
            data={'cleared_count': cleared_count},
            message=message
        )
        
    except Exception as e:
        return api_response(
            success=False,
            message=f"Cache clear failed: {str(e)}",
            status_code=500
        )


@debug_bp.route('/cache/keys', methods=['GET'])
@jwt_required()
def list_cache_keys():
    """List cache keys (Redis only)"""
    try:
        pattern = request.args.get('pattern', '*')
        
        from app.extensions.cache import get_redis_client
        redis_client = get_redis_client()
        
        if not redis_client:
            return api_response(
                success=False,
                message="Redis client not available",
                status_code=400
            )
        
        keys = redis_client.keys(f"taskpal:{pattern}")
        # Remove prefix for display
        display_keys = [key.replace('taskpal:', '') for key in keys]
        
        return api_response(
            success=True,
            data={
                'pattern': pattern,
                'keys': display_keys,
                'count': len(display_keys)
            },
            message=f"Found {len(display_keys)} cache keys"
        )
        
    except Exception as e:
        return api_response(
            success=False,
            message=f"Error listing cache keys: {str(e)}",
            status_code=500
        )