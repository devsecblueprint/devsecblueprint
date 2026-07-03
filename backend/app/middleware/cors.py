"""CORS middleware configuration.

Adds FastAPI's CORSMiddleware with allowed origins sourced from application
settings. Only the configured frontend origin and URL are permitted.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_settings


def setup_cors(app: FastAPI) -> None:
    """Attach CORS middleware with allowed origins from settings.

    Configures:
    - allow_origins: frontend_origin and frontend_url from environment config
    - allow_credentials: True (cookies/auth headers)
    - allow_methods: all HTTP methods
    - allow_headers: all headers
    """
    settings = get_settings()
    allowed_origins = [
        settings.frontend_origin,
        settings.frontend_url,
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
