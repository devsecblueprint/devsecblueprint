"""Application configuration using Pydantic Settings.

Loads environment variables from the ECS task definition or a local .env file.
Combines all variables from both Lambda functions (dsb-platform-api and
dsb-platform-membership) into a single Settings class.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration for the DSB Platform API.

    All fields map to environment variables injected by the ECS task definition
    or provided via a .env file during local development.
    """

    # DynamoDB Tables
    membership_table: str
    progress_table: str
    user_state_table: str
    testimonials_table: str
    notifications_table: str
    broadcasts_table: str = ""

    # Secrets Manager secret names
    discord_secret_name: str
    discord_bot_secret_name: str
    stripe_secret_name: str
    stripe_webhook_secret_name: str
    jwt_secret_name: str
    github_secret_name: str
    gitlab_secret_name: str
    bitbucket_secret_name: str

    # Discord configuration
    discord_guild_id: str
    discord_role_free_id: str
    discord_role_explorer_id: str
    discord_role_builder_id: str
    discord_role_builder_academy_id: str
    discord_callback_url: str

    # OAuth callback URLs
    frontend_url: str
    frontend_origin: str
    github_callback_url: str
    gitlab_callback_url: str
    bitbucket_callback_url: str

    # Application settings with defaults
    admin_users: str = ""
    content_registry_bucket: str = ""
    total_module_pages: int = 0
    session_token_lifetime_hours: int = 8
    ses_sender_email: str = "noreply@devsecblueprint.com"
    ses_region: str = "us-east-2"
    testimonial_notify_email: str = "info@devsecblueprint.com"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Create and return a Settings instance.

    This is used as a FastAPI dependency so settings can be injected
    and overridden in tests.
    """
    return Settings()
