"""
Request handlers for API endpoints.

This module contains all endpoint handlers organized by domain:
- progress: Progress tracking endpoints
- progress_get: Progress retrieval endpoints
- progress_reset: Progress reset endpoints (admin)
- analytics: Analytics endpoints (admin)
- user: User profile endpoints
- quiz: Quiz submission endpoints
"""

from handlers.progress import handle_progress
from handlers.progress_get import (
    handle_get_progress,
    handle_get_stats,
    handle_get_recent,
    handle_get_badges,
)
from handlers.progress_reset import handle_reset_progress
from handlers.analytics import handle_get_analytics
from handlers.user import handle_get_user_profile
from handlers.quiz import handle_quiz_submit

__all__ = [
    "handle_progress",
    "handle_get_progress",
    "handle_get_stats",
    "handle_get_recent",
    "handle_get_badges",
    "handle_reset_progress",
    "handle_get_analytics",
    "handle_get_user_profile",
    "handle_quiz_submit",
]
