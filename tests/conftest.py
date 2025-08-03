"""
Pytest configuration file for test suite.
Controls test environment setup and logging configuration.
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest environment."""
    # Suppress verbose C extension loading messages during tests
    # Only show warnings and errors, not INFO messages
    logging.getLogger('django_mercury.python_bindings.c_bindings').setLevel(logging.WARNING)
    
    # Also suppress validation messages unless they're errors
    logging.getLogger('performance_testing.validation').setLevel(logging.ERROR)
    
    # Set environment variable to reduce verbosity
    os.environ['MERCURY_TEST_MODE'] = '1'


def pytest_unconfigure(config):
    """Clean up after pytest."""
    # Reset logging levels
    logging.getLogger('django_mercury.python_bindings.c_bindings').setLevel(logging.INFO)
    logging.getLogger('performance_testing.validation').setLevel(logging.INFO)
    
    # Clean up environment
    os.environ.pop('MERCURY_TEST_MODE', None)


# Fixtures can be added here if needed
import pytest

@pytest.fixture(autouse=True)
def reset_c_extensions():
    """Reset C extensions state between tests to prevent interference."""
    yield
    # Cleanup happens after test
    from django_mercury.python_bindings import c_bindings
    if hasattr(c_bindings.c_extensions, '_initialized'):
        # Don't actually cleanup during tests, just reset the flag if needed
        pass