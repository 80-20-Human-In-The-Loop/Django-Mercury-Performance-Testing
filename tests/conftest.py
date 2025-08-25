"""
Pytest configuration for pure Python Django Mercury testing.

Controls test environment setup and logging configuration.

NOTE: Main testing is done via test_runner.py. This conftest.py is for
individual pytest debugging when needed.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest environment."""
    # Set environment variable to reduce verbosity during tests
    os.environ["MERCURY_TEST_MODE"] = "1"


def pytest_unconfigure(config):
    """Clean up after pytest."""
    # Clean up environment
    os.environ.pop("MERCURY_TEST_MODE", None)
