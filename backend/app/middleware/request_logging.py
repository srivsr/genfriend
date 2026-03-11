import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "rid=%s method=%s path=%s status=%d duration=%.1fms",
                request_id, request.method, request.url.path,
                response.status_code, elapsed,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "rid=%s method=%s path=%s error=%s duration=%.1fms",
                request_id, request.method, request.url.path,
                str(e), elapsed,
            )
            raise
