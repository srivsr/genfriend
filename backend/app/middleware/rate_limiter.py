import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("app.ratelimit")

# In-memory rate limiter (use Redis in multi-instance deployments)
REQUEST_COUNTS: dict[str, list[float]] = defaultdict(list)
MAX_REQUESTS = 100  # per window
WINDOW_SECONDS = 60


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/health/live", "/health/ready", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - WINDOW_SECONDS

        # Clean old entries
        REQUEST_COUNTS[client_ip] = [
            t for t in REQUEST_COUNTS[client_ip] if t > window_start
        ]

        if len(REQUEST_COUNTS[client_ip]) >= MAX_REQUESTS:
            logger.warning("Rate limit exceeded for %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

        REQUEST_COUNTS[client_ip].append(now)
        return await call_next(request)
