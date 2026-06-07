"""
Pytest Configuration for ClearMind Tests

Provides shared fixtures and configuration for the test suite.
"""

import os
import sys
import pytest

# Ensure backend is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set test environment variables before any app imports
os.environ.setdefault("GOOGLE_API_KEY", "test_key_for_ci")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DEBUG", "false")
