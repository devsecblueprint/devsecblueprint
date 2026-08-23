"""Slug generation utilities for videos.

Provides functions to generate URL-safe slugs from titles and ensure
uniqueness by appending numeric suffixes when conflicts arise.

Requirements: 2.7
"""

import re
import unicodedata
from collections.abc import Callable


def generate_slug(title: str) -> str:
    """Generate a URL-safe slug from a recording title.

    Applies the following transformations:
    - Normalize unicode characters to ASCII equivalents
    - Convert to lowercase
    - Replace non-alphanumeric characters with hyphens
    - Collapse consecutive hyphens into a single hyphen
    - Strip leading and trailing hyphens
    - Truncate to 220 characters maximum

    Args:
        title: The recording title (1-200 characters).

    Returns:
        A URL-safe slug string.
    """
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:220]


def ensure_unique_slug(
    slug: str,
    existing_check_fn: Callable[[str], bool],
) -> str:
    """Append a numeric suffix if the slug conflicts with an existing one.

    Args:
        slug: The base slug to check.
        existing_check_fn: A callable that returns True if the slug
            already exists in the database.

    Returns:
        A unique slug string.

    Raises:
        ValueError: If a unique slug cannot be generated after 999 attempts.
    """
    if not existing_check_fn(slug):
        return slug
    for i in range(1, 1000):
        candidate = f"{slug}-{i}"
        if not existing_check_fn(candidate):
            return candidate
    raise ValueError("Could not generate unique slug")
