"""In-memory rate limiter for API endpoints using sliding window."""

import time
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SlidingWindowRateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self):
        self._windows: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if a request is allowed under the rate limit."""
        now = time.time()
        cutoff = now - window_seconds

        if key not in self._windows:
            self._windows[key] = []

        # Clean old entries
        self._windows[key] = [ts for ts in self._windows[key] if ts > cutoff]

        if len(self._windows[key]) >= max_requests:
            return False

        self._windows[key].append(now)
        return True

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests in the current window."""
        now = time.time()
        cutoff = now - window_seconds
        if key not in self._windows:
            return max_requests
        active = [ts for ts in self._windows[key] if ts > cutoff]
        return max(0, max_requests - len(active))


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()

# Rate limit configurations per endpoint pattern
RATE_LIMITS = {
    "/api/v2/scrape": {"max_requests": 5, "window_seconds": 60},  # 5 scrapes per minute
    "/api/v3/scrape": {"max_requests": 5, "window_seconds": 60},
    "/api/v4/scrape": {"max_requests": 5, "window_seconds": 60},
    "/api/v5/search": {"max_requests": 10, "window_seconds": 60},  # 10 searches per minute
    "/api/v6/search": {"max_requests": 10, "window_seconds": 60},
    "/jobs/search": {"max_requests": 10, "window_seconds": 60},
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that applies rate limits to scraping endpoints."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Find matching rate limit config
        for pattern, config in RATE_LIMITS.items():
            if path.startswith(pattern):
                key = f"{client_ip}:{pattern}"
                if not rate_limiter.is_allowed(key, config["max_requests"], config["window_seconds"]):
                    remaining = rate_limiter.get_remaining(key, config["max_requests"], config["window_seconds"])
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Try again in a few seconds.",
                        headers={"X-RateLimit-Remaining": str(remaining)}
                    )
                break

        response = await call_next(request)
        return response
