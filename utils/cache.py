"""
Caching utilities for Google Ads Dashboard
Provides disk-based caching with TTL support
"""

import os
import json
import pickle
from typing import Any, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import diskcache as dc
import hashlib
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages disk-based caching with TTL support"""
    
    def __init__(self, cache_dir: str = "data/cache", default_ttl: int = 900):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize disk cache
        self.cache = dc.Cache(cache_dir)
        
        logger.info(f"Cache initialized at {cache_dir} with default TTL {default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            expire_time = ttl or self.default_ttl
            return self.cache.set(key, value, expire=expire_time)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.cache.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.clear()
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and not expired, False otherwise
        """
        return key in self.cache
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        try:
            stats = self.cache.stats()
            return {
                'hits': stats.get('cache_hits', 0),
                'misses': stats.get('cache_misses', 0),
                'size': len(self.cache),
                'volume': self.cache.volume(),
                'directory': self.cache_dir
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Global cache instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        # Get TTL from environment or use default
        default_ttl = int(os.getenv('CACHE_TTL', '3600'))
        _cache_manager = CacheManager(default_ttl=default_ttl)
    return _cache_manager

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of the arguments as cache key
    """
    # Create a string representation of all arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())  # Sort for consistent ordering
    }
    
    # Convert to JSON string and hash
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time-to-live in seconds (uses default if None)
        key_prefix: Prefix for cache key
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            arg_key = generate_cache_key(*args, **kwargs)
            cache_key = f"{key_prefix}{func_name}:{arg_key}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func_name}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func_name}, executing function")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_clear = lambda: get_cache_manager().clear()
        wrapper.cache_info = lambda: get_cache_manager().get_stats()
        
        return wrapper
    
    return decorator

def cache_google_ads_data(customer_id: str, data_type: str, ttl: int = 600):
    """
    Specialized decorator for caching Google Ads API data
    
    Args:
        customer_id: Google Ads customer ID
        data_type: Type of data being cached (campaigns, billing, etc.)
        ttl: Time-to-live in seconds (default 10 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate specialized cache key for Google Ads data
            cache_key = f"google_ads:{customer_id}:{data_type}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Google Ads cache hit for {data_type} - {customer_id}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Google Ads cache miss for {data_type} - {customer_id}")
            result = func(*args, **kwargs)
            
            # Cache the result with specified TTL
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator

def invalidate_customer_cache(customer_id: str):
    """
    Invalidate all cached data for a specific customer
    
    Args:
        customer_id: Google Ads customer ID
    """
    cache_manager = get_cache_manager()
    
    # Get all keys and find ones matching the customer
    try:
        keys_to_delete = []
        for key in cache_manager.cache:
            if f"google_ads:{customer_id}:" in key:
                keys_to_delete.append(key)
        
        # Delete matching keys
        for key in keys_to_delete:
            cache_manager.delete(key)
        
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for customer {customer_id}")
        
    except Exception as e:
        logger.error(f"Error invalidating cache for customer {customer_id}: {e}")

def warm_cache(func: Callable, *args, **kwargs):
    """
    Pre-warm cache by executing function
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
    """
    try:
        result = func(*args, **kwargs)
        logger.info(f"Cache warmed for {func.__name__}")
        return result
    except Exception as e:
        logger.error(f"Error warming cache for {func.__name__}: {e}")
        return None