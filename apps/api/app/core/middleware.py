from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds essential HTTP security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class InMemoryRateLimiter:
    """Sliding-window rate limiter keyed by client identifier (e.g., IP address)."""

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, client_key: str) -> tuple[bool, int, float]:
        now = time.time()
        cutoff = now - self.window_seconds
        queue = self._history[client_key]

        while queue and queue[0] < cutoff:
            queue.popleft()

        if len(queue) >= self.max_requests:
            retry_after = round(queue[0] + self.window_seconds - now, 2)
            return False, 0, max(0.0, retry_after)

        queue.append(now)
        remaining = self.max_requests - len(queue)
        return True, remaining, 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing sliding-window rate limits per client IP."""

    def __init__(self, app, limiter: InMemoryRateLimiter | None = None):
        super().__init__(app)
        self.limiter = limiter or InMemoryRateLimiter(max_requests=120, window_seconds=60.0)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining, retry_after = self.limiter.is_allowed(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
