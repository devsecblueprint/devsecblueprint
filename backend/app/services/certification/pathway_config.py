"""Hardcoded pathway definitions for the DSB Certification Program.

Learning requirements are dynamically loaded from the frontend's modules.json
at module import time. This keeps requirements in sync with content changes
without manual maintenance.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try multiple locations for modules.json
_MODULES_JSON_PATHS = [
    # Development: relative to project root
    Path(__file__).resolve().parents[4] / "frontend" / "lib" / "data" / "modules.json",
    # Docker/deployed: copied to app/data/modules.json
    Path(__file__).resolve().parents[2] / "data" / "modules.json",
]

# Capstone content IDs to EXCLUDE from learning requirements
# (capstone completion is handled separately by the review pass flow)
_CAPSTONE_CONTENT_IDS = frozenset(
    {
        "devsecops-capstone",
        "cloud_security_development-capstone",
    }
)

# Mapping from pathway_id to the learningPath value in modules.json
_PATHWAY_TO_LEARNING_PATH: dict[str, str] = {
    "devsecops-engineering": "DevSecOps",
    "cloud-security-engineering": "Cloud Security Development",
}


def _find_modules_json() -> Path | None:
    """Find modules.json from known locations.

    Returns:
        Path to modules.json or None if not found.
    """
    for path in _MODULES_JSON_PATHS:
        if path.exists():
            return path
    return None


def _load_learning_requirements() -> dict[str, list[str]]:
    """Load learning requirements from modules.json.

    Reads the frontend modules.json, groups page IDs by learningPath,
    and returns a mapping of pathway_id -> list of required content_ids.

    Capstone pages are excluded (handled separately by the review pass).

    Returns:
        Dict mapping pathway_id to list of required page (content) IDs.
    """
    requirements: dict[str, list[str]] = {
        "devsecops-engineering": [],
        "cloud-security-engineering": [],
        "dsb-champion": [],
    }

    modules_path = _find_modules_json()
    if modules_path is None:
        logger.warning(
            "modules.json not found at any known location; learning requirements will be empty",
        )
        return requirements

    try:
        with open(modules_path, encoding="utf-8") as f:
            modules = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load modules.json: %s", e)
        return requirements

    for module in modules:
        learning_path = module.get("learningPath", "")
        pages = module.get("pages", [])

        # Find which pathway this learningPath maps to
        for pathway_id, lp_name in _PATHWAY_TO_LEARNING_PATH.items():
            if learning_path == lp_name:
                for page in pages:
                    page_id = page.get("id", "")
                    if page_id and page_id not in _CAPSTONE_CONTENT_IDS:
                        requirements[pathway_id].append(page_id)

    # Also populate DSB Champion with ALL pages from ALL learning paths
    all_page_ids: list[str] = []
    for module in modules:
        pages = module.get("pages", [])
        for page in pages:
            page_id = page.get("id", "")
            if page_id and page_id not in _CAPSTONE_CONTENT_IDS:
                all_page_ids.append(page_id)
    requirements["dsb-champion"] = all_page_ids

    logger.info(
        "Loaded learning requirements: devsecops=%d pages, cloud-security=%d pages, dsb-champion=%d pages (all modules)",
        len(requirements["devsecops-engineering"]),
        len(requirements["cloud-security-engineering"]),
        len(requirements["dsb-champion"]),
    )

    return requirements


# Load requirements once at module import time (cached for process lifetime)
_LEARNING_REQUIREMENTS = _load_learning_requirements()


# Pathway definitions
PATHWAY_DEFINITIONS: dict[str, dict[str, Any]] = {
    "devsecops-engineering": {
        "pathway_id": "devsecops-engineering",
        "display_name": "DevSecOps Engineering Pathway",
        "description": "has successfully completed the requirements for this certification and has demonstrated the knowledge and skills to achieve this credential.",
        "pathway_code": "DSEP",
        "version": "2025.1",
        "capstone_content_id": "devsecops-capstone",
        "learning_requirements": _LEARNING_REQUIREMENTS["devsecops-engineering"],
        "is_active": True,
    },
    "cloud-security-engineering": {
        "pathway_id": "cloud-security-engineering",
        "display_name": "Cloud Security Engineering Pathway",
        "description": "has successfully completed the requirements for this certification and has demonstrated the knowledge and skills to achieve this credential.",
        "pathway_code": "CSEP",
        "version": "2025.1",
        "capstone_content_id": "cloud_security_development-capstone",
        "learning_requirements": _LEARNING_REQUIREMENTS["cloud-security-engineering"],
        "is_active": True,
    },
    "dsb-champion": {
        "pathway_id": "dsb-champion",
        "display_name": "DSB Champion",
        "description": "has successfully completed all required learning content across The DevSec Blueprint curriculum and has demonstrated commitment to continuous technical and professional development.",
        "pathway_code": "DSBC",
        "version": "2025.1",
        "capstone_content_id": "",
        "learning_requirements": _LEARNING_REQUIREMENTS["dsb-champion"],
        "is_active": True,
    },
}


def get_pathway(pathway_id: str) -> dict[str, Any] | None:
    """Get a pathway definition by ID.

    Returns:
        Pathway dict or None if not found.
    """
    return PATHWAY_DEFINITIONS.get(pathway_id)


def get_all_pathways() -> list[dict[str, Any]]:
    """Get all active pathway definitions.

    Returns:
        List of pathway dicts.
    """
    return [p for p in PATHWAY_DEFINITIONS.values() if p.get("is_active")]


def get_pathway_code(pathway_id: str) -> str | None:
    """Get the pathway code (e.g., 'DSEP') for a pathway ID.

    Returns:
        Pathway code string or None if not found.
    """
    pathway = PATHWAY_DEFINITIONS.get(pathway_id)
    return pathway["pathway_code"] if pathway else None
