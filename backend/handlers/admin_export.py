"""
Admin handler for data export.

Provides endpoints to export analytics data in CSV format.
"""

import logging
import csv
import io
from typing import Dict, Any
from auth.admin import require_admin
from services.dynamo import get_all_registered_users, get_all_users_progress
from services.progress_service import get_user_stats
from utils.responses import error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@require_admin
def handle_export_users(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/export/users endpoint.

    Export all users with their stats as CSV.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)
        query_params: Query string parameters (unused)

    Returns:
        dict: API Gateway response with CSV data

    Response Format (200 OK):
        CSV file with headers:
        user_id,username,github_username,registered_at,completed_count,overall_completion,current_streak,quizzes_passed
    """
    try:
        # Get all registered users
        all_users = get_all_registered_users()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "user_id",
                "username",
                "github_username",
                "registered_at",
                "completed_count",
                "overall_completion",
                "current_streak",
                "quizzes_passed",
            ]
        )

        # Write user data
        for user in all_users:
            try:
                stats = get_user_stats(user["user_id"])
                writer.writerow(
                    [
                        user["user_id"],
                        user.get("username", ""),
                        user.get("github_username", ""),
                        user.get("registered_at", ""),
                        stats.get("completed_count", 0),
                        stats.get("overall_completion", 0),
                        stats.get("current_streak", 0),
                        stats.get("quizzes_passed", 0),
                    ]
                )
            except Exception as e:
                logger.warning(
                    f"Failed to get stats for user {user['user_id']}: {str(e)}"
                )
                # Write user without stats
                writer.writerow(
                    [
                        user["user_id"],
                        user.get("username", ""),
                        user.get("github_username", ""),
                        user.get("registered_at", ""),
                        0,
                        0,
                        0,
                        0,
                    ]
                )

        csv_content = output.getvalue()
        output.close()

        logger.info(f"Users export by admin {username}: {len(all_users)} users")

        # Return CSV response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": 'attachment; filename="users_export.csv"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": csv_content,
        }

    except Exception as e:
        logger.error(f"Error exporting users: {str(e)}")
        return error_response(500, "Internal server error")


@require_admin
def handle_export_capstone_submissions(
    headers: Dict[str, str],
    username: str,
    user_id: str,
    query_params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Handle GET /admin/export/capstone-submissions endpoint.

    Export all capstone submissions as CSV.

    Args:
        headers: Request headers (provided by decorator)
        username: Authenticated admin username (provided by decorator)
        user_id: Authenticated user ID (provided by decorator)
        query_params: Query string parameters (unused)

    Returns:
        dict: API Gateway response with CSV data

    Response Format (200 OK):
        CSV file with headers:
        user_id,github_username,content_id,repo_url,submitted_at
    """
    try:
        from handlers.admin_submissions import get_capstone_submissions
        import os

        table_name = os.environ.get("PROGRESS_TABLE")
        if not table_name:
            return error_response(503, "Service unavailable")

        # Get all capstone submissions (no pagination)
        submissions, total_count = get_capstone_submissions(table_name, 1, 10000)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "user_id",
                "github_username",
                "content_id",
                "repo_url",
                "submitted_at",
            ]
        )

        # Write submission data
        for submission in submissions:
            writer.writerow(
                [
                    submission.get("user_id", ""),
                    submission.get("github_username", ""),
                    submission.get("content_id", ""),
                    submission.get("repo_url", ""),
                    submission.get("submitted_at", ""),
                ]
            )

        csv_content = output.getvalue()
        output.close()

        logger.info(
            f"Capstone submissions export by admin {username}: {len(submissions)} submissions"
        )

        # Return CSV response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": 'attachment; filename="capstone_submissions.csv"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": csv_content,
        }

    except Exception as e:
        logger.error(f"Error exporting capstone submissions: {str(e)}")
        return error_response(500, "Internal server error")
