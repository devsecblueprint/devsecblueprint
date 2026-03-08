"""
Analytics handler for admin users.

Provides system-wide analytics and statistics.
"""

import logging
import os
from typing import Dict, Any, Set
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from auth.jwt_utils import validate_jwt, extract_token_from_cookie
from services.dynamo import (
    get_all_users_progress,
    get_all_registered_users,
    get_total_capstone_submissions_count,
    get_all_badge_stats,
    get_all_quiz_stats,
)
from utils.responses import error_response, json_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Admin GitHub usernames (GitHub login usernames, e.g., "damienjburks")
ADMIN_USERS = os.environ["ADMIN_USERS"].split(",")


def handle_get_analytics(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /admin/analytics endpoint.

    Returns system-wide analytics including:
    - Total registered users
    - Users with progress
    - Users who completed all courses
    - Average completion rate
    - Total completions

    Args:
        headers: Request headers containing JWT cookie

    Returns:
        dict: API Gateway response with analytics data or error
    """
    try:
        # Extract JWT from cookie
        token = extract_token_from_cookie(headers)

        if not token:
            return error_response(401, "Unauthorized")

        # Validate JWT to get user info
        try:
            payload = validate_jwt(token)
        except Exception as e:
            logger.error(f"JWT validation failed: {str(e)}")
            return error_response(401, "Invalid token")

        username = payload.get("name")
        github_username = payload.get("github_login")

        if not github_username or github_username not in ADMIN_USERS:
            logger.warning(
                f"Non-admin user attempted to access analytics: {github_username}"
            )
            return error_response(403, "Forbidden - Admin access required")

        # Get all users' progress data
        all_progress = get_all_users_progress()

        # Get all registered users
        all_registered = get_all_registered_users()

        # Get capstone submissions count
        total_capstone_submissions = get_total_capstone_submissions_count()

        # Get badge statistics
        badge_stats = get_all_badge_stats()

        # Get quiz statistics
        quiz_stats = get_all_quiz_stats()

        # Get total pages from environment variable (set by Terraform)
        TOTAL_PAGES = int(os.environ.get("TOTAL_MODULE_PAGES", "96"))

        # Calculate analytics
        registered_user_ids: Set[str] = {user["user_id"] for user in all_registered}
        users_with_progress: Set[str] = set()
        users_completed: Set[str] = set()
        total_completions = 0
        user_completion_counts: Dict[str, int] = {}

        # Track active learners (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_learners_7d: Set[str] = set()

        for item in all_progress:
            user_id = item.get("user_id")
            if user_id:
                users_with_progress.add(user_id)
                total_completions += 1

                # Track completions per user
                if user_id not in user_completion_counts:
                    user_completion_counts[user_id] = 0
                user_completion_counts[user_id] += 1

                # Check if user completed all courses
                if user_completion_counts[user_id] >= TOTAL_PAGES:
                    users_completed.add(user_id)

                # Check if this completion was in the last 7 days
                completed_at_str = item.get("completed_at", "")
                if completed_at_str:
                    try:
                        completed_at = datetime.fromisoformat(
                            completed_at_str.replace("Z", "+00:00")
                        )
                        if completed_at >= seven_days_ago:
                            active_learners_7d.add(user_id)
                    except Exception:
                        pass

        # Calculate average completion rate
        total_registered = len(registered_user_ids)
        avg_completion = 0
        if len(users_with_progress) > 0:
            total_completion_percentage = sum(
                min(100.0, (count / TOTAL_PAGES) * 100)
                for count in user_completion_counts.values()
            )
            avg_completion = round(
                total_completion_percentage / len(users_with_progress), 1
            )

        # Calculate registration timeline (last 30 days)
        registration_by_date = defaultdict(int)
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        for user in all_registered:
            registered_at_str = user.get("registered_at", "")
            if registered_at_str:
                try:
                    registered_at = datetime.fromisoformat(
                        registered_at_str.replace("Z", "+00:00")
                    )
                    if registered_at >= thirty_days_ago:
                        date_key = registered_at.strftime("%Y-%m-%d")
                        registration_by_date[date_key] += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to parse registration date: {registered_at_str}"
                    )

        # Create timeline data for last 30 days
        registration_timeline = []
        for i in range(30):
            date = now - timedelta(days=29 - i)
            date_key = date.strftime("%Y-%m-%d")
            registration_timeline.append(
                {"date": date_key, "count": registration_by_date.get(date_key, 0)}
            )

        # Create user_id to username mapping (prefer github_username)
        user_id_to_username = {
            user["user_id"]: user.get("github_username")
            or user.get("username", f"User {user['user_id'][:8]}")
            for user in all_registered
        }

        analytics_data = {
            "total_registered_users": total_registered,
            "active_sessions": 0,  # TODO: Implement session tracking
            "users_with_progress": len(users_with_progress),
            "users_completed_all": len(users_completed),
            "active_learners_7d": len(active_learners_7d),
            "total_capstone_submissions": total_capstone_submissions,
            "average_completion_rate": avg_completion,
            "engagement_rate": (
                round((len(users_with_progress) / total_registered * 100), 1)
                if total_registered > 0
                else 0
            ),
            "badge_stats": badge_stats,
            "quiz_stats": quiz_stats,
            "registration_timeline": registration_timeline,
            "completion_by_user": [
                {
                    "user_id": user_id,
                    "username": user_id_to_username.get(user_id, f"User {user_id[:8]}"),
                    "completed": count,
                    "percentage": min(100.0, round((count / TOTAL_PAGES) * 100, 1)),
                }
                for user_id, count in sorted(
                    user_completion_counts.items(), key=lambda x: x[1], reverse=True
                )
            ][
                :10
            ],  # Top 10 users
        }

        logger.info(f"Analytics requested by admin: {username}")

        return json_response(200, analytics_data)

    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        return error_response(500, "Failed to fetch analytics")
