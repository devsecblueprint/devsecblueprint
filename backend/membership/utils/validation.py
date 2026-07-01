"""
Input validation utilities for the membership service.

Provides validation functions for Discord IDs, control character rejection,
and field length enforcement.
"""

import re


def validate_discord_id(value: str) -> bool:
    """
    Validate that a value is a valid Discord User ID (snowflake).

    Discord IDs are numeric strings of 17-20 characters representing
    a Twitter-style snowflake ID.

    Args:
        value: The string to validate

    Returns:
        bool: True if value is a valid Discord ID, False otherwise

    Validates: Requirements 10.1, 18.2
    """
    if not isinstance(value, str):
        return False
    if len(value) < 17 or len(value) > 20:
        return False
    return value.isdigit()


def reject_control_characters(value: str) -> str:
    """
    Check for and reject control characters in input strings.

    Raises ValueError if any ASCII control characters (0x00-0x1F) are found,
    excluding common whitespace (tab \\t, newline \\n, carriage return \\r).

    Args:
        value: The string to validate

    Returns:
        str: The original string if valid

    Raises:
        ValueError: If control characters are detected

    Validates: Requirements 10.3, 18.1
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")

    # Match control characters 0x00-0x1F except \t (0x09), \n (0x0A), \r (0x0D)
    control_pattern = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
    if control_pattern.search(value):
        raise ValueError("Input contains invalid control characters")

    return value


def validate_field_length(value: str, max_length: int, field_name: str) -> str:
    """
    Validate that a string field does not exceed the maximum length.

    Args:
        value: The string to validate
        max_length: Maximum allowed length
        field_name: Name of the field (for error messages)

    Returns:
        str: The original string if valid

    Raises:
        ValueError: If the value exceeds max_length

    Validates: Requirements 10.2, 18.1
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} exceeds maximum length of {max_length} characters"
        )

    return value
