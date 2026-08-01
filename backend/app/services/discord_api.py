"""Discord REST API client using httpx.

Provides a simple interface for Discord guild member role management
via the Discord REST API v10. Used by discord_sync and admin_discord services.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordClient:
    """Minimal Discord REST API client for guild role operations.

    Args:
        bot_token: Discord bot authentication token.
        guild_id: Target Discord guild (server) ID.
    """

    def __init__(self, bot_token: str, guild_id: str) -> None:
        self.headers = {"Authorization": f"Bot {bot_token}"}
        self.guild_id = guild_id

    def get_member_roles(self, user_id: str) -> list[str] | None:
        """Fetch a guild member's current role IDs.

        Args:
            user_id: Discord user ID.

        Returns:
            List of role ID strings, or None if member is not in the guild.
        """
        url = f"{_DISCORD_API_BASE}/guilds/{self.guild_id}/members/{user_id}"
        try:
            resp = httpx.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("roles", [])
        except httpx.HTTPError as e:
            logger.error("Failed to get member roles for %s: %s", user_id, e)
            return None

    def add_role(self, user_id: str, role_id: str) -> bool:
        """Add a role to a guild member.

        Args:
            user_id: Discord user ID.
            role_id: Discord role ID to add.

        Returns:
            True if role was added successfully (or already present).
        """
        url = (
            f"{_DISCORD_API_BASE}/guilds/{self.guild_id}"
            f"/members/{user_id}/roles/{role_id}"
        )
        try:
            resp = httpx.put(url, headers=self.headers, timeout=10)
            return resp.status_code in (200, 204)
        except httpx.HTTPError as e:
            logger.error("Failed to add role %s to user %s: %s", role_id, user_id, e)
            return False

    def remove_role(self, user_id: str, role_id: str) -> bool:
        """Remove a role from a guild member.

        Args:
            user_id: Discord user ID.
            role_id: Discord role ID to remove.

        Returns:
            True if role was removed (or was already absent / user not in guild).
        """
        url = (
            f"{_DISCORD_API_BASE}/guilds/{self.guild_id}"
            f"/members/{user_id}/roles/{role_id}"
        )
        try:
            resp = httpx.delete(url, headers=self.headers, timeout=10)
            return resp.status_code in (200, 204, 404)
        except httpx.HTTPError as e:
            logger.error(
                "Failed to remove role %s from user %s: %s", role_id, user_id, e
            )
            return False

    def get_guild_roles(self) -> list[dict] | None:
        """Fetch all roles in the guild.

        Returns:
            List of role dicts with id, name, color, position, etc.
            Returns None on failure.
        """
        url = f"{_DISCORD_API_BASE}/guilds/{self.guild_id}/roles"
        try:
            resp = httpx.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to get guild roles: %s", e)
            return None

    def get_member_roles_with_details(self, user_id: str) -> list[dict] | None:
        """Fetch a guild member's roles with names and colors.

        Args:
            user_id: Discord user ID.

        Returns:
            List of dicts with 'name' and 'color' (hex string or None) for each
            role, excluding @everyone. Returns None if member not in guild.
        """
        member_role_ids = self.get_member_roles(user_id)
        if member_role_ids is None:
            return None

        guild_roles = self.get_guild_roles()
        if guild_roles is None:
            return None

        # Build lookup of role_id -> {name, color}
        role_lookup = {}
        for role in guild_roles:
            role_lookup[role["id"]] = {
                "name": role["name"],
                "color": role.get("color", 0),  # color is int, 0 = no color
            }

        # Match member's role IDs to guild roles, exclude @everyone
        result = []
        for role_id in member_role_ids:
            role_info = role_lookup.get(role_id)
            if role_info and role_info["name"] != "@everyone":
                # Convert color int to hex string (Discord uses decimal int)
                color_int = role_info["color"]
                color_hex = f"#{color_int:06x}" if color_int > 0 else None
                result.append(
                    {
                        "name": role_info["name"],
                        "color": color_hex,
                    }
                )

        return result
