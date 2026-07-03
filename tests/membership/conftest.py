"""
Pytest configuration for membership tests.

Adds backend/membership to sys.path so that tests can import modules
using their original bare paths (e.g., `from handlers.sync_handlers import ...`).
"""

import os
import sys

# Add backend/membership directory to Python path for bare imports
membership_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "backend", "membership"
)
sys.path.insert(0, os.path.abspath(membership_dir))
