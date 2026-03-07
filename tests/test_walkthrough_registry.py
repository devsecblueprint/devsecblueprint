"""
Unit tests for Walkthrough Registry

Tests walkthrough discovery, metadata validation, caching, and query methods.
"""

import pytest
import json
import tempfile
from pathlib import Path
from backend.services.walkthrough_registry import (
    WalkthroughRegistry,
    WalkthroughMetadata,
    get_registry,
)


@pytest.fixture
def temp_walkthroughs_dir():
    """Create a temporary walkthroughs directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_metadata():
    """Return valid walkthrough metadata."""
    return {
        "id": "test-walkthrough",
        "title": "Test Walkthrough",
        "description": "A test walkthrough for unit testing",
        "difficulty": "Beginner",
        "topics": ["Testing", "Example"],
        "estimatedTime": 45,
        "prerequisites": ["intro-module"],
        "repository": "walkthroughs/test-walkthrough",
    }


def create_walkthrough(base_dir: Path, walkthrough_id: str, metadata: dict):
    """Helper to create a walkthrough directory with metadata.json."""
    walkthrough_dir = base_dir / walkthrough_id
    walkthrough_dir.mkdir(parents=True, exist_ok=True)

    metadata_file = walkthrough_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f)

    return walkthrough_dir


class TestWalkthroughMetadata:
    """Tests for WalkthroughMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating a WalkthroughMetadata instance."""
        metadata = WalkthroughMetadata(
            id="test-id",
            title="Test Title",
            description="Test Description",
            difficulty="Intermediate",
            topics=["Topic1", "Topic2"],
            estimated_time=60,
            prerequisites=["prereq1"],
            repository="walkthroughs/test",
        )

        assert metadata.id == "test-id"
        assert metadata.title == "Test Title"
        assert metadata.difficulty == "Intermediate"
        assert len(metadata.topics) == 2


class TestWalkthroughRegistry:
    """Tests for WalkthroughRegistry class."""

    def test_empty_directory(self, temp_walkthroughs_dir):
        """Test registry with empty directory."""
        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_nonexistent_directory(self):
        """Test registry with nonexistent directory."""
        registry = WalkthroughRegistry("/nonexistent/path")
        assert len(registry.get_all()) == 0

    def test_load_valid_walkthrough(self, temp_walkthroughs_dir, valid_metadata):
        """Test loading a valid walkthrough."""
        create_walkthrough(temp_walkthroughs_dir, "test-walkthrough", valid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        walkthroughs = registry.get_all()

        assert len(walkthroughs) == 1
        assert walkthroughs[0].id == "test-walkthrough"
        assert walkthroughs[0].title == "Test Walkthrough"
        assert walkthroughs[0].difficulty == "Beginner"

    def test_skip_template_directory(self, temp_walkthroughs_dir, valid_metadata):
        """Test that template directory is skipped."""
        # Create template directory
        template_metadata = valid_metadata.copy()
        template_metadata["id"] = "template"
        create_walkthrough(temp_walkthroughs_dir, "template", template_metadata)

        # Create regular walkthrough
        create_walkthrough(temp_walkthroughs_dir, "test-walkthrough", valid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        walkthroughs = registry.get_all()

        # Should only load the non-template walkthrough
        assert len(walkthroughs) == 1
        assert walkthroughs[0].id == "test-walkthrough"

    def test_skip_missing_metadata(self, temp_walkthroughs_dir):
        """Test that directories without metadata.json are skipped."""
        # Create directory without metadata.json
        walkthrough_dir = temp_walkthroughs_dir / "no-metadata"
        walkthrough_dir.mkdir()

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_skip_invalid_json(self, temp_walkthroughs_dir):
        """Test that walkthroughs with invalid JSON are skipped."""
        walkthrough_dir = temp_walkthroughs_dir / "invalid-json"
        walkthrough_dir.mkdir()

        metadata_file = walkthrough_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            f.write("{ invalid json }")

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_skip_missing_required_field(self, temp_walkthroughs_dir, valid_metadata):
        """Test that metadata missing required fields is skipped."""
        # Remove required field
        invalid_metadata = valid_metadata.copy()
        del invalid_metadata["title"]

        create_walkthrough(temp_walkthroughs_dir, "invalid", invalid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_skip_invalid_difficulty(self, temp_walkthroughs_dir, valid_metadata):
        """Test that metadata with invalid difficulty is skipped."""
        invalid_metadata = valid_metadata.copy()
        invalid_metadata["difficulty"] = "Expert"  # Invalid value

        create_walkthrough(temp_walkthroughs_dir, "invalid", invalid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_skip_negative_estimated_time(self, temp_walkthroughs_dir, valid_metadata):
        """Test that metadata with negative estimatedTime is skipped."""
        invalid_metadata = valid_metadata.copy()
        invalid_metadata["estimatedTime"] = -10

        create_walkthrough(temp_walkthroughs_dir, "invalid", invalid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_skip_zero_estimated_time(self, temp_walkthroughs_dir, valid_metadata):
        """Test that metadata with zero estimatedTime is skipped."""
        invalid_metadata = valid_metadata.copy()
        invalid_metadata["estimatedTime"] = 0

        create_walkthrough(temp_walkthroughs_dir, "invalid", invalid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_skip_wrong_type_topics(self, temp_walkthroughs_dir, valid_metadata):
        """Test that metadata with non-array topics is skipped."""
        invalid_metadata = valid_metadata.copy()
        invalid_metadata["topics"] = "not-an-array"

        create_walkthrough(temp_walkthroughs_dir, "invalid", invalid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        assert len(registry.get_all()) == 0

    def test_load_multiple_walkthroughs(self, temp_walkthroughs_dir, valid_metadata):
        """Test loading multiple valid walkthroughs."""
        # Create first walkthrough
        create_walkthrough(temp_walkthroughs_dir, "walkthrough-1", valid_metadata)

        # Create second walkthrough
        metadata2 = valid_metadata.copy()
        metadata2["id"] = "walkthrough-2"
        metadata2["title"] = "Second Walkthrough"
        create_walkthrough(temp_walkthroughs_dir, "walkthrough-2", metadata2)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        walkthroughs = registry.get_all()

        assert len(walkthroughs) == 2
        ids = {wt.id for wt in walkthroughs}
        assert ids == {"test-walkthrough", "walkthrough-2"}


class TestRegistryQueries:
    """Tests for registry query methods."""

    @pytest.fixture
    def populated_registry(self, temp_walkthroughs_dir):
        """Create a registry with multiple walkthroughs."""
        walkthroughs = [
            {
                "id": "beginner-cicd",
                "title": "Introduction to CI/CD",
                "description": "Learn the basics of continuous integration",
                "difficulty": "Beginner",
                "topics": ["CI/CD", "DevOps"],
                "estimatedTime": 30,
                "prerequisites": [],
                "repository": "walkthroughs/beginner-cicd",
            },
            {
                "id": "intermediate-security",
                "title": "Container Security",
                "description": "Secure your containers with best practices",
                "difficulty": "Intermediate",
                "topics": ["Security", "Containers"],
                "estimatedTime": 60,
                "prerequisites": ["beginner-cicd"],
                "repository": "walkthroughs/intermediate-security",
            },
            {
                "id": "advanced-kubernetes",
                "title": "Kubernetes Security Hardening",
                "description": "Advanced security configurations for Kubernetes",
                "difficulty": "Advanced",
                "topics": ["Kubernetes", "Security"],
                "estimatedTime": 90,
                "prerequisites": ["intermediate-security"],
                "repository": "walkthroughs/advanced-kubernetes",
            },
        ]

        for wt in walkthroughs:
            create_walkthrough(temp_walkthroughs_dir, wt["id"], wt)

        return WalkthroughRegistry(str(temp_walkthroughs_dir))

    def test_get_by_id_existing(self, populated_registry):
        """Test retrieving a walkthrough by existing ID."""
        walkthrough = populated_registry.get_by_id("beginner-cicd")

        assert walkthrough is not None
        assert walkthrough.id == "beginner-cicd"
        assert walkthrough.title == "Introduction to CI/CD"

    def test_get_by_id_nonexistent(self, populated_registry):
        """Test retrieving a walkthrough by nonexistent ID."""
        walkthrough = populated_registry.get_by_id("nonexistent")
        assert walkthrough is None

    def test_filter_by_difficulty_beginner(self, populated_registry):
        """Test filtering by Beginner difficulty."""
        results = populated_registry.filter_by_difficulty("Beginner")

        assert len(results) == 1
        assert results[0].id == "beginner-cicd"

    def test_filter_by_difficulty_intermediate(self, populated_registry):
        """Test filtering by Intermediate difficulty."""
        results = populated_registry.filter_by_difficulty("Intermediate")

        assert len(results) == 1
        assert results[0].id == "intermediate-security"

    def test_filter_by_difficulty_advanced(self, populated_registry):
        """Test filtering by Advanced difficulty."""
        results = populated_registry.filter_by_difficulty("Advanced")

        assert len(results) == 1
        assert results[0].id == "advanced-kubernetes"

    def test_filter_by_difficulty_no_matches(self, populated_registry):
        """Test filtering with no matches."""
        results = populated_registry.filter_by_difficulty("Expert")
        assert len(results) == 0

    def test_filter_by_single_topic(self, populated_registry):
        """Test filtering by a single topic."""
        results = populated_registry.filter_by_topics(["Security"])

        assert len(results) == 2
        ids = {wt.id for wt in results}
        assert ids == {"intermediate-security", "advanced-kubernetes"}

    def test_filter_by_multiple_topics(self, populated_registry):
        """Test filtering by multiple topics (OR logic)."""
        results = populated_registry.filter_by_topics(["CI/CD", "Kubernetes"])

        assert len(results) == 2
        ids = {wt.id for wt in results}
        assert ids == {"beginner-cicd", "advanced-kubernetes"}

    def test_filter_by_topic_no_matches(self, populated_registry):
        """Test filtering by topic with no matches."""
        results = populated_registry.filter_by_topics(["Nonexistent"])
        assert len(results) == 0

    def test_search_in_title(self, populated_registry):
        """Test search matching in title."""
        results = populated_registry.search("CI/CD")

        assert len(results) == 1
        assert results[0].id == "beginner-cicd"

    def test_search_in_description(self, populated_registry):
        """Test search matching in description."""
        results = populated_registry.search("containers")

        assert len(results) == 1
        assert results[0].id == "intermediate-security"

    def test_search_in_topics(self, populated_registry):
        """Test search matching in topics."""
        results = populated_registry.search("Security")

        assert len(results) == 2
        ids = {wt.id for wt in results}
        assert ids == {"intermediate-security", "advanced-kubernetes"}

    def test_search_case_insensitive(self, populated_registry):
        """Test search is case-insensitive."""
        results_lower = populated_registry.search("security")
        results_upper = populated_registry.search("SECURITY")
        results_mixed = populated_registry.search("SeCuRiTy")

        assert len(results_lower) == 2
        assert len(results_upper) == 2
        assert len(results_mixed) == 2

    def test_search_partial_match(self, populated_registry):
        """Test search supports partial matching."""
        results = populated_registry.search("Kube")

        assert len(results) == 1
        assert results[0].id == "advanced-kubernetes"

    def test_search_no_matches(self, populated_registry):
        """Test search with no matches."""
        results = populated_registry.search("nonexistent")
        assert len(results) == 0


class TestGlobalRegistry:
    """Tests for global registry singleton."""

    def test_get_registry_singleton(self):
        """Test that get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2


class TestCaching:
    """Tests for registry caching behavior."""

    def test_cache_populated_on_init(self, temp_walkthroughs_dir, valid_metadata):
        """Test that cache is populated during initialization."""
        create_walkthrough(temp_walkthroughs_dir, "test-walkthrough", valid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))

        # Verify cache is populated
        assert len(registry._cache) == 1
        assert "test-walkthrough" in registry._cache

    def test_get_all_returns_cached_data(self, temp_walkthroughs_dir, valid_metadata):
        """Test that get_all returns data from cache."""
        create_walkthrough(temp_walkthroughs_dir, "test-walkthrough", valid_metadata)

        registry = WalkthroughRegistry(str(temp_walkthroughs_dir))

        # Get all walkthroughs
        walkthroughs1 = registry.get_all()
        walkthroughs2 = registry.get_all()

        # Should return same data (from cache)
        assert len(walkthroughs1) == len(walkthroughs2)
        assert walkthroughs1[0].id == walkthroughs2[0].id
