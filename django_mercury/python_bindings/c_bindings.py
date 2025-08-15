"""
Pure Python Implementation Compatibility Module

This module provides compatibility for the pure Python implementation
of Django Mercury Performance Testing Framework.

Django Mercury is now a pure Python package with no compiled extensions.
This provides better cross-platform compatibility and easier debugging.

Author: EduLite Performance Team
Version: 3.0.0 (Pure Python)
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)

# Pure Python implementation flags
HAS_C_EXTENSIONS = False
C_EXTENSIONS_AVAILABLE = False


class MockCExtensions:
    """Mock object that provides None for all C extension attributes."""
    
    def __init__(self):
        self.query_analyzer = None
        self.metrics_engine = None
        self.test_orchestrator = None
        self.performance_monitor = None
    
    def __bool__(self):
        """Always returns False to indicate no C extensions."""
        return False


# Create the mock c_extensions object for compatibility
c_extensions = MockCExtensions()


def initialize_pure_python():
    """Initialize pure Python implementation (compatibility function)."""
    logger.debug("Django Mercury running in pure Python mode")
    return True


def get_implementation_info():
    """Get information about the current implementation."""
    return {
        "implementation": "pure_python",
        "version": "3.0.0",
        "performance_mode": "standard",
        "cross_platform": True
    }


def are_c_extensions_available():
    """Check if C extensions are available (always False now)."""
    return False


def is_pure_python_mode():
    """Check if running in pure Python mode (always True now)."""
    return True