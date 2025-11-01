"""
Token Bucket implementation for rate limiting.

Uses asyncio.Lock for thread-safe operations in async context.
"""

import asyncio
import time
from collections import defaultdict
from typing import Callable, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.config import settings


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            bool: True if tokens were consumed, False if not enough tokens
        """
        async with self.lock:
            now = time.time()
            # Refill tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_refill = now
            
            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting HTTP requests.
    
    Uses token bucket algorithm to limit requests per client IP.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per client
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=requests_per_minute,
                refill_rate=requests_per_minute / 60.0
            )
        )
        # Clean up old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health check endpoints but add informational headers
        if request.url.path in ["/health", "/healthz", "/readyz"]:
            response = await call_next(request)
            # Add informational headers (not rate limited)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute)
            return response
        
        # Skip rate limiting if disabled
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean up old buckets periodically
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_buckets()
            self.last_cleanup = now
        
        # Check rate limit
        bucket = self.buckets[client_ip]
        if not await bucket.consume():
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        
        return response
    
    def _cleanup_buckets(self) -> None:
        """Remove buckets that haven't been used recently."""
        now = time.time()
        to_remove = []
        
        for ip, bucket in self.buckets.items():
            # Remove if bucket is full (hasn't been used in a while)
            if bucket.tokens >= bucket.capacity - 1:
                if now - bucket.last_refill > 600:  # 10 minutes
                    to_remove.append(ip)
        
        for ip in to_remove:
            del self.buckets[ip]
