"""
Unit tests for Walkthrough Service

Tests business logic functions for walkthrough operations including
filtering, retrieval, and README loading.
"""

import pytest
import tempfile
import json
from pathlib import Path
from backend.services import walkthrough_service
from backend.services.walkthrough_registry import WalkthroughRegistry


@pytest.fixture
def temp_walkthroughs_dir():
    """Create a temporary walkthroughs directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_walkthroughs(temp_walkthroughs_dir):
    """Return sample walkthrough metadata with correct repository paths."""
    return [
        {
            "id": "beginner-cicd",
            "title": "Introduction to CI/CD",
            "description": "Learn the basics of continuous integration",
            "difficulty": "Beginner",
            "topics": ["CI/CD", "DevOps"],
            "estimatedTime": 30,
            "prerequisites": [],
            "repository": str(temp_walkthroughs_dir / "beginner-cicd"),
        },
        {
            "id": "intermediate-security",
            "title": "Container Security",
            "description": "Secure your containers with best practices",
            "difficulty": "Intermediate",
            "topics": ["Security", "Containers"],
            "estimatedTime": 60,
            "prerequisites": ["beginner-cicd"],
            "repository": str(temp_walkthroughs_dir / "intermediate-security"),
        },
        {
            "id": "advanced-kubernetes",
            "title": "Kubernetes Security Hardening",
            "description": "Advanced security configurations for Kubernetes",
            "difficulty": "Advanced",
            "topics": ["Kubernetes", "Security"],
            "estimatedTime": 90,
            "prerequisites": ["intermediate-security"],
            "repository": str(temp_walkthroughs_dir / "advanced-kubernetes"),
        },
    ]


def create_walkthrough_with_readme(
    base_dir: Path, walkthrough_id: str, metadata: dict, readme_content: str = None
):
    """Helper to create a walkthrough directory with metadata.json and README.md."""
    walkthrough_dir = base_dir / walkthrough_id
    walkthrough_dir.mkdir(parents=True, exist_ok=True)

    # Create metadata.json
    metadata_file = walkthrough_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f)

    # Create README.md if content provided
    if readme_content is not None:
        readme_file = walkthrough_dir / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)

    return walkthrough_dir


@pytest.fixture
def setup_registry(temp_walkthroughs_dir, sample_walkthroughs, monkeypatch):
    """Setup a test registry with sample walkthroughs."""
    # Create walkthroughs with README files
    for wt in sample_walkthroughs:
        readme_content = f"# {wt['title']}\n\nThis is the README for {wt['id']}."
        create_walkthrough_with_readme(
            temp_walkthroughs_dir, wt["id"], wt, readme_content
        )

    # Create a new registry instance with the temp directory
    test_registry = WalkthroughRegistry(str(temp_walkthroughs_dir))

    # Monkey patch the get_registry function to return our test registry
    monkeypatch.setattr(walkthrough_service, "get_registry", lambda: test_registry)

    return test_registry


class TestGetWalkthroughs:
    """Tests for get_walkthroughs function."""

    def test_get_all_walkthroughs(self, setup_registry):
        """Test retrieving all walkthroughs without filters."""
        results = walkthrough_service.get_walkthroughs()

        assert len(results) == 3
        assert all(isinstance(wt, dict) for wt in results)

        # Verify all expected fields are present
        for wt in results:
            assert "id" in wt
            assert "title" in wt
            assert "description" in wt
            assert "difficulty" in wt
            assert "topics" in wt
            assert "estimatedTime" in wt
            assert "prerequisites" in wt
            assert "repository" in wt

    def test_filter_by_difficulty_beginner(self, setup_registry):
        """Test filtering by Beginner difficulty."""
        results = walkthrough_service.get_walkthroughs(difficulty="Beginner")

        assert len(results) == 1
        assert results[0]["id"] == "beginner-cicd"
        assert results[0]["difficulty"] == "Beginner"

    def test_filter_by_difficulty_intermediate(self, setup_registry):
        """Test filtering by Intermediate difficulty."""
        results = walkthrough_service.get_walkthroughs(difficulty="Intermediate")

        assert len(results) == 1
        assert results[0]["id"] == "intermediate-security"
        assert results[0]["difficulty"] == "Intermediate"

    def test_filter_by_difficulty_advanced(self, setup_registry):
        """Test filtering by Advanced difficulty."""
        results = walkthrough_service.get_walkthroughs(difficulty="Advanced")

        assert len(results) == 1
        assert results[0]["id"] == "advanced-kubernetes"
        assert results[0]["difficulty"] == "Advanced"

    def test_filter_by_single_topic(self, setup_registry):
        """Test filtering by a single topic."""
        results = walkthrough_service.get_walkthroughs(topics=["Security"])

        assert len(results) == 2
        ids = {wt["id"] for wt in results}
        assert ids == {"intermediate-security", "advanced-kubernetes"}

    def test_filter_by_multiple_topics(self, setup_registry):
        """Test filtering by multiple topics (OR logic)."""
        results = walkthrough_service.get_walkthroughs(topics=["CI/CD", "Kubernetes"])

        assert len(results) == 2
        ids = {wt["id"] for wt in results}
        assert ids == {"beginner-cicd", "advanced-kubernetes"}

    def test_search_in_title(self, setup_registry):
        """Test search matching in title."""
        results = walkthrough_service.get_walkthroughs(search="CI/CD")

        assert len(results) == 1
        assert results[0]["id"] == "beginner-cicd"

    def test_search_in_description(self, setup_registry):
        """Test search matching in description."""
        results = walkthrough_service.get_walkthroughs(search="containers")

        assert len(results) == 1
        assert results[0]["id"] == "intermediate-security"

    def test_search_in_topics(self, setup_registry):
        """Test search matching in topics."""
        results = walkthrough_service.get_walkthroughs(search="Security")

        assert len(results) == 2
        ids = {wt["id"] for wt in results}
        assert ids == {"intermediate-security", "advanced-kubernetes"}

    def test_search_case_insensitive(self, setup_registry):
        """Test search is case-insensitive."""
        results_lower = walkthrough_service.get_walkthroughs(search="security")
        results_upper = walkthrough_service.get_walkthroughs(search="SECURITY")

        assert len(results_lower) == 2
        assert len(results_upper) == 2

    def test_search_partial_match(self, setup_registry):
        """Test search supports partial matching."""
        results = walkthrough_service.get_walkthroughs(search="Kube")

        assert len(results) == 1
        assert results[0]["id"] == "advanced-kubernetes"

    def test_combined_filters_difficulty_and_topics(self, setup_registry):
        """Test combining difficulty and topics filters (AND logic)."""
        results = walkthrough_service.get_walkthroughs(
            difficulty="Intermediate", topics=["Security"]
        )

        assert len(results) == 1
        assert results[0]["id"] == "intermediate-security"

    def test_combined_filters_difficulty_and_search(self, setup_registry):
        """Test combining difficulty and search filters (AND logic)."""
        results = walkthrough_service.get_walkthroughs(
            difficulty="Advanced", search="Kubernetes"
        )

        assert len(results) == 1
        assert results[0]["id"] == "advanced-kubernetes"

    def test_combined_filters_all_three(self, setup_registry):
        """Test combining all three filters (AND logic)."""
        results = walkthrough_service.get_walkthroughs(
            difficulty="Advanced", topics=["Security"], search="Kubernetes"
        )

        assert len(results) == 1
        assert results[0]["id"] == "advanced-kubernetes"

    def test_filters_no_matches(self, setup_registry):
        """Test filters that match no walkthroughs."""
        results = walkthrough_service.get_walkthroughs(
            difficulty="Beginner", topics=["Kubernetes"]
        )

        assert len(results) == 0

    def test_dict_format(self, setup_registry):
        """Test that returned walkthroughs are in correct dict format."""
        results = walkthrough_service.get_walkthroughs()

        assert len(results) > 0
        wt = results[0]

        # Verify camelCase for estimatedTime
        assert "estimatedTime" in wt
        assert isinstance(wt["estimatedTime"], int)

        # Verify all fields have correct types
        assert isinstance(wt["id"], str)
        assert isinstance(wt["title"], str)
        assert isinstance(wt["description"], str)
        assert isinstance(wt["difficulty"], str)
        assert isinstance(wt["topics"], list)
        assert isinstance(wt["prerequisites"], list)
        assert isinstance(wt["repository"], str)


class TestGetWalkthroughById:
    """Tests for get_walkthrough_by_id function."""

    def test_get_existing_walkthrough(self, setup_registry):
        """Test retrieving an existing walkthrough by ID."""
        result = walkthrough_service.get_walkthrough_by_id("beginner-cicd")

        assert result is not None
        assert result["id"] == "beginner-cicd"
        assert result["title"] == "Introduction to CI/CD"
        assert result["difficulty"] == "Beginner"

    def test_get_nonexistent_walkthrough(self, setup_registry):
        """Test retrieving a nonexistent walkthrough returns None."""
        result = walkthrough_service.get_walkthrough_by_id("nonexistent")

        assert result is None

    def test_dict_format(self, setup_registry):
        """Test that returned walkthrough is in correct dict format."""
        result = walkthrough_service.get_walkthrough_by_id("intermediate-security")

        assert result is not None

        # Verify all expected fields
        assert "id" in result
        assert "title" in result
        assert "description" in result
        assert "difficulty" in result
        assert "topics" in result
        assert "estimatedTime" in result
        assert "prerequisites" in result
        assert "repository" in result

        # Verify camelCase for estimatedTime
        assert result["estimatedTime"] == 60

    def test_all_walkthroughs_retrievable(self, setup_registry):
        """Test that all walkthroughs can be retrieved by ID."""
        all_walkthroughs = walkthrough_service.get_walkthroughs()

        for wt in all_walkthroughs:
            result = walkthrough_service.get_walkthrough_by_id(wt["id"])
            assert result is not None
            assert result["id"] == wt["id"]


class TestLoadReadme:
    """Tests for load_readme function."""

    def test_load_existing_readme(self, setup_registry, temp_walkthroughs_dir):
        """Test loading README for an existing walkthrough."""
        readme_content = walkthrough_service.load_readme("beginner-cicd")

        assert readme_content is not None
        assert isinstance(readme_content, str)
        assert "Introduction to CI/CD" in readme_content
        assert "beginner-cicd" in readme_content

    def test_load_readme_preserves_content(self, setup_registry, temp_walkthroughs_dir):
        """Test that README content is preserved exactly."""
        expected_content = "# Test\n\nThis is a test README with **markdown**."

        # Create a walkthrough with specific README content
        metadata = {
            "id": "test-readme",
            "title": "Test README",
            "description": "Testing README loading",
            "difficulty": "Beginner",
            "topics": ["Test"],
            "estimatedTime": 10,
            "prerequisites": [],
            "repository": str(temp_walkthroughs_dir / "test-readme"),
        }
        create_walkthrough_with_readme(
            temp_walkthroughs_dir, "test-readme", metadata, expected_content
        )

        # Reload registry to pick up new walkthrough
        test_registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        walkthrough_service.get_registry = lambda: test_registry

        readme_content = walkthrough_service.load_readme("test-readme")

        assert readme_content == expected_content

    def test_load_readme_nonexistent_walkthrough(self, setup_registry):
        """Test loading README for nonexistent walkthrough raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            walkthrough_service.load_readme("nonexistent")

        assert "Walkthrough not found" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_load_readme_missing_file(self, setup_registry, temp_walkthroughs_dir):
        """Test loading README when file doesn't exist raises FileNotFoundError."""
        # Create a walkthrough without README
        metadata = {
            "id": "no-readme",
            "title": "No README",
            "description": "Walkthrough without README",
            "difficulty": "Beginner",
            "topics": ["Test"],
            "estimatedTime": 10,
            "prerequisites": [],
            "repository": str(temp_walkthroughs_dir / "no-readme"),
        }
        create_walkthrough_with_readme(
            temp_walkthroughs_dir, "no-readme", metadata, readme_content=None
        )

        # Reload registry to pick up new walkthrough
        test_registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        walkthrough_service.get_registry = lambda: test_registry

        with pytest.raises(FileNotFoundError) as exc_info:
            walkthrough_service.load_readme("no-readme")

        assert "README.md not found" in str(exc_info.value)
        assert "no-readme" in str(exc_info.value)

    def test_load_readme_utf8_encoding(self, setup_registry, temp_walkthroughs_dir):
        """Test that README is loaded with UTF-8 encoding."""
        # Create README with UTF-8 characters
        utf8_content = "# Test\n\nUnicode: 你好 🚀 café"

        metadata = {
            "id": "utf8-test",
            "title": "UTF-8 Test",
            "description": "Testing UTF-8 encoding",
            "difficulty": "Beginner",
            "topics": ["Test"],
            "estimatedTime": 10,
            "prerequisites": [],
            "repository": str(temp_walkthroughs_dir / "utf8-test"),
        }
        create_walkthrough_with_readme(
            temp_walkthroughs_dir, "utf8-test", metadata, utf8_content
        )

        # Reload registry
        test_registry = WalkthroughRegistry(str(temp_walkthroughs_dir))
        walkthrough_service.get_registry = lambda: test_registry

        readme_content = walkthrough_service.load_readme("utf8-test")

        assert readme_content == utf8_content
        assert "你好" in readme_content
        assert "🚀" in readme_content
        assert "café" in readme_content


class TestWalkthroughToDict:
    """Tests for _walkthrough_to_dict helper function."""

    def test_conversion_preserves_all_fields(self, setup_registry):
        """Test that conversion preserves all metadata fields."""
        from backend.services.walkthrough_registry import WalkthroughMetadata

        metadata = WalkthroughMetadata(
            id="test-id",
            title="Test Title",
            description="Test Description",
            difficulty="Intermediate",
            topics=["Topic1", "Topic2"],
            estimated_time=45,
            prerequisites=["prereq1"],
            repository="walkthroughs/test",
        )

        result = walkthrough_service._walkthrough_to_dict(metadata)

        assert result["id"] == "test-id"
        assert result["title"] == "Test Title"
        assert result["description"] == "Test Description"
        assert result["difficulty"] == "Intermediate"
        assert result["topics"] == ["Topic1", "Topic2"]
        assert result["estimatedTime"] == 45
        assert result["prerequisites"] == ["prereq1"]
        assert result["repository"] == "walkthroughs/test"

    def test_camelcase_estimated_time(self, setup_registry):
        """Test that estimated_time is converted to estimatedTime."""
        from backend.services.walkthrough_registry import WalkthroughMetadata

        metadata = WalkthroughMetadata(
            id="test",
            title="Test",
            description="Test",
            difficulty="Beginner",
            topics=[],
            estimated_time=30,
            prerequisites=[],
            repository="test",
        )

        result = walkthrough_service._walkthrough_to_dict(metadata)

        assert "estimatedTime" in result
        assert "estimated_time" not in result
        assert result["estimatedTime"] == 30


class TestGetWalkthroughProgress:
    """Tests for get_walkthrough_progress function."""

    def test_get_progress_existing_record(self, monkeypatch):
        """Test retrieving existing progress record."""

        # Mock the dynamo function
        def mock_get_progress(user_id, walkthrough_id):
            return {
                "status": "in_progress",
                "started_at": "2024-01-15T10:00:00+00:00",
                "completed_at": None,
            }

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )

        result = walkthrough_service.get_walkthrough_progress(
            "user123", "walkthrough-id"
        )

        assert result["status"] == "in_progress"
        assert result["started_at"] == "2024-01-15T10:00:00+00:00"
        assert result["completed_at"] is None

    def test_get_progress_completed_record(self, monkeypatch):
        """Test retrieving completed progress record."""

        def mock_get_progress(user_id, walkthrough_id):
            return {
                "status": "completed",
                "started_at": "2024-01-15T10:00:00+00:00",
                "completed_at": "2024-01-20T15:30:00+00:00",
            }

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )

        result = walkthrough_service.get_walkthrough_progress(
            "user123", "walkthrough-id"
        )

        assert result["status"] == "completed"
        assert result["started_at"] == "2024-01-15T10:00:00+00:00"
        assert result["completed_at"] == "2024-01-20T15:30:00+00:00"

    def test_get_progress_no_record(self, monkeypatch):
        """Test retrieving progress when no record exists returns not_started."""

        def mock_get_progress(user_id, walkthrough_id):
            return None

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )

        result = walkthrough_service.get_walkthrough_progress(
            "user123", "walkthrough-id"
        )

        assert result["status"] == "not_started"
        assert result["started_at"] is None
        assert result["completed_at"] is None

    def test_get_progress_handles_empty_timestamps(self, monkeypatch):
        """Test that empty string timestamps are converted to None."""

        def mock_get_progress(user_id, walkthrough_id):
            return {"status": "in_progress", "started_at": "", "completed_at": ""}

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )

        result = walkthrough_service.get_walkthrough_progress(
            "user123", "walkthrough-id"
        )

        assert result["status"] == "in_progress"
        assert result["started_at"] is None
        assert result["completed_at"] is None


class TestUpdateWalkthroughProgress:
    """Tests for update_walkthrough_progress function."""

    def test_update_to_in_progress_first_view(self, monkeypatch):
        """Test updating to in_progress on first view sets started_at."""

        # Mock dynamo functions
        def mock_get_progress(user_id, walkthrough_id):
            return None  # No existing record

        saved_data = {}

        def mock_save_progress(
            user_id, walkthrough_id, status, started_at=None, completed_at=None
        ):
            saved_data["user_id"] = user_id
            saved_data["walkthrough_id"] = walkthrough_id
            saved_data["status"] = status
            saved_data["started_at"] = started_at
            saved_data["completed_at"] = completed_at

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )
        monkeypatch.setattr(
            dynamo_module, "save_walkthrough_progress", mock_save_progress
        )

        walkthrough_service.update_walkthrough_progress(
            "user123", "walkthrough-id", "in_progress"
        )

        assert saved_data["user_id"] == "user123"
        assert saved_data["walkthrough_id"] == "walkthrough-id"
        assert saved_data["status"] == "in_progress"
        assert saved_data["started_at"] is not None
        assert saved_data["completed_at"] is None

        # Verify started_at is a valid ISO timestamp
        from datetime import datetime

        datetime.fromisoformat(saved_data["started_at"])

    def test_update_to_in_progress_existing_record(self, monkeypatch):
        """Test updating to in_progress with existing record preserves started_at."""
        existing_started_at = "2024-01-15T10:00:00+00:00"

        def mock_get_progress(user_id, walkthrough_id):
            return {
                "status": "in_progress",
                "started_at": existing_started_at,
                "completed_at": None,
            }

        saved_data = {}

        def mock_save_progress(
            user_id, walkthrough_id, status, started_at=None, completed_at=None
        ):
            saved_data["started_at"] = started_at
            saved_data["status"] = status

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )
        monkeypatch.setattr(
            dynamo_module, "save_walkthrough_progress", mock_save_progress
        )

        walkthrough_service.update_walkthrough_progress(
            "user123", "walkthrough-id", "in_progress"
        )

        assert saved_data["started_at"] == existing_started_at
        assert saved_data["status"] == "in_progress"

    def test_update_to_completed_sets_completed_at(self, monkeypatch):
        """Test updating to completed sets completed_at timestamp."""
        existing_started_at = "2024-01-15T10:00:00+00:00"

        def mock_get_progress(user_id, walkthrough_id):
            return {
                "status": "in_progress",
                "started_at": existing_started_at,
                "completed_at": None,
            }

        saved_data = {}

        def mock_save_progress(
            user_id, walkthrough_id, status, started_at=None, completed_at=None
        ):
            saved_data["status"] = status
            saved_data["started_at"] = started_at
            saved_data["completed_at"] = completed_at

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )
        monkeypatch.setattr(
            dynamo_module, "save_walkthrough_progress", mock_save_progress
        )

        walkthrough_service.update_walkthrough_progress(
            "user123", "walkthrough-id", "completed"
        )

        assert saved_data["status"] == "completed"
        assert saved_data["started_at"] == existing_started_at
        assert saved_data["completed_at"] is not None

        # Verify completed_at is a valid ISO timestamp
        from datetime import datetime

        datetime.fromisoformat(saved_data["completed_at"])

    def test_update_to_completed_without_prior_record(self, monkeypatch):
        """Test updating to completed without prior record sets both timestamps."""

        def mock_get_progress(user_id, walkthrough_id):
            return None

        saved_data = {}

        def mock_save_progress(
            user_id, walkthrough_id, status, started_at=None, completed_at=None
        ):
            saved_data["status"] = status
            saved_data["started_at"] = started_at
            saved_data["completed_at"] = completed_at

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )
        monkeypatch.setattr(
            dynamo_module, "save_walkthrough_progress", mock_save_progress
        )

        walkthrough_service.update_walkthrough_progress(
            "user123", "walkthrough-id", "completed"
        )

        assert saved_data["status"] == "completed"
        assert saved_data["started_at"] is not None
        assert saved_data["completed_at"] is not None

        # Both timestamps should be valid
        from datetime import datetime

        datetime.fromisoformat(saved_data["started_at"])
        datetime.fromisoformat(saved_data["completed_at"])

    def test_update_invalid_status_raises_error(self, monkeypatch):
        """Test that invalid status raises ValueError."""

        def mock_get_progress(user_id, walkthrough_id):
            return None

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )

        with pytest.raises(ValueError) as exc_info:
            walkthrough_service.update_walkthrough_progress(
                "user123", "walkthrough-id", "invalid_status"
            )

        assert "Invalid status" in str(exc_info.value)
        assert "invalid_status" in str(exc_info.value)

    def test_update_not_started_status_raises_error(self, monkeypatch):
        """Test that not_started status is not allowed for updates."""

        def mock_get_progress(user_id, walkthrough_id):
            return None

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )

        with pytest.raises(ValueError) as exc_info:
            walkthrough_service.update_walkthrough_progress(
                "user123", "walkthrough-id", "not_started"
            )

        assert "Invalid status" in str(exc_info.value)

    def test_update_preserves_started_at_when_completing(self, monkeypatch):
        """Test that completing a walkthrough preserves the original started_at."""
        original_started_at = "2024-01-10T08:00:00+00:00"

        def mock_get_progress(user_id, walkthrough_id):
            return {
                "status": "in_progress",
                "started_at": original_started_at,
                "completed_at": None,
            }

        saved_data = {}

        def mock_save_progress(
            user_id, walkthrough_id, status, started_at=None, completed_at=None
        ):
            saved_data["started_at"] = started_at
            saved_data["completed_at"] = completed_at

        import backend.services.dynamo as dynamo_module

        monkeypatch.setattr(
            dynamo_module, "get_walkthrough_progress", mock_get_progress
        )
        monkeypatch.setattr(
            dynamo_module, "save_walkthrough_progress", mock_save_progress
        )

        walkthrough_service.update_walkthrough_progress(
            "user123", "walkthrough-id", "completed"
        )

        # Original started_at should be preserved
        assert saved_data["started_at"] == original_started_at
        # completed_at should be set to a new timestamp
        assert saved_data["completed_at"] is not None
        assert saved_data["completed_at"] != original_started_at
