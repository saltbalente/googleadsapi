"""
Advanced Caching System for Google Ads Dashboard
Provides disk-based caching with TTL, compression, and monitoring
Version: 2.0 Ultra
Author: saltbalente
Date: 2025-01-13
"""

import os
import json
import pickle
import zlib
import base64
from typing import Any, Optional, Union, Callable, List, Tuple
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager
import diskcache as dc
import hashlib
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CACHE MANAGER CLASS
# ============================================================================

class CacheManager:
    """
    Advanced disk-based cache manager with TTL, compression, and monitoring
    
    Features:
        - Disk-based persistence (survives restarts)
        - TTL (Time-To-Live) support
        - Compression for large data
        - Cache statistics and monitoring
        - Batch operations
        - Specialized Google Ads caching
    """
    
    def __init__(self, cache_dir: str = "data/cache", default_ttl: int = 900):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (default: 15 minutes)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize disk cache
        self.cache = dc.Cache(cache_dir)
        
        logger.info(f"✅ Cache initialized at {cache_dir} with default TTL {default_ttl}s")
    
    # ========================================================================
    # BASIC OPERATIONS
    # ========================================================================
    
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
            logger.error(f"❌ Error getting cache key {key}: {e}")
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
            success = self.cache.set(key, value, expire=expire_time)
            
            if success:
                logger.debug(f"✓ Cached {key} with TTL {expire_time}s")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Error setting cache key {key}: {e}")
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
            deleted = self.cache.delete(key)
            if deleted:
                logger.debug(f"🗑️ Deleted cache key {key}")
            return deleted
        
        except Exception as e:
            logger.error(f"❌ Error deleting cache key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.clear()
            logger.info("🧹 Cache cleared successfully")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache and is not expired
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and not expired, False otherwise
        """
        try:
            return key in self.cache
        except:
            return False
    
    # ========================================================================
    # COMPRESSED CACHE OPERATIONS
    # ========================================================================
    
    def set_compressed(self, key: str, value: Any, ttl: Optional[int] = None, 
                      compression_threshold: int = 102400) -> bool:
        """
        Set value in cache with automatic compression for large data
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            compression_threshold: Compress if size > threshold bytes (default: 100KB)
            
        Returns:
            True if successful
        """
        try:
            # Serializar con pickle
            pickled = pickle.dumps(value)
            original_size = len(pickled)
            
            # Comprimir si supera el threshold
            if original_size > compression_threshold:
                compressed = zlib.compress(pickled, level=6)
                compressed_size = len(compressed)
                
                data = {
                    'compressed': True,
                    'data': base64.b64encode(compressed).decode('utf-8'),
                    'original_size': original_size,
                    'compressed_size': compressed_size
                }
                
                reduction = (1 - compressed_size / original_size) * 100
                logger.info(f"💾 Compressed {key}: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({reduction:.1f}% reduction)")
            else:
                data = {
                    'compressed': False,
                    'data': value,
                    'original_size': original_size
                }
            
            return self.set(key, data, ttl)
        
        except Exception as e:
            logger.error(f"❌ Error setting compressed cache {key}: {e}")
            return False
    
    def get_compressed(self, key: str) -> Optional[Any]:
        """
        Get compressed value from cache and decompress if needed
        
        Args:
            key: Cache key
            
        Returns:
            Decompressed value or None
        """
        try:
            data = self.get(key)
            
            if data is None:
                return None
            
            # Si es dict con flag de compresión
            if isinstance(data, dict) and 'compressed' in data:
                if data['compressed']:
                    # Descomprimir
                    compressed = base64.b64decode(data['data'])
                    pickled = zlib.decompress(compressed)
                    return pickle.loads(pickled)
                else:
                    return data['data']
            
            # Si no tiene formato especial, retornar tal cual
            return data
        
        except Exception as e:
            logger.error(f"❌ Error getting compressed cache {key}: {e}")
            return None
    
    # ========================================================================
    # STATISTICS AND MONITORING
    # ========================================================================
    
    def get_stats(self) -> dict:
        """
        Get cache statistics - Compatible with all diskcache versions
        
        Returns:
            Dictionary with cache stats
        """
        try:
            # Intentar obtener stats del cache
            try:
                stats_raw = self.cache.stats(enable=True)
                
                # Manejar diferentes tipos de retorno de diskcache
                if hasattr(stats_raw, '_asdict'):  # Es namedtuple
                    stats_dict = stats_raw._asdict()
                elif isinstance(stats_raw, dict):  # Ya es dict
                    stats_dict = stats_raw
                elif isinstance(stats_raw, tuple):  # Es tupla simple
                    stats_dict = {}
                else:
                    stats_dict = {}
            
            except (AttributeError, TypeError):
                # Si stats() no está disponible
                stats_dict = {}
            
            # Construir respuesta con datos seguros
            return {
                'hits': stats_dict.get('cache_hits', 0),
                'misses': stats_dict.get('cache_misses', 0),
                'size': len(self.cache),
                'volume': self.cache.volume(),
                'directory': self.cache_dir,
                'evictions': stats_dict.get('evictions', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {
                'hits': 0,
                'misses': 0,
                'size': 0,
                'volume': 0,
                'directory': self.cache_dir,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_cache_dashboard_data(self) -> dict:
        """
        Get comprehensive cache metrics for monitoring dashboard
        
        Returns:
            Dict with detailed metrics and health status
        """
        try:
            stats = self.get_stats()
            
            # Calcular métricas adicionales
            total_requests = stats.get('hits', 0) + stats.get('misses', 0)
            hit_rate = (stats.get('hits', 0) / total_requests * 100) if total_requests > 0 else 0
            miss_rate = 100 - hit_rate
            
            # Tamaño del cache en MB
            volume_mb = stats.get('volume', 0) / (1024 * 1024)
            
            # Estado de salud
            if hit_rate > 80:
                health_status = 'excellent'
                health_color = 'green'
                recommendation = "✅ Cache funcionando óptimamente"
            elif hit_rate > 50:
                health_status = 'good'
                health_color = 'blue'
                recommendation = "✓ Cache funcionando bien, considera aumentar TTL para mejorar"
            elif hit_rate > 20:
                health_status = 'degraded'
                health_color = 'yellow'
                recommendation = "⚠️ Hit rate bajo, revisa patrones de acceso o aumenta TTL"
            else:
                health_status = 'poor'
                health_color = 'red'
                recommendation = "❌ Hit rate crítico, considera pre-warming o revisar estrategia de cache"
            
            return {
                'stats': stats,
                'metrics': {
                    'total_requests': total_requests,
                    'hit_rate': round(hit_rate, 2),
                    'miss_rate': round(miss_rate, 2),
                    'volume_mb': round(volume_mb, 2),
                    'avg_ttl_seconds': self.default_ttl,
                    'keys_count': stats.get('size', 0),
                    'evictions': stats.get('evictions', 0)
                },
                'health': {
                    'status': health_status,
                    'color': health_color,
                    'recommendation': recommendation,
                    'score': round(hit_rate, 1)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {e}")
            return {
                'stats': {},
                'metrics': {},
                'health': {
                    'status': 'error',
                    'color': 'red',
                    'recommendation': f"❌ Error: {str(e)}",
                    'score': 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    @contextmanager
    def batch_operations(self):
        """
        Context manager for batch cache operations (better performance)
        
        Usage:
            with cache_manager.batch_operations():
                cache_manager.set('key1', 'value1')
                cache_manager.set('key2', 'value2')
                cache_manager.set('key3', 'value3')
        """
        try:
            yield self
        finally:
            # Asegurar que los cambios se escriban
            pass
    
    def set_many(self, items: dict, ttl: Optional[int] = None) -> int:
        """
        Set multiple key-value pairs in batch
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Time-to-live for all items
            
        Returns:
            Number of successfully cached items
        """
        count = 0
        with self.batch_operations():
            for key, value in items.items():
                if self.set(key, value, ttl):
                    count += 1
        
        logger.info(f"📦 Batch cached {count}/{len(items)} items")
        return count
    
    def get_many(self, keys: List[str]) -> dict:
        """
        Get multiple values in batch
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary with available key-value pairs
        """
        results = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                results[key] = value
        
        logger.debug(f"📦 Batch retrieved {len(results)}/{len(keys)} items")
        return results


# ============================================================================
# GLOBAL CACHE INSTANCE
# ============================================================================

_cache_manager = None

def get_cache_manager() -> CacheManager:
    """
    Get global cache manager singleton instance
    
    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        # Get TTL from environment or use default
        default_ttl = int(os.getenv('CACHE_TTL', '3600'))
        cache_dir = os.getenv('CACHE_DIR', 'data/cache')
        _cache_manager = CacheManager(cache_dir=cache_dir, default_ttl=default_ttl)
    
    return _cache_manager


# ============================================================================
# CACHE KEY GENERATION
# ============================================================================

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a deterministic cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of the arguments as cache key
    """
    try:
        # Create a string representation of all arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())  # Sort for consistent ordering
        }
        
        # Convert to JSON string and hash
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    except Exception as e:
        logger.error(f"❌ Error generating cache key: {e}")
        # Fallback: usar timestamp + random
        import time
        import random
        return hashlib.md5(f"{time.time()}_{random.random()}".encode()).hexdigest()


# ============================================================================
# DECORATORS
# ============================================================================

def cached(ttl: Optional[int] = None, key_prefix: str = "", use_compression: bool = False):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time-to-live in seconds (uses default if None)
        key_prefix: Prefix for cache key (useful for namespacing)
        use_compression: Use compression for large results
        
    Returns:
        Decorated function
        
    Usage:
        @cached(ttl=3600, key_prefix="user_")
        def get_user_data(user_id):
            return expensive_operation(user_id)
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
            if use_compression:
                cached_result = cache_manager.get_compressed(cache_key)
            else:
                cached_result = cache_manager.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"💾 Cache HIT for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"❌ Cache MISS for {func.__name__}, executing...")
            result = func(*args, **kwargs)
            
            # Cache the result
            if use_compression:
                cache_manager.set_compressed(cache_key, result, ttl)
            else:
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
        data_type: Type of data (campaigns, ads, billing, etc.)
        ttl: Time-to-live in seconds (default 10 minutes)
        
    Usage:
        @cache_google_ads_data(customer_id="123456", data_type="campaigns", ttl=600)
        def fetch_campaigns(date_range):
            return api.get_campaigns(date_range)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate specialized cache key for Google Ads data
            arg_key = generate_cache_key(*args, **kwargs)
            cache_key = f"google_ads:{customer_id}:{data_type}:{arg_key}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"💾 Google Ads cache HIT: {data_type} - {customer_id}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"❌ Google Ads cache MISS: {data_type} - {customer_id}")
            result = func(*args, **kwargs)
            
            # Cache the result with specified TTL
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


# ============================================================================
# CACHE INVALIDATION
# ============================================================================

def invalidate_customer_cache(customer_id: str) -> int:
    """
    Invalidate all cached data for a specific Google Ads customer
    
    Args:
        customer_id: Google Ads customer ID
        
    Returns:
        Number of invalidated cache entries
    """
    cache_manager = get_cache_manager()
    
    try:
        keys_to_delete = []
        
        # Find all keys matching the customer
        for key in cache_manager.cache:
            if f"google_ads:{customer_id}:" in key:
                keys_to_delete.append(key)
        
        # Delete matching keys
        deleted_count = 0
        for key in keys_to_delete:
            if cache_manager.delete(key):
                deleted_count += 1
        
        logger.info(f"🗑️ Invalidated {deleted_count} cache entries for customer {customer_id}")
        return deleted_count
    
    except Exception as e:
        logger.error(f"❌ Error invalidating cache for customer {customer_id}: {e}")
        return 0


def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache entries matching a pattern
    
    Args:
        pattern: String pattern to match in cache keys
        
    Returns:
        Number of invalidated entries
    """
    cache_manager = get_cache_manager()
    
    try:
        keys_to_delete = []
        
        for key in cache_manager.cache:
            if pattern in key:
                keys_to_delete.append(key)
        
        deleted_count = 0
        for key in keys_to_delete:
            if cache_manager.delete(key):
                deleted_count += 1
        
        logger.info(f"🗑️ Invalidated {deleted_count} cache entries matching '{pattern}'")
        return deleted_count
    
    except Exception as e:
        logger.error(f"❌ Error invalidating cache pattern '{pattern}': {e}")
        return 0


# ============================================================================
# CACHE WARMING
# ============================================================================

def warm_cache(func: Callable, *args, **kwargs) -> Optional[Any]:
    """
    Pre-warm cache by executing function
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or None if error
    """
    try:
        result = func(*args, **kwargs)
        logger.info(f"🔥 Cache warmed for {func.__name__}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Error warming cache for {func.__name__}: {e}")
        return None


def warm_cache_batch(warm_functions: List[Tuple[Callable, list, dict]]) -> List[Tuple[str, bool, Optional[str]]]:
    """
    Pre-warm multiple functions in parallel
    
    Args:
        warm_functions: List of tuples (function, args, kwargs)
        
    Returns:
        List of tuples (function_name, success, error_message)
        
    Usage:
        results = warm_cache_batch([
            (get_campaigns, ['123'], {}),
            (get_billing, ['123'], {'date_range': '30d'}),
        ])
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(warm_cache, func, *args, **kwargs): (func, args, kwargs)
            for func, args, kwargs in warm_functions
        }
        
        for future in as_completed(futures):
            func, args, kwargs = futures[future]
            try:
                future.result()
                results.append((func.__name__, True, None))
                logger.info(f"✅ Warmed cache for {func.__name__}")
            
            except Exception as e:
                results.append((func.__name__, False, str(e)))
                logger.error(f"❌ Failed to warm cache for {func.__name__}: {e}")
    
    return results


# ============================================================================
# STREAMLIT WIDGETS
# ============================================================================

def show_cache_widget():
    """
    Streamlit widget to display and manage cache
    
    Usage:
        import streamlit as st
        from utils.cache_manager import show_cache_widget
        
        with st.sidebar:
            show_cache_widget()
    """
    try:
        import streamlit as st
    except ImportError:
        logger.error("Streamlit not installed. Cannot show cache widget.")
        return
    
    cache_manager = get_cache_manager()
    
    st.markdown("### 💾 Cache Manager")
    
    # Get dashboard data
    dashboard_data = cache_manager.get_cache_dashboard_data()
    metrics = dashboard_data.get('metrics', {})
    health = dashboard_data.get('health', {})
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hit_rate = metrics.get('hit_rate', 0)
        st.metric(
            "Hit Rate",
            f"{hit_rate:.1f}%",
            delta=f"{hit_rate - 50:.1f}%" if hit_rate > 0 else None
        )
    
    with col2:
        st.metric("Keys", metrics.get('keys_count', 0))
    
    with col3:
        st.metric("Size", f"{metrics.get('volume_mb', 0):.1f} MB")
    
    with col4:
        st.metric("Requests", metrics.get('total_requests', 0))
    
    # Health status
    status = health.get('status', 'unknown')
    recommendation = health.get('recommendation', '')
    
    if status == 'excellent':
        st.success(recommendation)
    elif status == 'good':
        st.info(recommendation)
    elif status == 'degraded':
        st.warning(recommendation)
    else:
        st.error(recommendation)
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clear Cache", use_container_width=True):
            if cache_manager.clear():
                st.success("✅ Cache cleared")
                st.rerun()
            else:
                st.error("❌ Error clearing cache")
    
    with col2:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()
    
    # Expandable details
    with st.expander("📊 Detailed Stats"):
        st.json(dashboard_data)


def show_cache_sidebar():
    """
    Simplified cache widget for sidebar
    
    Usage:
        from utils.cache_manager import show_cache_sidebar
        show_cache_sidebar()
    """
    try:
        import streamlit as st
    except ImportError:
        return
    
    cache_manager = get_cache_manager()
    dashboard_data = cache_manager.get_cache_dashboard_data()
    metrics = dashboard_data.get('metrics', {})
    
    with st.sidebar:
        st.markdown("### 💾 Cache")
        
        # Compact metrics
        st.metric("Hit Rate", f"{metrics.get('hit_rate', 0):.0f}%")
        st.metric("Keys", metrics.get('keys_count', 0))
        
        # Clear button
        if st.button("🧹 Clear", use_container_width=True):
            cache_manager.clear()
            st.rerun()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_cache_size_mb() -> float:
    """Get current cache size in megabytes"""
    cache_manager = get_cache_manager()
    stats = cache_manager.get_stats()
    return stats.get('volume', 0) / (1024 * 1024)


def get_cache_hit_rate() -> float:
    """Get current cache hit rate percentage"""
    cache_manager = get_cache_manager()
    dashboard_data = cache_manager.get_cache_dashboard_data()
    return dashboard_data.get('metrics', {}).get('hit_rate', 0.0)


def is_cache_healthy() -> bool:
    """Check if cache is in healthy state"""
    hit_rate = get_cache_hit_rate()
    return hit_rate > 50.0


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'CacheManager',
    'get_cache_manager',
    'generate_cache_key',
    'cached',
    'cache_google_ads_data',
    'invalidate_customer_cache',
    'invalidate_pattern',
    'warm_cache',
    'warm_cache_batch',
    'show_cache_widget',
    'show_cache_sidebar',
    'get_cache_size_mb',
    'get_cache_hit_rate',
    'is_cache_healthy'
]