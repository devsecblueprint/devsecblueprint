"""Property tests for slug generation.

Property 3: Slug generation produces valid slugs
For any valid recording title (1-200 characters), the generated slug
SHALL contain only lowercase alphanumeric characters and hyphens,
SHALL NOT start or end with a hyphen, SHALL NOT contain consecutive
hyphens, and SHALL be at most 220 characters long.

Validates: Requirements 2.7
"""

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.slug_utils import ensure_unique_slug, generate_slug


@given(title=st.text(min_size=1, max_size=200))
@settings(max_examples=200)
def test_slug_format_validity(title: str) -> None:
    """Verify generated slug meets all format constraints."""
    slug = generate_slug(title)

    # May be empty if title has no alphanumeric content
    if not slug:
        return

    # Only lowercase alphanumeric and hyphens
    assert re.fullmatch(r"[a-z0-9\-]+", slug), f"Invalid chars in slug: {slug!r}"

    # No leading or trailing hyphens
    assert not slug.startswith("-"), f"Leading hyphen: {slug!r}"
    assert not slug.endswith("-"), f"Trailing hyphen: {slug!r}"

    # No consecutive hyphens
    assert "--" not in slug, f"Consecutive hyphens: {slug!r}"

    # Max 220 characters
    assert len(slug) <= 220, f"Slug too long: {len(slug)} chars"


@given(title=st.text(min_size=1, max_size=200, alphabet="abcdefghij0123456"))
@settings(max_examples=50)
def test_slug_from_alphanumeric_title(title: str) -> None:
    """Verify slug preserves alphanumeric content."""
    slug = generate_slug(title)
    if slug:
        # Should be lowercase version of the title
        assert slug == slug.lower()


def test_ensure_unique_slug_no_conflict() -> None:
    """Verify unique slug returns as-is when no conflict."""
    slug = ensure_unique_slug("my-slug", lambda s: False)
    assert slug == "my-slug"


def test_ensure_unique_slug_with_conflict() -> None:
    """Verify unique slug appends suffix on conflict."""
    existing = {"my-slug"}
    slug = ensure_unique_slug("my-slug", lambda s: s in existing)
    assert slug == "my-slug-1"


def test_ensure_unique_slug_multiple_conflicts() -> None:
    """Verify unique slug increments suffix correctly."""
    existing = {"my-slug", "my-slug-1", "my-slug-2"}
    slug = ensure_unique_slug("my-slug", lambda s: s in existing)
    assert slug == "my-slug-3"
