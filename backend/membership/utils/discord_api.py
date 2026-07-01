"""
Discord REST API client with rate limiting and exponential backoff.

Provides a DiscordClient class for interacting with the Discord API v10,
including member management, role operations, and guild membership.
All requests use bot token authentication and include rate limit handling.
"""

import time
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class DiscordClient:
    """
    Discord API v10 client with rate limiting and retry logic.

    Uses bot token authentication for all requests. Handles:
    - Rate limiting via X-RateLimit-Remaining and X-RateLimit-Reset-After headers
    - Exponential backoff on 5xx errors (1s base, 2x multiplier, max 60s, max 5 retries)
    - 429 Too Many Requests with Retry-After header
    - 404 responses treated as "user not in guild" (graceful handling)
    - 10-second timeout on all API calls

    Validates: Requirements 8.1-8.3, 11.3-11.6, 18.3, 18.6
    """

    BASE_URL = "https://discord.com/api/v10"
    TIMEOUT = 10  # seconds
    MAX_RETRIES = 5
    BASE_BACKOFF = 1  # seconds
    MAX_BACKOFF = 60  # seconds

    def __init__(self, bot_token: str, guild_id: str):
        """
        Initialize the Discord API client.

        Args:
            bot_token: Discord bot token for Authorization header
            guild_id: Discord guild (server) ID for all guild operations
        """
        self.bot_token = bot_token
        self.guild_id = guild_id
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json",
            }
        )

    def get_member(self, user_id: str) -> Optional[dict]:
        """
        Get a guild member by user ID.

        GET /guilds/{guild_id}/members/{user_id}

        Args:
            user_id: Discord user ID

        Returns:
            dict: Member object from Discord API, or None if user is not in guild (404)

        Validates: Requirements 11.1, 11.3
        """
        path = f"/guilds/{self.guild_id}/members/{user_id}"
        response = self._request("GET", path)

        if response is None:
            return None

        if response.status_code == 404:
            logger.debug("User %s not found in guild %s", user_id, self.guild_id)
            return None

        if response.status_code == 200:
            return response.json()

        logger.error(
            "Unexpected status %d getting member %s",
            response.status_code,
            user_id,
        )
        return None

    def add_member_to_guild(self, user_id: str, access_token: str) -> bool:
        """
        Add a user to the guild using their OAuth2 access token.

        PUT /guilds/{guild_id}/members/{user_id}
        Body: {"access_token": access_token}

        Requires the guilds.join OAuth2 scope on the access token.

        Args:
            user_id: Discord user ID to add
            access_token: User's OAuth2 access token with guilds.join scope

        Returns:
            bool: True if user was added (201) or already a member (204),
                  False on failure

        Validates: Requirements 8.1-8.3
        """
        path = f"/guilds/{self.guild_id}/members/{user_id}"
        response = self._request("PUT", path, json={"access_token": access_token})

        if response is None:
            return False

        if response.status_code in (201, 204):
            logger.info(
                "User %s added to guild %s (status=%d)",
                user_id,
                self.guild_id,
                response.status_code,
            )
            return True

        logger.error(
            "Failed to add user %s to guild: status=%d",
            user_id,
            response.status_code,
        )
        return False

    def get_member_roles(self, user_id: str) -> Optional[list]:
        """
        Get the list of role IDs for a guild member.

        Calls get_member() and extracts the "roles" field.

        Args:
            user_id: Discord user ID

        Returns:
            list[str]: List of role ID strings, or None if user is not in guild

        Validates: Requirements 11.3
        """
        member = self.get_member(user_id)
        if member is None:
            return None
        return member.get("roles", [])

    def add_role(self, user_id: str, role_id: str) -> bool:
        """
        Add a role to a guild member.

        PUT /guilds/{guild_id}/members/{user_id}/roles/{role_id}

        Args:
            user_id: Discord user ID
            role_id: Discord role ID to add

        Returns:
            bool: True on success (204), False on failure

        Validates: Requirements 11.4
        """
        path = f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}"
        response = self._request("PUT", path)

        if response is None:
            return False

        if response.status_code == 204:
            logger.info(
                "Added role %s to user %s in guild %s",
                role_id,
                user_id,
                self.guild_id,
            )
            return True

        if response.status_code == 404:
            logger.warning(
                "Cannot add role %s to user %s: user not in guild",
                role_id,
                user_id,
            )
            return False

        logger.error(
            "Failed to add role %s to user %s: status=%d",
            role_id,
            user_id,
            response.status_code,
        )
        return False

    def remove_role(self, user_id: str, role_id: str) -> bool:
        """
        Remove a role from a guild member.

        DELETE /guilds/{guild_id}/members/{user_id}/roles/{role_id}

        Args:
            user_id: Discord user ID
            role_id: Discord role ID to remove

        Returns:
            bool: True on success (204), False on failure

        Validates: Requirements 11.5
        """
        path = f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}"
        response = self._request("DELETE", path)

        if response is None:
            return False

        if response.status_code == 204:
            logger.info(
                "Removed role %s from user %s in guild %s",
                role_id,
                user_id,
                self.guild_id,
            )
            return True

        if response.status_code == 404:
            logger.warning(
                "Cannot remove role %s from user %s: user not in guild",
                role_id,
                user_id,
            )
            return False

        logger.error(
            "Failed to remove role %s from user %s: status=%d",
            role_id,
            user_id,
            response.status_code,
        )
        return False

    def _request(self, method: str, path: str, **kwargs) -> Optional[requests.Response]:
        """
        Internal method to make Discord API requests with rate limiting and retries.

        Handles:
        - 10-second timeout on all requests
        - Rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset-After)
        - 429 responses: sleep for Retry-After duration, then retry
        - 5xx errors: exponential backoff (1s, 2s, 4s, 8s, 16s capped at 60s)
        - 404: return response for caller to handle
        - Other 4xx: log and return None

        Args:
            method: HTTP method (GET, PUT, DELETE)
            path: API path (appended to BASE_URL)
            **kwargs: Additional arguments passed to requests (e.g., json=)

        Returns:
            requests.Response on success or 404, None on unrecoverable failure
        """
        url = f"{self.BASE_URL}{path}"
        kwargs.setdefault("timeout", self.TIMEOUT)

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(
                    "Discord API %s %s (attempt %d/%d)",
                    method,
                    path,
                    attempt + 1,
                    self.MAX_RETRIES,
                )

                response = self._session.request(method, url, **kwargs)

                # Handle rate limit headers proactively
                self._handle_rate_limit(response)

                # 429 Too Many Requests — respect Retry-After
                if response.status_code == 429:
                    retry_after = self._get_retry_after(response)
                    logger.warning(
                        "Rate limited on %s %s, retrying after %.2fs",
                        method,
                        path,
                        retry_after,
                    )
                    time.sleep(retry_after)
                    continue

                # 5xx Server Error — exponential backoff
                if response.status_code >= 500:
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        "Discord server error %d on %s %s, backing off %.2fs "
                        "(attempt %d/%d)",
                        response.status_code,
                        method,
                        path,
                        backoff,
                        attempt + 1,
                        self.MAX_RETRIES,
                    )
                    time.sleep(backoff)
                    continue

                # 404 — return to caller for graceful handling
                if response.status_code == 404:
                    return response

                # 2xx — success
                if 200 <= response.status_code < 300:
                    return response

                # Other 4xx — client error, not retryable
                logger.error(
                    "Discord API error %d on %s %s: %s",
                    response.status_code,
                    method,
                    path,
                    response.text[:500],
                )
                return None

            except requests.exceptions.Timeout:
                backoff = self._calculate_backoff(attempt)
                logger.warning(
                    "Discord API timeout on %s %s (attempt %d/%d), "
                    "backing off %.2fs",
                    method,
                    path,
                    attempt + 1,
                    self.MAX_RETRIES,
                    backoff,
                )
                time.sleep(backoff)
                continue

            except requests.exceptions.RequestException as exc:
                backoff = self._calculate_backoff(attempt)
                logger.error(
                    "Discord API request error on %s %s (attempt %d/%d): %s",
                    method,
                    path,
                    attempt + 1,
                    self.MAX_RETRIES,
                    str(exc),
                )
                time.sleep(backoff)
                continue

        logger.error(
            "Discord API %s %s failed after %d retries",
            method,
            path,
            self.MAX_RETRIES,
        )
        return None

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """
        Check rate limit headers and sleep if bucket is exhausted.

        Reads X-RateLimit-Remaining and X-RateLimit-Reset-After headers.
        If remaining requests are 0, proactively sleeps until the bucket resets.

        Args:
            response: The HTTP response to inspect for rate limit headers
        """
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_after = response.headers.get("X-RateLimit-Reset-After")

        if remaining is not None and int(remaining) == 0 and reset_after:
            sleep_time = float(reset_after)
            logger.info(
                "Rate limit bucket exhausted, sleeping %.2fs until reset",
                sleep_time,
            )
            time.sleep(sleep_time)

    def _get_retry_after(self, response: requests.Response) -> float:
        """
        Extract the Retry-After duration from a 429 response.

        Checks both the Retry-After header and the response body
        (Discord includes retry_after in the JSON body).

        Args:
            response: The 429 response

        Returns:
            float: Seconds to wait before retrying (defaults to 1.0)
        """
        # Try Retry-After header first
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except (ValueError, TypeError):
                pass

        # Try JSON body (Discord-specific)
        try:
            body = response.json()
            if "retry_after" in body:
                return float(body["retry_after"])
        except (ValueError, TypeError, KeyError):
            pass

        # Default fallback
        return 1.0

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff duration for a given retry attempt.

        Formula: min(BASE_BACKOFF * 2^attempt, MAX_BACKOFF)
        Sequence: 1s, 2s, 4s, 8s, 16s (capped at 60s)

        Args:
            attempt: Zero-based attempt number

        Returns:
            float: Seconds to wait before next retry
        """
        backoff = self.BASE_BACKOFF * (2**attempt)
        return min(backoff, self.MAX_BACKOFF)
