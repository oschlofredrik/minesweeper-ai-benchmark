"""Redis-compatible caching service for Vercel deployment.

Since Vercel serverless functions are stateless, we implement:
1. In-memory cache for the function lifetime
2. Optional Redis support if REDIS_URL is provided
3. Fallback to no caching if neither is available
"""

import os
import json
import time
import pickle
import logging
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Check for Redis configuration
REDIS_URL = os.environ.get('REDIS_URL', '')
CACHE_PREFIX = os.environ.get('CACHE_PREFIX', 'tilts:')
DEFAULT_TTL = int(os.environ.get('CACHE_DEFAULT_TTL', '300'))  # 5 minutes

# Try to import Redis
HAS_REDIS = False
redis_client = None

if REDIS_URL:
    try:
        import redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=False)
        redis_client.ping()
        HAS_REDIS = True
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis: {e}")
        HAS_REDIS = False

class CacheService:
    """Unified cache service with Redis and in-memory fallback."""
    
    def __init__(self):
        self.memory_cache = {}
        self.has_redis = HAS_REDIS
        self.redis = redis_client
        
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{CACHE_PREFIX}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = self._make_key(key)
        
        # Try Redis first
        if self.has_redis:
            try:
                value = self.redis.get(full_key)
                if value:
                    return pickle.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to memory cache
        if full_key in self.memory_cache:
            value, expiry = self.memory_cache[full_key]
            if time.time() < expiry:
                return value
            else:
                del self.memory_cache[full_key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """Set value in cache with TTL."""
        full_key = self._make_key(key)
        
        # Try Redis first
        if self.has_redis:
            try:
                serialized = pickle.dumps(value)
                self.redis.setex(full_key, ttl, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Always set in memory cache as fallback
        expiry = time.time() + ttl
        self.memory_cache[full_key] = (value, expiry)
        
        # Cleanup old entries if memory cache gets too large
        if len(self.memory_cache) > 1000:
            self._cleanup_memory_cache()
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        full_key = self._make_key(key)
        
        # Try Redis first
        if self.has_redis:
            try:
                self.redis.delete(full_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Remove from memory cache
        self.memory_cache.pop(full_key, None)
        return True
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        count = 0
        full_pattern = self._make_key(pattern)
        
        # Redis pattern deletion
        if self.has_redis:
            try:
                keys = self.redis.keys(f"{full_pattern}*")
                if keys:
                    count = self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis delete pattern error: {e}")
        
        # Memory cache pattern deletion
        keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(full_pattern)]
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1
        
        return count
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in cache."""
        full_key = self._make_key(key)
        
        if self.has_redis:
            try:
                return self.redis.incrby(full_key, amount)
            except Exception as e:
                logger.error(f"Redis increment error: {e}")
        
        # Fallback to memory
        if full_key in self.memory_cache:
            value, expiry = self.memory_cache[full_key]
            if isinstance(value, int) and time.time() < expiry:
                new_value = value + amount
                self.memory_cache[full_key] = (new_value, expiry)
                return new_value
        
        # Initialize counter
        self.memory_cache[full_key] = (amount, time.time() + DEFAULT_TTL)
        return amount
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once."""
        result = {}
        
        if self.has_redis:
            try:
                full_keys = [self._make_key(k) for k in keys]
                values = self.redis.mget(full_keys)
                for key, value in zip(keys, values):
                    if value:
                        result[key] = pickle.loads(value)
            except Exception as e:
                logger.error(f"Redis mget error: {e}")
        
        # Fill missing values from memory cache
        for key in keys:
            if key not in result:
                value = self.get(key)
                if value is not None:
                    result[key] = value
        
        return result
    
    def set_many(self, mapping: Dict[str, Any], ttl: int = DEFAULT_TTL) -> bool:
        """Set multiple values at once."""
        if self.has_redis:
            try:
                pipe = self.redis.pipeline()
                for key, value in mapping.items():
                    full_key = self._make_key(key)
                    serialized = pickle.dumps(value)
                    pipe.setex(full_key, ttl, serialized)
                pipe.execute()
            except Exception as e:
                logger.error(f"Redis set_many error: {e}")
        
        # Always set in memory cache
        expiry = time.time() + ttl
        for key, value in mapping.items():
            full_key = self._make_key(key)
            self.memory_cache[full_key] = (value, expiry)
        
        return True
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache."""
        current_time = time.time()
        expired_keys = [k for k, (_, exp) in self.memory_cache.items() if exp < current_time]
        for key in expired_keys:
            del self.memory_cache[key]
    
    def clear(self):
        """Clear all cache entries (use with caution)."""
        if self.has_redis:
            try:
                keys = self.redis.keys(f"{CACHE_PREFIX}*")
                if keys:
                    self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        self.memory_cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'has_redis': self.has_redis,
            'memory_cache_size': len(self.memory_cache),
            'cache_prefix': CACHE_PREFIX
        }
        
        if self.has_redis:
            try:
                info = self.redis.info()
                stats['redis_info'] = {
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed')
                }
            except:
                pass
        
        return stats

# Global cache instance
cache = CacheService()

# Decorator for caching function results
def cached(ttl: int = DEFAULT_TTL, key_func: Optional[Callable] = None):
    """Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__module__}.{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        wrapper.cache_clear = lambda: cache.delete_pattern(f"{func.__module__}.{func.__name__}:")
        return wrapper
    return decorator

# Cache key generators for common patterns
def model_cache_key(model_name: str) -> str:
    """Generate cache key for model-specific data."""
    return f"model:{model_name}"

def session_cache_key(session_id: str) -> str:
    """Generate cache key for session data."""
    return f"session:{session_id}"

def leaderboard_cache_key(game_type: str = "all") -> str:
    """Generate cache key for leaderboard data."""
    return f"leaderboard:{game_type}"

def prompt_search_cache_key(query: str, game_type: Optional[str], tags: Optional[List[str]]) -> str:
    """Generate cache key for prompt search results."""
    tags_str = ",".join(sorted(tags)) if tags else ""
    return f"prompts:{query}:{game_type or 'all'}:{tags_str}"

# Export everything
__all__ = [
    'cache',
    'cached',
    'model_cache_key',
    'session_cache_key',
    'leaderboard_cache_key',
    'prompt_search_cache_key',
    'CacheService'
]