"""
Unit tests for admin authentication utilities.

Tests the require_admin decorator and logging utilities.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.auth.admin import (
    require_admin,
    log_admin_access,
    is_admin,
    get_admin_users,
    ADMIN_USERS,
)
from jose import JWTError


class TestRequireAdminDecorator:
    """Test the require_admin decorator."""

    def test_missing_jwt_returns_401(self):
        """Test that missing JWT token returns 401 Unauthorized."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": "success"}

        # Headers without cookie
        headers = {}

        response = mock_handler(headers)

        assert response["statusCode"] == 401
        assert "Unauthorized" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_invalid_jwt_returns_401(self, mock_extract, mock_validate):
        """Test that invalid JWT token returns 401."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": "success"}

        # Mock token extraction
        mock_extract.return_value = "invalid_token"

        # Mock JWT validation to raise error
        mock_validate.side_effect = JWTError("Invalid signature")

        headers = {"cookie": "dsb_token=invalid_token"}
        response = mock_handler(headers)

        assert response["statusCode"] == 401
        assert "Invalid token" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_non_admin_user_returns_403(self, mock_extract, mock_validate):
        """Test that non-admin user receives 403 Forbidden."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": "success"}

        # Mock token extraction
        mock_extract.return_value = "valid_token"

        # Mock JWT validation with non-admin user
        mock_validate.return_value = {"sub": "github|12345678", "name": "regular_user"}

        headers = {"cookie": "dsb_token=valid_token"}
        response = mock_handler(headers)

        assert response["statusCode"] == 403
        assert "Forbidden" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_admin_user_succeeds(self, mock_extract, mock_validate):
        """Test that admin user can access endpoint."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": f"success for {username}"}

        # Mock token extraction
        mock_extract.return_value = "valid_token"

        # Mock JWT validation with admin user
        mock_validate.return_value = {"sub": "github|87654321", "name": "damienjburks"}

        headers = {"cookie": "dsb_token=valid_token"}
        response = mock_handler(headers)

        assert response["statusCode"] == 200
        assert "success for damienjburks" in response["body"]

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_admin_user_with_display_name(self, mock_extract, mock_validate):
        """Test that admin user with display name can access endpoint."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": f"success"}

        # Mock token extraction
        mock_extract.return_value = "valid_token"

        # Mock JWT validation with admin display name
        mock_validate.return_value = {"sub": "github|87654321", "name": "Damien Burks"}

        headers = {"cookie": "dsb_token=valid_token"}
        response = mock_handler(headers)

        assert response["statusCode"] == 200

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    def test_handler_receives_username_and_user_id(self, mock_extract, mock_validate):
        """Test that handler receives username and user_id parameters."""
        received_params = {}

        @require_admin
        def mock_handler(headers, username, user_id):
            received_params["username"] = username
            received_params["user_id"] = user_id
            return {"statusCode": 200, "body": "success"}

        # Mock token extraction
        mock_extract.return_value = "valid_token"

        # Mock JWT validation
        mock_validate.return_value = {"sub": "github|87654321", "name": "damienjburks"}

        headers = {"cookie": "dsb_token=valid_token"}
        mock_handler(headers)

        assert received_params["username"] == "damienjburks"
        assert received_params["user_id"] == "github|87654321"

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    @patch("backend.auth.admin.log_admin_access")
    def test_logs_all_access_attempts(self, mock_log, mock_extract, mock_validate):
        """Test that all access attempts are logged."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": "success"}

        # Test successful access
        mock_extract.return_value = "valid_token"
        mock_validate.return_value = {"sub": "github|87654321", "name": "damienjburks"}

        headers = {"cookie": "dsb_token=valid_token"}
        mock_handler(headers)

        # Verify logging was called
        assert mock_log.called
        call_args = mock_log.call_args[1]
        assert call_args["success"] is True
        assert call_args["username"] == "damienjburks"

    @patch("backend.auth.admin.validate_jwt")
    @patch("backend.auth.admin.extract_token_from_cookie")
    @patch("backend.auth.admin.log_admin_access")
    def test_logs_failed_attempts(self, mock_log, mock_extract, mock_validate):
        """Test that failed access attempts are logged."""

        @require_admin
        def mock_handler(headers, username, user_id):
            return {"statusCode": 200, "body": "success"}

        # Test missing token
        mock_extract.return_value = None

        headers = {}
        mock_handler(headers)

        # Verify logging was called with failure
        assert mock_log.called
        call_args = mock_log.call_args[1]
        assert call_args["success"] is False
        assert "Missing JWT token" in call_args["reason"]


class TestLogAdminAccess:
    """Test the log_admin_access function."""

    @patch("backend.auth.admin.logger")
    def test_logs_successful_access(self, mock_logger):
        """Test logging of successful admin access."""
        log_admin_access(
            endpoint="handle_test",
            username="damienjburks",
            user_id="github|12345",
            success=True,
        )

        # Verify info log was called
        assert mock_logger.info.called
        # Check the first info call (not the structured log)
        log_message = mock_logger.info.call_args_list[0][0][0]
        assert "Admin access" in log_message
        assert "handle_test" in log_message
        assert "damienjburks" in log_message

    @patch("backend.auth.admin.logger")
    def test_logs_failed_access(self, mock_logger):
        """Test logging of failed admin access."""
        log_admin_access(
            endpoint="handle_test",
            username="regular_user",
            user_id="github|99999",
            success=False,
            reason="User not in ADMIN_USERS list",
        )

        # Verify warning log was called
        assert mock_logger.warning.called
        log_message = mock_logger.warning.call_args[0][0]
        assert "Admin access denied" in log_message
        assert "User not in ADMIN_USERS list" in log_message

    @patch("backend.auth.admin.logger")
    def test_logs_structured_data(self, mock_logger):
        """Test that structured log data is created."""
        log_admin_access(
            endpoint="handle_test",
            username="damienjburks",
            user_id="github|12345",
            success=True,
        )

        # Check that structured log was created
        calls = [str(call) for call in mock_logger.info.call_args_list]
        structured_log = [call for call in calls if "ADMIN_ACCESS_LOG" in call]
        assert len(structured_log) > 0


class TestIsAdmin:
    """Test the is_admin helper function."""

    def test_returns_true_for_admin_username(self):
        """Test that admin username returns True."""
        assert is_admin("damienjburks") is True

    def test_returns_true_for_admin_display_name(self):
        """Test that admin display name returns True."""
        assert is_admin("Damien Burks") is True

    def test_returns_false_for_non_admin(self):
        """Test that non-admin username returns False."""
        assert is_admin("regular_user") is False

    def test_returns_false_for_none(self):
        """Test that None returns False."""
        assert is_admin(None) is False

    def test_returns_false_for_empty_string(self):
        """Test that empty string returns False."""
        assert is_admin("") is False


class TestGetAdminUsers:
    """Test the get_admin_users helper function."""

    def test_returns_list_of_admins(self):
        """Test that function returns list of admin usernames."""
        admins = get_admin_users()
        assert isinstance(admins, list)
        assert "damienjburks" in admins
        assert "Damien Burks" in admins

    def test_returns_copy_not_reference(self):
        """Test that function returns a copy, not reference to ADMIN_USERS."""
        admins = get_admin_users()
        admins.append("test_user")

        # Original ADMIN_USERS should not be modified
        assert "test_user" not in ADMIN_USERS
