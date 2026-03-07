"""
Unit tests for auth/jwt_utils.py JWT utilities.
"""

import os
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError

from backend.auth.jwt_utils import generate_jwt, validate_jwt, extract_token_from_cookie


@pytest.fixture
def mock_jwt_secret():
    """Mock JWT secret from Secrets Manager."""
    return {"secret_key": "test-secret-key-12345"}


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {"JWT_SECRET_NAME": "test-jwt-secret"}):
        yield


class TestGenerateJWT:
    """Test JWT generation."""

    def test_generates_valid_jwt(self, mock_env_vars, mock_jwt_secret):
        """Should generate a valid JWT token."""
        user_id = "12345678"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            token = generate_jwt(user_id)

            # Verify token is a string
            assert isinstance(token, str)
            assert len(token) > 0

            # Decode without verification to check structure
            decoded = jwt.decode(
                token, mock_jwt_secret["secret_key"], algorithms=["HS256"]
            )
            assert decoded["sub"] == user_id
            assert "exp" in decoded

    def test_jwt_uses_hs256_algorithm(self, mock_env_vars, mock_jwt_secret):
        """Should use HS256 algorithm."""
        user_id = "12345678"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            token = generate_jwt(user_id)

            # Decode header to check algorithm
            header = jwt.get_unverified_header(token)
            assert header["alg"] == "HS256"

    def test_jwt_expires_in_one_hour(self, mock_env_vars, mock_jwt_secret):
        """Should set expiration to 1 hour from creation."""
        user_id = "12345678"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            before = datetime.now(timezone.utc)
            token = generate_jwt(user_id)
            after = datetime.now(timezone.utc)

            decoded = jwt.decode(
                token, mock_jwt_secret["secret_key"], algorithms=["HS256"]
            )
            exp_timestamp = decoded["exp"]
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

            # Expiration should be approximately 1 hour from now (within 5 seconds tolerance)
            expected_exp = before + timedelta(hours=1)
            time_diff = abs((exp_datetime - expected_exp).total_seconds())
            assert time_diff < 5

    def test_jwt_includes_user_id_in_sub_claim(self, mock_env_vars, mock_jwt_secret):
        """Should include user ID in sub claim."""
        user_id = "87654321"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            token = generate_jwt(user_id)

            decoded = jwt.decode(
                token, mock_jwt_secret["secret_key"], algorithms=["HS256"]
            )
            assert decoded["sub"] == user_id

    def test_raises_error_when_env_var_missing(self, mock_jwt_secret):
        """Should raise error when JWT_SECRET_NAME not set."""
        user_id = "12345678"

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                generate_jwt(user_id)

            assert "JWT_SECRET_NAME" in str(exc_info.value)

    def test_raises_error_when_secret_key_missing(self, mock_env_vars):
        """Should raise error when secret_key not in secret."""
        user_id = "12345678"
        invalid_secret = {"other_key": "value"}

        with patch("backend.auth.jwt_utils.get_secret", return_value=invalid_secret):
            with pytest.raises(Exception) as exc_info:
                generate_jwt(user_id)

            assert "secret_key not found" in str(exc_info.value)

    def test_generates_different_tokens_for_different_users(
        self, mock_env_vars, mock_jwt_secret
    ):
        """Should generate different tokens for different user IDs."""
        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            token1 = generate_jwt("user1")
            token2 = generate_jwt("user2")

            assert token1 != token2

            decoded1 = jwt.decode(
                token1, mock_jwt_secret["secret_key"], algorithms=["HS256"]
            )
            decoded2 = jwt.decode(
                token2, mock_jwt_secret["secret_key"], algorithms=["HS256"]
            )

            assert decoded1["sub"] == "user1"
            assert decoded2["sub"] == "user2"


class TestValidateJWT:
    """Test JWT validation."""

    def test_validates_valid_jwt(self, mock_env_vars, mock_jwt_secret):
        """Should successfully validate a valid JWT."""
        user_id = "12345678"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            # Generate a token
            token = generate_jwt(user_id)

            # Validate it
            payload = validate_jwt(token)

            assert payload["sub"] == user_id
            assert "exp" in payload

    def test_rejects_expired_jwt(self, mock_env_vars, mock_jwt_secret):
        """Should reject expired JWT."""
        user_id = "12345678"

        # Create an expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {"sub": user_id, "exp": past_time}
        expired_token = jwt.encode(
            payload, mock_jwt_secret["secret_key"], algorithm="HS256"
        )

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            with pytest.raises(JWTError):
                validate_jwt(expired_token)

    def test_rejects_invalid_signature(self, mock_env_vars, mock_jwt_secret):
        """Should reject JWT with invalid signature."""
        user_id = "12345678"
        wrong_secret = {"secret_key": "wrong-secret-key"}

        # Create token with wrong secret
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            with pytest.raises(JWTError):
                validate_jwt(token)

    def test_rejects_malformed_token(self, mock_env_vars, mock_jwt_secret):
        """Should reject malformed JWT."""
        malformed_token = "not.a.valid.jwt.token"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            with pytest.raises(JWTError):
                validate_jwt(malformed_token)

    def test_raises_error_when_env_var_missing(self, mock_jwt_secret):
        """Should raise error when JWT_SECRET_NAME not set."""
        token = "some.jwt.token"

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                validate_jwt(token)

            assert "JWT_SECRET_NAME" in str(exc_info.value)

    def test_raises_error_when_secret_key_missing(self, mock_env_vars):
        """Should raise error when secret_key not in secret."""
        token = "some.jwt.token"
        invalid_secret = {"other_key": "value"}

        with patch("backend.auth.jwt_utils.get_secret", return_value=invalid_secret):
            with pytest.raises(Exception) as exc_info:
                validate_jwt(token)

            assert "secret_key not found" in str(exc_info.value)

    def test_round_trip_validation(self, mock_env_vars, mock_jwt_secret):
        """Should successfully round-trip: generate -> validate -> extract user_id."""
        user_id = "87654321"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            # Generate token
            token = generate_jwt(user_id)

            # Validate token
            payload = validate_jwt(token)

            # Extract user_id
            extracted_user_id = payload["sub"]

            assert extracted_user_id == user_id


class TestExtractTokenFromCookie:
    """Test cookie token extraction."""

    def test_extracts_token_from_single_cookie(self):
        """Should extract token from cookie header with single cookie."""
        headers = {"cookie": "dsb_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}

        token = extract_token_from_cookie(headers)

        assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

    def test_extracts_token_from_multiple_cookies(self):
        """Should extract dsb_token from multiple cookies."""
        headers = {"cookie": "session_id=abc123; dsb_token=jwt_token_here; other=value"}

        token = extract_token_from_cookie(headers)

        assert token == "jwt_token_here"

    def test_returns_none_when_cookie_missing(self):
        """Should return None when cookie header is missing."""
        headers = {}

        token = extract_token_from_cookie(headers)

        assert token is None

    def test_returns_none_when_dsb_token_not_present(self):
        """Should return None when dsb_token cookie is not present."""
        headers = {"cookie": "session_id=abc123; other=value"}

        token = extract_token_from_cookie(headers)

        assert token is None

    def test_handles_empty_cookie_header(self):
        """Should handle empty cookie header."""
        headers = {"cookie": ""}

        token = extract_token_from_cookie(headers)

        assert token is None

    def test_handles_cookie_with_spaces(self):
        """Should handle cookies with spaces around separators."""
        headers = {"cookie": "session_id=abc123 ;  dsb_token=jwt_value ; other=test"}

        token = extract_token_from_cookie(headers)

        assert token == "jwt_value"

    def test_extracts_full_jwt_token(self):
        """Should extract complete JWT token with dots and special characters."""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        headers = {"cookie": f"dsb_token={jwt_token}"}

        token = extract_token_from_cookie(headers)

        assert token == jwt_token

    def test_handles_lowercase_header_keys(self):
        """Should work with lowercase header keys (API Gateway format)."""
        headers = {"cookie": "dsb_token=test_token"}

        token = extract_token_from_cookie(headers)

        assert token == "test_token"

    def test_handles_cookie_without_equals(self):
        """Should handle malformed cookies gracefully."""
        headers = {"cookie": "malformed_cookie; dsb_token=valid_token"}

        token = extract_token_from_cookie(headers)

        assert token == "valid_token"


class TestVerifyUser:
    """Test /me endpoint handler (verify_user function)."""

    def test_returns_user_info_with_valid_jwt(self, mock_env_vars, mock_jwt_secret):
        """Should return user_id and authenticated=true with valid JWT."""
        from backend.auth.jwt_utils import verify_user

        user_id = "12345678"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            # Generate a valid token
            token = generate_jwt(user_id)

            # Create headers with the token
            headers = {"cookie": f"dsb_token={token}"}

            # Call verify_user
            response = verify_user(headers)

            # Verify response structure
            assert response["statusCode"] == 200
            assert "headers" in response
            assert response["headers"]["Content-Type"] == "application/json"
            assert "Access-Control-Allow-Origin" in response["headers"]

            # Verify response body
            body = json.loads(response["body"])
            assert body["user_id"] == user_id
            assert body["authenticated"] is True

    def test_returns_401_when_cookie_missing(self):
        """Should return 401 when dsb_token cookie is missing."""
        from backend.auth.jwt_utils import verify_user

        headers = {}

        response = verify_user(headers)

        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body
        assert body["error"] == "Authentication failed"

    def test_returns_401_when_jwt_invalid(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT signature is invalid."""
        from backend.auth.jwt_utils import verify_user

        # Create an invalid token
        headers = {"cookie": "dsb_token=invalid.jwt.token"}

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            response = verify_user(headers)

            assert response["statusCode"] == 401
            body = json.loads(response["body"])
            assert "error" in body
            assert body["error"] == "Authentication failed"

    def test_returns_401_when_jwt_expired(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT is expired."""
        from backend.auth.jwt_utils import verify_user

        user_id = "12345678"

        # Create an expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {"sub": user_id, "exp": past_time}
        expired_token = jwt.encode(
            payload, mock_jwt_secret["secret_key"], algorithm="HS256"
        )

        headers = {"cookie": f"dsb_token={expired_token}"}

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            response = verify_user(headers)

            assert response["statusCode"] == 401
            body = json.loads(response["body"])
            assert "error" in body

    def test_returns_401_when_sub_claim_missing(self, mock_env_vars, mock_jwt_secret):
        """Should return 401 when JWT doesn't have sub claim."""
        from backend.auth.jwt_utils import verify_user

        # Create a token without sub claim
        payload = {"exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, mock_jwt_secret["secret_key"], algorithm="HS256")

        headers = {"cookie": f"dsb_token={token}"}

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            response = verify_user(headers)

            assert response["statusCode"] == 401
            body = json.loads(response["body"])
            assert "error" in body

    def test_response_includes_cors_headers(self, mock_env_vars, mock_jwt_secret):
        """Should include CORS headers in response."""
        from backend.auth.jwt_utils import verify_user

        user_id = "12345678"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            token = generate_jwt(user_id)
            headers = {"cookie": f"dsb_token={token}"}

            response = verify_user(headers)

            assert "Access-Control-Allow-Origin" in response["headers"]
            assert (
                response["headers"]["Access-Control-Allow-Origin"]
                == "https://devsecblueprint.com"
            )
            assert "Access-Control-Allow-Credentials" in response["headers"]
            assert response["headers"]["Access-Control-Allow-Credentials"] == "true"

    def test_does_not_expose_sensitive_info_in_errors(self, mock_env_vars):
        """Should not expose stack traces or sensitive information in error responses."""
        from backend.auth.jwt_utils import verify_user

        # Simulate an unexpected error by making get_secret fail
        headers = {"cookie": "dsb_token=some.token.here"}

        with patch(
            "backend.auth.jwt_utils.get_secret",
            side_effect=Exception("Internal AWS error"),
        ):
            response = verify_user(headers)

            # Should return 401 with generic message
            assert response["statusCode"] == 401
            body = json.loads(response["body"])
            assert body["error"] == "Authentication failed"

            # Should not contain internal error details
            assert "AWS" not in body["error"]
            assert "Internal" not in body["error"]

    def test_handles_multiple_cookies(self, mock_env_vars, mock_jwt_secret):
        """Should extract JWT from multiple cookies correctly."""
        from backend.auth.jwt_utils import verify_user

        user_id = "87654321"

        with patch("backend.auth.jwt_utils.get_secret", return_value=mock_jwt_secret):
            token = generate_jwt(user_id)
            headers = {"cookie": f"session=abc123; dsb_token={token}; other=value"}

            response = verify_user(headers)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["user_id"] == user_id
            assert body["authenticated"] is True
