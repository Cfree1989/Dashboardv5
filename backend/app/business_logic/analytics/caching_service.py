import os
import time
from typing import Any, Optional, Tuple, Dict
from flask import current_app

class CachingService:
    """Reusable caching service extracted from analytics.py"""
    
    def __init__(self, cache_ttl: Optional[int] = None):
        """Initialize with optional TTL override"""
        self._cache: dict = {}
        self._cache_ttl = cache_ttl or int(os.environ.get('ANALYTICS_CACHE_TTL', '60'))
    
    def _is_testing_environment(self) -> bool:
        """Check if we're in a testing environment"""
        try:
            return current_app.config.get('TESTING', False)
        except Exception:
            # If app context not ready, assume not testing
            return False
    
    def get(self, key: Tuple) -> Optional[Any]:
        """Get cached data if available and not expired"""
        if self._is_testing_environment():
            return None
            
        entry = self._cache.get(key)
        if not entry:
            return None
            
        expires_at, data = entry
        if time.time() >= expires_at:
            try:
                del self._cache[key]
            except Exception:
                pass
            return None
            
        return data
    
    def set(self, key: Tuple, data: Any, ttl: Optional[int] = None) -> None:
        """Cache data with optional TTL override"""
        if self._is_testing_environment():
            return
            
        cache_ttl = ttl or self._cache_ttl
        self._cache[key] = (time.time() + cache_ttl, data)
    
    def invalidate(self, key: Tuple) -> None:
        """Remove specific cache entry"""
        try:
            del self._cache[key]
        except KeyError:
            pass
    
    def clear(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return {
            'total_entries': len(self._cache),
            'cache_ttl': self._cache_ttl,
            'is_testing': self._is_testing_environment()
        }
