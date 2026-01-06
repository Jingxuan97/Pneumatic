# app/rate_limit.py
"""
Rate limiting middleware for FastAPI.
Supports rate limiting per user (authenticated) and per IP (unauthenticated).
"""
import time
from typing import Dict, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import asyncio


class RateLimiter:
    """Simple in-memory rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store request timestamps: key -> list of timestamps
        self.minute_buckets: Dict[str, list] = defaultdict(list)
        self.hour_buckets: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()

    def _get_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """
        Get rate limit key (user ID if authenticated, IP otherwise).

        Args:
            request: FastAPI request
            user_id: Authenticated user ID (if available)

        Returns:
            Rate limit key
        """
        if user_id:
            return f"user:{user_id}"
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        # Check for forwarded IP (from proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        return f"ip:{client_ip}"

    async def is_allowed(self, request: Request, user_id: Optional[str] = None) -> tuple:
        """
        Check if request is allowed under rate limits.

        Args:
            request: FastAPI request
            user_id: Authenticated user ID (if available)

        Returns:
            Tuple of (is_allowed, error_message)
        """
        async with self.lock:
            key = self._get_key(request, user_id)
            now = time.time()

            # Clean old entries (older than 1 hour)
            self.hour_buckets[key] = [ts for ts in self.hour_buckets[key] if now - ts < 3600]
            self.minute_buckets[key] = [ts for ts in self.minute_buckets[key] if now - ts < 60]

            # Check hourly limit
            if len(self.hour_buckets[key]) >= self.requests_per_hour:
                return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"

            # Check per-minute limit
            if len(self.minute_buckets[key]) >= self.requests_per_minute:
                return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"

            # Add current request
            self.hour_buckets[key].append(now)
            self.minute_buckets[key].append(now)

            return True, None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting."""

    def __init__(self, app, rate_limiter: RateLimiter, exempt_paths: Optional[list] = None):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
            exempt_paths: List of paths to exempt from rate limiting (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exempt_paths = exempt_paths or ["/health", "/ready", "/metrics", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Try to get user ID from request state (set by auth middleware if authenticated)
        user_id = getattr(request.state, "user_id", None)

        # Check rate limit
        allowed, error_msg = await self.rate_limiter.is_allowed(request, user_id)

        if not allowed:
            return Response(
                content=f'{{"detail": "{error_msg}"}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": "60",  # Suggest retry after 60 seconds
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )

        response = await call_next(request)

        # Add rate limit headers
        key = self.rate_limiter._get_key(request, user_id)
        remaining_minute = max(0, self.rate_limiter.requests_per_minute - len(self.rate_limiter.minute_buckets[key]))
        remaining_hour = max(0, self.rate_limiter.requests_per_hour - len(self.rate_limiter.hour_buckets[key]))

        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining_minute)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response
