"""
Walkthrough Registry Module

Server-side component that discovers, parses, and caches walkthrough metadata.
Provides discovery, filtering, and search capabilities for walkthroughs.

Requirements: 3.1, 3.2, 3.8, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class WalkthroughMetadata:
    """
    Walkthrough metadata structure.

    Attributes:
        id: Unique walkthrough identifier
        title: Walkthrough name
        description: Summary of the walkthrough
        difficulty: One of "Beginner", "Intermediate", "Advanced"
        topics: List of topic tags
        estimated_time: Completion time in minutes
        prerequisites: List of required knowledge or completed modules
        repository: Relative path to the walkthrough directory
    """

    id: str
    title: str
    description: str
    difficulty: str
    topics: List[str]
    estimated_time: int
    prerequisites: List[str]
    repository: str


class WalkthroughRegistry:
    """
    Manages walkthrough discovery and metadata caching.

    Scans the walkthroughs directory for metadata.json files, validates them,
    and provides query methods for filtering and searching walkthroughs.
    """

    VALID_DIFFICULTIES = {"Beginner", "Intermediate", "Advanced"}

    def __init__(self, walkthroughs_dir: str = "walkthroughs"):
        """
        Initialize the registry and load walkthroughs.

        Args:
            walkthroughs_dir: Path to the walkthroughs directory
        """
        # Try to find walkthroughs directory relative to project root
        # Check if we're in backend/ subdirectory and adjust path accordingly
        walkthroughs_path = Path(walkthroughs_dir)

        if not walkthroughs_path.exists():
            # Try parent directory (for when running from backend/)
            parent_path = Path("..") / walkthroughs_dir
            if parent_path.exists():
                walkthroughs_path = parent_path

        self._walkthroughs_dir = walkthroughs_path
        self._cache: Dict[str, WalkthroughMetadata] = {}
        self._load_walkthroughs()

    def _load_walkthroughs(self) -> None:
        """
        Scan walkthroughs directory and load all valid metadata.
        Invalid walkthroughs are logged and skipped.

        Requirements: 3.1, 3.2
        """
        if not self._walkthroughs_dir.exists():
            logger.warning(
                f"Walkthroughs directory not found: {self._walkthroughs_dir}"
            )
            return

        for item in self._walkthroughs_dir.iterdir():
            if not item.is_dir():
                continue

            # Skip template directory
            if item.name == "template":
                continue

            metadata_file = item / "metadata.json"
            if not metadata_file.exists():
                logger.warning(f"Skipping {item.name}: metadata.json not found")
                continue

            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if self._validate_metadata(data):
                    walkthrough = WalkthroughMetadata(
                        id=data["id"],
                        title=data["title"],
                        description=data["description"],
                        difficulty=data["difficulty"],
                        topics=data["topics"],
                        estimated_time=data["estimatedTime"],
                        prerequisites=data["prerequisites"],
                        repository=data["repository"],
                    )
                    self._cache[walkthrough.id] = walkthrough
                    logger.info(f"Loaded walkthrough: {walkthrough.id}")
                else:
                    logger.warning(f"Skipping {item.name}: metadata validation failed")

            except json.JSONDecodeError as e:
                logger.warning(f"Skipping {item.name}: invalid JSON - {e}")
            except Exception as e:
                logger.warning(f"Skipping {item.name}: error loading metadata - {e}")

    def _validate_metadata(self, data: dict) -> bool:
        """
        Validate that metadata contains all required fields with correct types.

        Args:
            data: Metadata dictionary to validate

        Returns:
            True if valid, False otherwise

        Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6
        """
        required_fields = {
            "id": str,
            "title": str,
            "description": str,
            "difficulty": str,
            "topics": list,
            "estimatedTime": int,
            "prerequisites": list,
            "repository": str,
        }

        # Check all required fields are present
        for field, expected_type in required_fields.items():
            if field not in data:
                logger.warning(f"Validation failed: missing field '{field}'")
                return False

            if not isinstance(data[field], expected_type):
                logger.warning(f"Validation failed: field '{field}' has wrong type")
                return False

        # Validate difficulty is one of the allowed values
        if data["difficulty"] not in self.VALID_DIFFICULTIES:
            logger.warning(
                f"Validation failed: difficulty must be one of {self.VALID_DIFFICULTIES}"
            )
            return False

        # Validate topics is an array of strings
        if not all(isinstance(topic, str) for topic in data["topics"]):
            logger.warning(f"Validation failed: topics must be an array of strings")
            return False

        # Validate estimatedTime is positive
        if data["estimatedTime"] <= 0:
            logger.warning(f"Validation failed: estimatedTime must be positive")
            return False

        # Validate prerequisites is an array
        if not isinstance(data["prerequisites"], list):
            logger.warning(f"Validation failed: prerequisites must be an array")
            return False

        # Validate repository is a valid relative path
        if not data["repository"] or not isinstance(data["repository"], str):
            logger.warning(f"Validation failed: repository must be a valid string")
            return False

        return True

    def get_all(self) -> List[WalkthroughMetadata]:
        """
        Retrieve all walkthroughs.

        Returns:
            List of walkthrough metadata objects

        Requirements: 3.4
        """
        return list(self._cache.values())

    def get_by_id(self, walkthrough_id: str) -> Optional[WalkthroughMetadata]:
        """
        Retrieve a single walkthrough by ID.

        Args:
            walkthrough_id: Unique walkthrough identifier

        Returns:
            Walkthrough metadata or None if not found

        Requirements: 3.5
        """
        return self._cache.get(walkthrough_id)

    def filter_by_difficulty(self, difficulty: str) -> List[WalkthroughMetadata]:
        """
        Filter walkthroughs by difficulty level.

        Args:
            difficulty: One of "Beginner", "Intermediate", "Advanced"

        Returns:
            List of matching walkthroughs

        Requirements: 3.6
        """
        return [wt for wt in self._cache.values() if wt.difficulty == difficulty]

    def filter_by_topics(self, topics: List[str]) -> List[WalkthroughMetadata]:
        """
        Filter walkthroughs by topic tags.

        Args:
            topics: List of topic tags to match

        Returns:
            List of walkthroughs containing at least one matching topic

        Requirements: 3.7
        """
        return [
            wt
            for wt in self._cache.values()
            if any(topic in wt.topics for topic in topics)
        ]

    def search(self, query: str) -> List[WalkthroughMetadata]:
        """
        Search walkthroughs by keyword.

        Args:
            query: Search query (case-insensitive, partial matching)

        Returns:
            List of walkthroughs matching the query in title, description, or topics

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        query_lower = query.lower()
        results = []

        for wt in self._cache.values():
            # Search in title
            if query_lower in wt.title.lower():
                results.append(wt)
                continue

            # Search in description
            if query_lower in wt.description.lower():
                results.append(wt)
                continue

            # Search in topics
            if any(query_lower in topic.lower() for topic in wt.topics):
                results.append(wt)
                continue

        return results


# Global registry instance
_registry: Optional[WalkthroughRegistry] = None


def get_registry() -> WalkthroughRegistry:
    """
    Get or create the global walkthrough registry instance.

    Returns:
        WalkthroughRegistry instance

    Requirements: 3.8
    """
    global _registry
    if _registry is None:
        _registry = WalkthroughRegistry()
    return _registry
