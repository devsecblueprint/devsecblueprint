"""Global exception handler.

Catches unhandled exceptions, logs context, and returns a safe 500 response
that never leaks internal details (stack traces, file paths, env vars).
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.error")


def setup_exception_handlers(app: FastAPI) -> None:
    """Register the global exception handler on the app."""

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Log full details internally for debugging — never exposed in response
        logger.error(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        # Return generic error without leaking stack traces, file paths, or env vars
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
