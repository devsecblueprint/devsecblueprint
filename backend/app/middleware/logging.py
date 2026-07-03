"""Structured request/response logging middleware.

Logs each HTTP request as a JSON object with method, path, status_code,
and duration_ms. Output is structured JSON suitable for CloudWatch ingestion.
"""

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log each HTTP request/response as structured JSON.

    For every request processed, emits a JSON log line containing:
    - method: HTTP method (GET, POST, etc.)
    - path: Request path
    - status_code: Response HTTP status code
    - duration_ms: Time taken to process the request in milliseconds
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        log_entry = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        logger.info(json.dumps(log_entry))
        return response
