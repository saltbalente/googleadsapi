"""
Rate limiting utilities for Google Ads API calls
Implements token bucket algorithm for API rate limiting
"""

import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def wait_for_tokens(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until enough tokens are available
        
        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if tokens were acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.consume(tokens):
                return True
            
            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            # Calculate wait time until next token
            with self.lock:
                self._refill()
                if self.tokens < tokens:
                    tokens_needed = tokens - self.tokens
                    wait_time = tokens_needed / self.refill_rate
                    time.sleep(min(wait_time, 0.1))  # Sleep at most 100ms at a time
                else:
                    time.sleep(0.01)  # Small sleep to prevent busy waiting

class RateLimiter:
    """Rate limiter for Google Ads API calls"""
    
    def __init__(self):
        """Initialize rate limiter with Google Ads API limits"""
        # Google Ads API rate limits (approximate)
        # These are conservative estimates - actual limits may vary
        self.buckets: Dict[str, TokenBucket] = {
            # General API calls - 10,000 operations per day
            'general': TokenBucket(capacity=100, refill_rate=0.115),  # ~10k/day
            
            # Report downloads - more restrictive
            'reports': TokenBucket(capacity=15, refill_rate=0.05),  # ~180/hour
            
            # Mutate operations (create/update/delete)
            'mutate': TokenBucket(capacity=50, refill_rate=0.058),  # ~5k/day
            
            # Search operations
            'search': TokenBucket(capacity=100, refill_rate=0.115),  # ~10k/day
        }
        
        # Track API call statistics
        self.stats = {
            'total_calls': 0,
            'rate_limited_calls': 0,
            'last_reset': datetime.now()
        }
        
        self.stats_lock = threading.Lock()
    
    def acquire(self, operation_type: str = 'general', tokens: int = 1, 
                timeout: Optional[float] = 30.0) -> bool:
        """
        Acquire tokens for API operation
        
        Args:
            operation_type: Type of operation (general, reports, mutate, search)
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait
            
        Returns:
            True if tokens acquired, False if timeout or invalid operation
        """
        if operation_type not in self.buckets:
            logger.warning(f"Unknown operation type: {operation_type}, using 'general'")
            operation_type = 'general'
        
        bucket = self.buckets[operation_type]
        
        # Try to acquire tokens
        success = bucket.wait_for_tokens(tokens, timeout)
        
        # Update statistics
        with self.stats_lock:
            self.stats['total_calls'] += 1
            if not success:
                self.stats['rate_limited_calls'] += 1
        
        if not success:
            logger.warning(f"Rate limit exceeded for {operation_type} operation")
        
        return success
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        with self.stats_lock:
            return {
                **self.stats,
                'rate_limit_percentage': (
                    self.stats['rate_limited_calls'] / max(1, self.stats['total_calls']) * 100
                ),
                'bucket_status': {
                    name: {
                        'tokens': bucket.tokens,
                        'capacity': bucket.capacity,
                        'refill_rate': bucket.refill_rate
                    }
                    for name, bucket in self.buckets.items()
                }
            }
    
    def reset_stats(self):
        """Reset rate limiting statistics"""
        with self.stats_lock:
            self.stats = {
                'total_calls': 0,
                'rate_limited_calls': 0,
                'last_reset': datetime.now()
            }

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def rate_limited(operation_type: str = 'general', tokens: int = 1, timeout: float = 30.0):
    """
    Decorator to apply rate limiting to functions
    
    Args:
        operation_type: Type of operation for rate limiting
        tokens: Number of tokens to consume
        timeout: Maximum time to wait for tokens
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            rate_limiter = get_rate_limiter()
            
            # Try to acquire tokens
            if not rate_limiter.acquire(operation_type, tokens, timeout):
                raise Exception(f"Rate limit exceeded for {operation_type} operation")
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on API responses"""
    
    def __init__(self, initial_rate: float = 1.0):
        """
        Initialize adaptive rate limiter
        
        Args:
            initial_rate: Initial requests per second
        """
        self.current_rate = initial_rate
        self.min_rate = 0.1
        self.max_rate = 10.0
        self.last_request = 0.0
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.lock = threading.Lock()
    
    def wait_and_execute(self, func, *args, **kwargs):
        """
        Execute function with adaptive rate limiting
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        with self.lock:
            # Calculate wait time
            now = time.time()
            time_since_last = now - self.last_request
            min_interval = 1.0 / self.current_rate
            
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                time.sleep(wait_time)
            
            self.last_request = time.time()
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Success - potentially increase rate
            with self.lock:
                self.consecutive_successes += 1
                self.consecutive_failures = 0
                
                # Increase rate after several successes
                if self.consecutive_successes >= 5:
                    self.current_rate = min(self.max_rate, self.current_rate * 1.1)
                    self.consecutive_successes = 0
                    logger.debug(f"Increased rate to {self.current_rate:.2f} req/s")
            
            return result
            
        except Exception as e:
            # Check if it's a rate limit error
            if self._is_rate_limit_error(e):
                with self.lock:
                    self.consecutive_failures += 1
                    self.consecutive_successes = 0
                    
                    # Decrease rate on rate limit errors
                    self.current_rate = max(self.min_rate, self.current_rate * 0.5)
                    logger.warning(f"Rate limited, decreased rate to {self.current_rate:.2f} req/s")
                
                # Wait longer before retrying
                time.sleep(2.0)
            
            raise
    
    def _is_rate_limit_error(self, error) -> bool:
        """Check if error is related to rate limiting"""
        error_str = str(error).lower()
        rate_limit_indicators = [
            'rate limit',
            'quota exceeded',
            'too many requests',
            'throttled',
            'rate_limit_exceeded'
        ]
        
        return any(indicator in error_str for indicator in rate_limit_indicators)

def adaptive_rate_limited(initial_rate: float = 1.0):
    """
    Decorator for adaptive rate limiting
    
    Args:
        initial_rate: Initial requests per second
    """
    limiter = AdaptiveRateLimiter(initial_rate)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            return limiter.wait_and_execute(func, *args, **kwargs)
        return wrapper
    return decorator