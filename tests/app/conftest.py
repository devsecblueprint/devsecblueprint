"""
Pytest conftest for tests/app/ — sets required environment variables
before any app modules are imported.

The Settings model (pydantic-settings) requires these env vars at import time
because app.main triggers setup_cors() → get_settings() at module level.
"""

import os

import pytest

# Set all required environment variables for pydantic Settings before
# any app module imports happen during collection.
_TEST_ENV = {
    "MEMBERSHIP_TABLE": "test-membership",
    "PROGRESS_TABLE": "test-progress",
    "USER_STATE_TABLE": "test-user-state",
    "TESTIMONIALS_TABLE": "test-testimonials",
    "NOTIFICATIONS_TABLE": "test-notifications",
    "DISCORD_SECRET_NAME": "test-discord",
    "DISCORD_BOT_SECRET_NAME": "test-discord-bot",
    "STRIPE_SECRET_NAME": "test-stripe",
    "STRIPE_WEBHOOK_SECRET_NAME": "test-stripe-webhook",
    "JWT_SECRET_NAME": "test-jwt-secret",
    "GITHUB_SECRET_NAME": "test-github",
    "GITLAB_SECRET_NAME": "test-gitlab",
    "BITBUCKET_SECRET_NAME": "test-bitbucket",
    "DISCORD_GUILD_ID": "123456",
    "DISCORD_ROLE_FREE_ID": "111",
    "DISCORD_ROLE_EXPLORER_ID": "222",
    "DISCORD_ROLE_BUILDER_ID": "333",
    "DISCORD_ROLE_BUILDER_ACADEMY_ID": "444",
    "DISCORD_CALLBACK_URL": "https://example.com/callback",
    "FRONTEND_URL": "https://example.com",
    "FRONTEND_ORIGIN": "https://example.com",
    "GITHUB_CALLBACK_URL": "https://example.com/auth/github/callback",
    "GITLAB_CALLBACK_URL": "https://example.com/auth/gitlab/callback",
    "BITBUCKET_CALLBACK_URL": "https://example.com/auth/bitbucket/callback",
}

for key, value in _TEST_ENV.items():
    os.environ.setdefault(key, value)


@pytest.fixture(autouse=True)
def mock_jwt_secret():
    """Override the root conftest mock_jwt_secret to be a no-op for tests/app/.

    These tests manage their own boto3 mocks more granularly.
    """
    yield
