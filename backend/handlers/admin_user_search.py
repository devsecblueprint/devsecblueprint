"""
Admin handler for user search and lookup.

Provides endpoint to search for users and view their detailed progress.
"""

import logging
import os
from typing import Dict, Any
from auth.admin import require_admin
from services.dynamo import get_all_registered_users
from services.progress_service import get_user_stats, get_user_progress
from services.badge_service import calculate_user_badges, get_badges_earned_count
from utils.responses import json_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_user_search(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/users/search endpoint.

    Search for users by username or GitHub username.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)
        query_params: Query string parameters (q=search_query)

    Query Parameters:
        - q: Search query (searches username and github_username)

    Returns:
        dict: API Gateway response with matching users or error

    Response Format (200 OK):
        {
            "users": [
                {
                    "user_id": "github|12345678",
                    "username": "john_doe",
                    "github_username": "johndoe",
                    "avatar_url": "https://...",
                    "registered_at": "2024-01-15T10:30:00Z",
                    "stats": {
                        "completed_count": 42,
                        "overall_completion": 43.8,
                        "current_streak": 5,
                        "quizzes_passed": 10
                    }
                }
            ],
            "total_results": 1
        }
    """
    try:
        # Get search query
        if query_params is None:
            query_params = {}

        search_query = query_params.get("q", "").strip().lower()

        if not search_query:
            return error_response(400, "Search query parameter 'q' is required")

        # Get all registered users
        all_users = get_all_registered_users()

        # Filter users by search query
        matching_users = []
        for user in all_users:
            username_match = search_query in user.get("username", "").lower()
            github_match = search_query in user.get("github_username", "").lower()

            if username_match or github_match:
                # Get user stats
                try:
                    stats = get_user_stats(user["user_id"])
                    progress_items = get_user_progress(user["user_id"])
                    badges = calculate_user_badges(stats, progress_items)
                    badges_earned = get_badges_earned_count(badges)

                    user_data = {
                        "user_id": user["user_id"],
                        "username": user.get("username", ""),
                        "github_username": user.get("github_username", ""),
                        "avatar_url": user.get("avatar_url", ""),
                        "registered_at": user.get("registered_at", ""),
                        "last_login": user.get("last_login", ""),
                        "stats": {
                            "completed_count": stats.get("completed_count", 0),
                            "overall_completion": stats.get("overall_completion", 0),
                            "quizzes_passed": stats.get("quizzes_passed", 0),
                            "walkthroughs_completed": stats.get(
                                "walkthroughs_completed", 0
                            ),
                            "capstone_submissions": stats.get(
                                "capstone_submissions", 0
                            ),
                            "badges_earned": badges_earned,
                        },
                    }
                    matching_users.append(user_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to get stats for user {user['user_id']}: {str(e)}"
                    )
                    # Include user without stats
                    user_data = {
                        "user_id": user["user_id"],
                        "username": user.get("username", ""),
                        "github_username": user.get("github_username", ""),
                        "avatar_url": user.get("avatar_url", ""),
                        "registered_at": user.get("registered_at", ""),
                        "last_login": user.get("last_login", ""),
                        "stats": {
                            "completed_count": 0,
                            "overall_completion": 0,
                            "quizzes_passed": 0,
                            "walkthroughs_completed": 0,
                            "capstone_submissions": 0,
                            "badges_earned": 0,
                        },
                    }
                    matching_users.append(user_data)

        # Sort by completion (most progress first)
        matching_users.sort(key=lambda x: x["stats"]["completed_count"], reverse=True)

        logger.info(
            f"User search by admin {username}: query='{search_query}', results={len(matching_users)}"
        )

        return json_response(
            200, {"users": matching_users, "total_results": len(matching_users)}
        )

    except Exception as e:
        logger.error(f"Error in user search: {str(e)}")
        return error_response(500, "Internal server error")
