"""
Admin handler for user list and user profile endpoints.

Provides paginated user listing and detailed user profile with stats and badges.
"""

import logging
import math
from typing import Dict, Any
from auth.admin import require_admin
from services.dynamo import (
    get_all_registered_users,
    get_user_profile,
    get_user_walkthrough_progress,
)
from services.progress_service import get_user_stats, get_user_progress
from services.badge_service import calculate_user_badges, get_badges_earned_count
from utils.responses import json_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_list_users(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/users endpoint.

    Returns a paginated list of all registered users sorted alphabetically by username.

    Supports an optional ``search`` query parameter that filters across ALL users
    (username, github_username, gitlab_username) before pagination is applied.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)
        query_params: Query string parameters (page, page_size, search)

    Returns:
        dict: API Gateway response with paginated user list
    """
    try:
        if query_params is None:
            query_params = {}

        # Parse and validate pagination params
        try:
            page = int(query_params.get("page", "1"))
        except (ValueError, TypeError):
            return error_response(400, "Invalid pagination parameters")

        try:
            page_size = int(query_params.get("page_size", "20"))
        except (ValueError, TypeError):
            return error_response(400, "Invalid pagination parameters")

        if page < 1:
            return error_response(400, "Page must be >= 1")

        if page_size < 1 or page_size > 100:
            return error_response(400, "Page size must be between 1 and 100")

        # Get all users
        all_users = get_all_registered_users()

        # Optional server-side search across all users
        search_query = query_params.get("search", "").strip().lower()
        if search_query:
            all_users = [
                u
                for u in all_users
                if search_query in u.get("username", "").lower()
                or search_query in u.get("github_username", "").lower()
                or search_query in u.get("gitlab_username", "").lower()
                or search_query in u.get("bitbucket_username", "").lower()
                or search_query in u.get("provider", "").lower()
            ]

        # Sort alphabetically by username (case-insensitive)
        all_users.sort(key=lambda u: u.get("username", "").lower())

        total_count = len(all_users)
        total_pages = max(1, math.ceil(total_count / page_size))

        # Paginate in-memory
        start = (page - 1) * page_size
        end = start + page_size
        users_page = all_users[start:end]

        logger.info(
            f"List users by admin {username}: page={page}, page_size={page_size}, total={total_count}"
        )

        return json_response(
            200,
            {
                "users": users_page,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return error_response(500, "Failed to retrieve users")


@require_admin
def handle_get_user_profile(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    target_user_id: str = "",
) -> Dict[str, Any]:
    """
    Handle GET /admin/users/{user_id}/profile endpoint.

    Returns detailed user profile with stats and badges.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)
        target_user_id: The user ID to look up

    Returns:
        dict: API Gateway response with user profile, stats, and badges
    """
    try:
        if not target_user_id:
            return error_response(400, "User ID is required")

        # Fetch user profile from DynamoDB
        user = get_user_profile(target_user_id)
        if not user:
            return error_response(404, "User not found")

        # Compute stats with graceful degradation
        try:
            stats = get_user_stats(target_user_id)
            progress_items = get_user_progress(target_user_id)
            badges = calculate_user_badges(stats, progress_items)
        except Exception as e:
            logger.warning(
                f"Failed to compute stats for user {target_user_id}: {str(e)}"
            )
            stats = {
                "completed_count": 0,
                "overall_completion": 0,
                "quizzes_passed": 0,
                "walkthroughs_completed": 0,
                "capstone_submissions": 0,
                "current_streak": 0,
                "longest_streak": 0,
            }
            badges = []

        # Fetch walkthrough progress with graceful degradation
        try:
            walkthrough_progress = get_user_walkthrough_progress(target_user_id)
        except Exception as e:
            logger.warning(
                f"Failed to get walkthrough progress for user {target_user_id}: {str(e)}"
            )
            walkthrough_progress = []

        logger.info(
            f"User profile viewed by admin {username}: target_user_id={target_user_id}"
        )

        return json_response(
            200,
            {
                "user": user,
                "stats": {
                    "completed_count": stats.get("completed_count", 0),
                    "overall_completion": stats.get("overall_completion", 0),
                    "quizzes_passed": stats.get("quizzes_passed", 0),
                    "walkthroughs_completed": stats.get("walkthroughs_completed", 0),
                    "capstone_submissions": stats.get("capstone_submissions", 0),
                    "current_streak": stats.get("current_streak", 0),
                    "longest_streak": stats.get("longest_streak", 0),
                },
                "badges": badges,
                "walkthrough_progress": walkthrough_progress,
            },
        )

    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return error_response(500, "Internal server error")
