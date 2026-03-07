"""
Property-based tests for OAuth functionality.

Feature: backend-phase1
"""

import os
from urllib.parse import urlparse, parse_qs
from unittest.mock import patch
from hypothesis import given, strategies as st, settings

# Strategies for OAuth parameters
client_id_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # Printable ASCII
    min_size=1,
    max_size=100,
).filter(
    lambda x: "&" not in x and "=" not in x
)  # Avoid URL-breaking characters

callback_url_strategy = st.from_regex(
    r"https://[a-z0-9\-\.]+\.[a-z]{2,}/[a-z0-9\-/]*", fullmatch=True
)


class TestOAuthProperties:
    """Property-based tests for OAuth URL construction."""

    @settings(max_examples=100)
    @given(client_id=client_id_strategy, callback_url=callback_url_strategy)
    def test_property_1_oauth_url_construction(self, client_id, callback_url):
        """
        Property 1: OAuth URL Construction

        For any valid GitHub client ID and callback URL, when constructing the OAuth
        authorization URL, the resulting URL should:
        - Point to GitHub's authorize endpoint (https://github.com/login/oauth/authorize)
        - Include client_id parameter matching the provided client ID
        - Include redirect_uri parameter matching the provided callback URL
        - Include scope parameter set to "read:user"
        - Be properly URL-encoded

        **Validates: Requirements 1.1, 1.3**
        """
        from backend.auth.github import start_oauth

        # Set environment variables and mock get_secret
        with (
            patch.dict(
                os.environ,
                {
                    "GITHUB_SECRET_NAME": "test-github-secret",
                    "GITHUB_CALLBACK_URL": callback_url,
                    "FRONTEND_ORIGIN": "https://devsecblueprint.com",
                },
            ),
            patch("backend.auth.github.get_secret") as mock_get_secret,
        ):
            # Mock the secret retrieval
            mock_get_secret.return_value = {"client_id": client_id}

            # Call start_oauth
            response = start_oauth()

            # Verify response structure
            assert response["statusCode"] == 302, "Should return 302 redirect"
            assert "headers" in response, "Response should have headers"
            assert (
                "Location" in response["headers"]
            ), "Response should have Location header"

            # Extract the authorization URL
            auth_url = response["headers"]["Location"]

            # Property: Points to GitHub's authorize endpoint
            parsed_url = urlparse(auth_url)
            assert parsed_url.scheme == "https", "URL should use HTTPS"
            assert parsed_url.netloc == "github.com", "URL should point to github.com"
            assert (
                parsed_url.path == "/login/oauth/authorize"
            ), f"URL path should be /login/oauth/authorize, got {parsed_url.path}"

            # Parse query parameters
            query_params = parse_qs(parsed_url.query)

            # Property: Includes client_id parameter matching the provided client ID
            assert "client_id" in query_params, "URL should include client_id parameter"
            assert (
                query_params["client_id"][0] == client_id
            ), f"client_id should be {client_id}, got {query_params['client_id'][0]}"

            # Property: Includes redirect_uri parameter matching the provided callback URL
            assert (
                "redirect_uri" in query_params
            ), "URL should include redirect_uri parameter"
            assert (
                query_params["redirect_uri"][0] == callback_url
            ), f"redirect_uri should be {callback_url}, got {query_params['redirect_uri'][0]}"

            # Property: Includes scope parameter set to "read:user"
            assert "scope" in query_params, "URL should include scope parameter"
            assert (
                query_params["scope"][0] == "read:user"
            ), f"scope should be 'read:user', got {query_params['scope'][0]}"
