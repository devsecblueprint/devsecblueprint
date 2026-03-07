"""
Property-based tests for JWT utilities.

Feature: backend-phase1
"""

import os
import time
from unittest.mock import patch
from hypothesis import given, strategies as st, settings
from jose import jwt as jose_jwt
from backend.auth.jwt_utils import generate_jwt, validate_jwt

# Strategy for generating valid user IDs (GitHub user IDs are numeric strings)
user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Nd",)),  # Numeric digits
    min_size=1,
    max_size=20,
).filter(lambda x: x.strip() != "")


class TestJWTProperties:
    """Property-based tests for JWT generation and validation."""

    @settings(max_examples=100)
    @given(user_id=user_id_strategy)
    @patch.dict(os.environ, {"JWT_SECRET_NAME": "test-jwt-secret"})
    @patch("backend.auth.jwt_utils.get_secret")
    def test_property_3_jwt_generation_and_structure(self, mock_get_secret, user_id):
        """
        Property 3: JWT Generation and Structure

        For any GitHub user ID, when generating a JWT token, the token should:
        - Use HS256 algorithm (verifiable from JWT header)
        - Have an expiration time approximately 1 hour (3600 seconds ±5 seconds) from creation
        - Include the user ID in the "sub" claim
        - Be verifiable with the JWT secret
        - Decode to a valid payload structure

        **Validates: Requirements 2.4, 11.1, 11.2, 11.3**
        """
        # Mock the secret
        mock_get_secret.return_value = {
            "secret_key": "test-secret-key-min-32-characters-long"
        }

        # Record time before generation
        time_before = time.time()

        # Generate JWT
        token = generate_jwt(user_id)

        # Record time after generation
        time_after = time.time()

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode without verification to check structure
        unverified_header = jose_jwt.get_unverified_header(token)
        unverified_claims = jose_jwt.get_unverified_claims(token)

        # Property: Uses HS256 algorithm
        assert (
            unverified_header["alg"] == "HS256"
        ), f"Expected HS256 algorithm, got {unverified_header['alg']}"

        # Property: Includes user ID in sub claim
        assert "sub" in unverified_claims, "Token missing 'sub' claim"
        assert (
            unverified_claims["sub"] == user_id
        ), f"Expected sub={user_id}, got {unverified_claims['sub']}"

        # Property: Has expiration claim
        assert "exp" in unverified_claims, "Token missing 'exp' claim"

        # Property: Expiration is approximately 1 hour (3600 seconds ±5 seconds) from creation
        expected_exp_min = time_before + 3595  # 3600 - 5
        expected_exp_max = time_after + 3605  # 3600 + 5
        actual_exp = unverified_claims["exp"]
        assert (
            expected_exp_min <= actual_exp <= expected_exp_max
        ), f"Expected exp between {expected_exp_min} and {expected_exp_max}, got {actual_exp}"

        # Property: Token is verifiable with the JWT secret
        try:
            decoded = jose_jwt.decode(
                token, "test-secret-key-min-32-characters-long", algorithms=["HS256"]
            )
            assert decoded["sub"] == user_id
        except Exception as e:
            raise AssertionError(f"Token verification failed: {e}")

    @settings(max_examples=100)
    @given(user_id=user_id_strategy)
    @patch.dict(os.environ, {"JWT_SECRET_NAME": "test-jwt-secret"})
    @patch("backend.auth.jwt_utils.get_secret")
    def test_property_4_jwt_round_trip_validation(self, mock_get_secret, user_id):
        """
        Property 4: JWT Round-Trip Validation

        For any valid user ID, generating a JWT and then validating it should:
        - Successfully extract the original user ID from the validated payload
        - Not raise any validation exceptions
        - Return a payload with matching "sub" claim

        This is a round-trip property: generate(user_id) → validate(token) → extract(user_id)
        should preserve the user ID.

        **Validates: Requirements 3.2, 11.4, 11.5**
        """
        # Mock the secret
        mock_get_secret.return_value = {
            "secret_key": "test-secret-key-min-32-characters-long"
        }

        # Generate JWT
        token = generate_jwt(user_id)

        # Validate JWT (should not raise exception)
        try:
            payload = validate_jwt(token)
        except Exception as e:
            raise AssertionError(f"Round-trip validation failed: {e}")

        # Property: Payload contains the original user ID
        assert "sub" in payload, "Validated payload missing 'sub' claim"
        assert (
            payload["sub"] == user_id
        ), f"Round-trip failed: expected user_id={user_id}, got {payload['sub']}"

        # Property: Payload structure is valid
        assert isinstance(payload, dict), "Payload should be a dictionary"
        assert "exp" in payload, "Validated payload missing 'exp' claim"
