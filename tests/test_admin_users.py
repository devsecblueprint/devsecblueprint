"""
Unit tests for admin user list and profile endpoints.

Tests handle_list_users and handle_get_user_profile handlers.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

SAMPLE_USERS = [
    {
        "user_id": "1",
        "username": "Alice",
        "github_username": "alice",
        "gitlab_username": "",
        "provider": "github",
        "avatar_url": "https://example.com/alice.png",
        "registered_at": "2024-03-01T00:00:00Z",
        "last_login": "2024-03-25T00:00:00Z",
    },
    {
        "user_id": "2",
        "username": "Bob",
        "github_username": "bob",
        "gitlab_username": "",
        "provider": "github",
        "avatar_url": "https://example.com/bob.png",
        "registered_at": "2024-02-01T00:00:00Z",
        "last_login": "2024-03-20T00:00:00Z",
    },
    {
        "user_id": "3",
        "username": "Charlie",
        "github_username": "",
        "gitlab_username": "charlie",
        "provider": "gitlab",
        "avatar_url": "https://example.com/charlie.png",
        "registered_at": "2024-01-01T00:00:00Z",
        "last_login": "2024-03-15T00:00:00Z",
    },
]


def _bypass_admin(fn):
    """Call the handler directly, bypassing the @require_admin decorator."""
    # The actual function is wrapped by @require_admin, so we access __wrapped__
    return fn.__wrapped__


class TestHandleListUsers:
    """Tests for handle_list_users endpoint."""

    @patch("backend.handlers.admin_users.get_all_registered_users")
    def test_returns_paginated_results(self, mock_get_users):
        from backend.handlers.admin_users import handle_list_users

        mock_get_users.return_value = list(SAMPLE_USERS)

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page": "1", "page_size": "2"},
        )

        body = json.loads(result["body"])
        assert result["statusCode"] == 200
        assert len(body["users"]) == 2
        assert body["total_count"] == 3
        assert body["page"] == 1
        assert body["page_size"] == 2
        assert body["total_pages"] == 2

    @patch("backend.handlers.admin_users.get_all_registered_users")
    def test_sorts_by_registered_at_desc(self, mock_get_users):
        from backend.handlers.admin_users import handle_list_users

        mock_get_users.return_value = list(SAMPLE_USERS)

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page": "1", "page_size": "10"},
        )

        body = json.loads(result["body"])
        dates = [u["registered_at"] for u in body["users"]]
        assert dates == sorted(dates, reverse=True)

    @patch("backend.handlers.admin_users.get_all_registered_users")
    def test_default_pagination(self, mock_get_users):
        from backend.handlers.admin_users import handle_list_users

        mock_get_users.return_value = list(SAMPLE_USERS)

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={},
        )

        body = json.loads(result["body"])
        assert body["page"] == 1
        assert body["page_size"] == 20

    def test_page_less_than_1(self):
        from backend.handlers.admin_users import handle_list_users

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page": "0"},
        )

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Page must be >= 1" in body["error"]

    def test_page_size_too_large(self):
        from backend.handlers.admin_users import handle_list_users

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page_size": "101"},
        )

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Page size must be between 1 and 100" in body["error"]

    def test_page_size_zero(self):
        from backend.handlers.admin_users import handle_list_users

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page_size": "0"},
        )

        assert result["statusCode"] == 400

    def test_invalid_page_param(self):
        from backend.handlers.admin_users import handle_list_users

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page": "abc"},
        )

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid pagination parameters" in body["error"]

    def test_invalid_page_size_param(self):
        from backend.handlers.admin_users import handle_list_users

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page_size": "xyz"},
        )

        assert result["statusCode"] == 400

    @patch("backend.handlers.admin_users.get_all_registered_users")
    def test_second_page(self, mock_get_users):
        from backend.handlers.admin_users import handle_list_users

        mock_get_users.return_value = list(SAMPLE_USERS)

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={"page": "2", "page_size": "2"},
        )

        body = json.loads(result["body"])
        assert len(body["users"]) == 1
        assert body["page"] == 2

    @patch("backend.handlers.admin_users.get_all_registered_users")
    def test_empty_user_list(self, mock_get_users):
        from backend.handlers.admin_users import handle_list_users

        mock_get_users.return_value = []

        result = _bypass_admin(handle_list_users)(
            headers={},
            username="admin",
            user_id="admin_id",
            query_params={},
        )

        body = json.loads(result["body"])
        assert result["statusCode"] == 200
        assert body["users"] == []
        assert body["total_count"] == 0
        assert body["total_pages"] == 1


class TestHandleGetUserProfile:
    """Tests for handle_get_user_profile endpoint."""

    @patch("backend.handlers.admin_users.calculate_user_badges")
    @patch("backend.handlers.admin_users.get_user_progress")
    @patch("backend.handlers.admin_users.get_user_stats")
    @patch("backend.handlers.admin_users.get_user_profile")
    def test_returns_profile_with_stats_and_badges(
        self, mock_get_profile, mock_get_stats, mock_get_progress, mock_calc_badges
    ):
        from backend.handlers.admin_users import handle_get_user_profile

        mock_get_profile.return_value = {
            "user_id": "1",
            "username": "Alice",
            "github_username": "alice",
            "avatar_url": "https://example.com/alice.png",
            "registered_at": "2024-01-15T10:30:00Z",
            "last_login": "2024-03-25T08:00:00Z",
        }
        mock_get_stats.return_value = {
            "user_id": "1",
            "completed_count": 42,
            "overall_completion": 44,
            "quizzes_passed": 10,
            "walkthroughs_completed": 3,
            "capstone_submissions": 1,
            "current_streak": 5,
            "longest_streak": 12,
        }
        mock_get_progress.return_value = []
        mock_calc_badges.return_value = [
            {"id": "b1", "title": "First Steps", "icon": "🎯", "earned": True}
        ]

        result = _bypass_admin(handle_get_user_profile)(
            headers={},
            username="admin",
            user_id="admin_id",
            target_user_id="1",
        )

        body = json.loads(result["body"])
        assert result["statusCode"] == 200
        assert body["user"]["user_id"] == "1"
        assert body["stats"]["completed_count"] == 42
        assert body["stats"]["current_streak"] == 5
        assert len(body["badges"]) == 1

    @patch("backend.handlers.admin_users.get_user_profile")
    def test_returns_404_for_unknown_user(self, mock_get_profile):
        from backend.handlers.admin_users import handle_get_user_profile

        mock_get_profile.return_value = None

        result = _bypass_admin(handle_get_user_profile)(
            headers={},
            username="admin",
            user_id="admin_id",
            target_user_id="nonexistent",
        )

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "User not found" in body["error"]

    @patch("backend.handlers.admin_users.get_user_stats")
    @patch("backend.handlers.admin_users.get_user_profile")
    def test_graceful_stats_failure(self, mock_get_profile, mock_get_stats):
        from backend.handlers.admin_users import handle_get_user_profile

        mock_get_profile.return_value = {
            "user_id": "1",
            "username": "Alice",
            "github_username": "alice",
            "avatar_url": "",
            "registered_at": "2024-01-15T10:30:00Z",
            "last_login": "2024-03-25T08:00:00Z",
        }
        mock_get_stats.side_effect = Exception("DynamoDB error")

        result = _bypass_admin(handle_get_user_profile)(
            headers={},
            username="admin",
            user_id="admin_id",
            target_user_id="1",
        )

        body = json.loads(result["body"])
        assert result["statusCode"] == 200
        assert body["stats"]["completed_count"] == 0
        assert body["stats"]["overall_completion"] == 0
        assert body["stats"]["quizzes_passed"] == 0
        assert body["stats"]["walkthroughs_completed"] == 0
        assert body["stats"]["capstone_submissions"] == 0
        assert body["stats"]["current_streak"] == 0
        assert body["stats"]["longest_streak"] == 0
        assert body["badges"] == []

    def test_missing_target_user_id(self):
        from backend.handlers.admin_users import handle_get_user_profile

        result = _bypass_admin(handle_get_user_profile)(
            headers={},
            username="admin",
            user_id="admin_id",
            target_user_id="",
        )

        assert result["statusCode"] == 400
