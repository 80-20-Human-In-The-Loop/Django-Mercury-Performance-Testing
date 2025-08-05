"""
Smart loader for Django Mercury implementations.

This module automatically detects and loads the best available implementation
(C extensions or pure Python) based on what's available in the environment.
"""

import os
import sys
import warnings
from typing import Type, Any, Optional


# Environment variable to force pure Python implementation
FORCE_PURE_PYTHON = os.environ.get("DJANGO_MERCURY_PURE_PYTHON", "").lower() in ("1", "true", "yes")

# Track what implementation we're using
IMPLEMENTATION_TYPE = None
C_EXTENSIONS_AVAILABLE = False


def _try_import_c_extensions():
    """
    Try to import C extensions and return status.

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # On Windows, ensure DLLs can be loaded
        if sys.platform == 'win32':
            import os
            # Add the package directory to DLL search path
            package_dir = os.path.dirname(os.path.dirname(__file__))
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(package_dir)
        
        # Try importing C extensions - we consolidated to metrics
        import django_mercury._c_metrics
        import django_mercury._c_analyzer
        import django_mercury._c_orchestrator

        return True, None
    except ImportError as e:
        return False, str(e)


def _show_performance_warning():
    """Show warning about using pure Python implementation."""
    warning_msg = (
        "Django Mercury: C extensions not available. Using pure Python implementation.\n"
        "Performance monitoring will work but with higher overhead.\n"
        "For optimal performance:\n"
    )

    if sys.platform == "linux":
        warning_msg += (
            "  Ubuntu/Debian: sudo apt-get install python3-dev build-essential\n"
            "  RHEL/CentOS: sudo yum install python3-devel gcc\n"
            "  Then reinstall: pip install --force-reinstall django-mercury-performance\n"
        )
    elif sys.platform == "darwin":
        warning_msg += (
            "  macOS: xcode-select --install\n"
            "  Then reinstall: pip install --force-reinstall django-mercury-performance\n"
        )
    elif sys.platform == "win32":
        warning_msg += (
            "  Windows: Install Visual Studio Build Tools\n"
            "  https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio\n"
            "  Then reinstall: pip install --force-reinstall django-mercury-performance\n"
        )
    else:
        warning_msg += (
            "  Install a C compiler for your platform and reinstall django-mercury-performance\n"
        )

    warning_msg += "\n" "To suppress this warning, set: DJANGO_MERCURY_PURE_PYTHON=1\n" "=" * 60

    warnings.warn(warning_msg, RuntimeWarning, stacklevel=3)


class ImplementationLoader:
    """Loader that selects the best available implementation."""

    def __init__(self):
        self._performance_monitor_class = None
        self._metrics_engine_class = None
        self._query_analyzer_class = None
        self._test_orchestrator_class = None
        self._loaded = False

    def load(self):
        """Load the appropriate implementation."""
        global IMPLEMENTATION_TYPE, C_EXTENSIONS_AVAILABLE

        if self._loaded:
            return

        if FORCE_PURE_PYTHON:
            # User explicitly wants pure Python
            IMPLEMENTATION_TYPE = "pure_python_forced"
            self._load_pure_python()
        else:
            # Try C extensions first
            c_available, error = _try_import_c_extensions()

            if c_available:
                IMPLEMENTATION_TYPE = "c_extensions"
                C_EXTENSIONS_AVAILABLE = True
                self._load_c_extensions()
            else:
                IMPLEMENTATION_TYPE = "pure_python_fallback"
                C_EXTENSIONS_AVAILABLE = False
                self._load_pure_python()

                # Show warning unless explicitly suppressed
                if not os.environ.get("DJANGO_MERCURY_SUPPRESS_WARNING"):
                    _show_performance_warning()

        self._loaded = True

    def _load_c_extensions(self):
        """Load C extension implementations."""
        try:
            # On Windows, ensure DLLs can be loaded
            if sys.platform == 'win32':
                import os
                package_dir = os.path.dirname(os.path.dirname(__file__))
                if hasattr(os, 'add_dll_directory'):
                    os.add_dll_directory(package_dir)
            
            # Test that C extensions can be imported (consolidated to metrics)
            import django_mercury._c_metrics
            import django_mercury._c_analyzer
            import django_mercury._c_orchestrator

            # Use wrapper classes that provide Python interface
            from .c_wrappers import (
                CPerformanceMonitor,
                CMetricsEngine,
                CQueryAnalyzer,
                CTestOrchestrator,
            )

            # Performance monitor now uses metrics engine internally
            self._performance_monitor_class = CPerformanceMonitor
            self._metrics_engine_class = CMetricsEngine
            self._query_analyzer_class = CQueryAnalyzer
            self._test_orchestrator_class = CTestOrchestrator

        except ImportError as e:
            # C extensions not available, fall back to Python
            self._load_pure_python()

    def _load_pure_python(self):
        """Load pure Python implementations."""
        from .pure_python import (
            PythonPerformanceMonitor,
            PythonMetricsEngine,
            PythonQueryAnalyzer,
            PythonTestOrchestrator,
        )

        self._performance_monitor_class = PythonPerformanceMonitor
        self._metrics_engine_class = PythonMetricsEngine
        self._query_analyzer_class = PythonQueryAnalyzer
        self._test_orchestrator_class = PythonTestOrchestrator

    @property
    def PerformanceMonitor(self) -> Type:
        """Get the PerformanceMonitor class."""
        if not self._loaded:
            self.load()
        return self._performance_monitor_class

    @property
    def MetricsEngine(self) -> Type:
        """Get the MetricsEngine class."""
        if not self._loaded:
            self.load()
        return self._metrics_engine_class

    @property
    def QueryAnalyzer(self) -> Type:
        """Get the QueryAnalyzer class."""
        if not self._loaded:
            self.load()
        return self._query_analyzer_class

    @property
    def TestOrchestrator(self) -> Type:
        """Get the TestOrchestrator class."""
        if not self._loaded:
            self.load()
        return self._test_orchestrator_class

    def get_implementation_info(self) -> dict:
        """
        Get information about the current implementation.

        Returns:
            Dictionary with implementation details
        """
        if not self._loaded:
            self.load()

        return {
            "type": IMPLEMENTATION_TYPE,
            "c_extensions_available": C_EXTENSIONS_AVAILABLE,
            "forced_pure_python": FORCE_PURE_PYTHON,
            "platform": sys.platform,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }


# Global loader instance
_loader = ImplementationLoader()


def get_performance_monitor():
    """
    Get the best available PerformanceMonitor implementation.

    Returns:
        PerformanceMonitor class (C or Python implementation)
    """
    return _loader.PerformanceMonitor


def get_metrics_engine():
    """
    Get the best available MetricsEngine implementation.

    Returns:
        MetricsEngine class (C or Python implementation)
    """
    return _loader.MetricsEngine


def get_query_analyzer():
    """
    Get the best available QueryAnalyzer implementation.

    Returns:
        QueryAnalyzer class (C or Python implementation)
    """
    return _loader.QueryAnalyzer


def get_test_orchestrator():
    """
    Get the best available TestOrchestrator implementation.

    Returns:
        TestOrchestrator class (C or Python implementation)
    """
    return _loader.TestOrchestrator


def get_implementation_info():
    """
    Get information about the current implementation.

    Returns:
        Dictionary with implementation details
    """
    return _loader.get_implementation_info()


# Convenience exports - these will be the actual classes
PerformanceMonitor = property(lambda self: _loader.PerformanceMonitor)
MetricsEngine = property(lambda self: _loader.MetricsEngine)
QueryAnalyzer = property(lambda self: _loader.QueryAnalyzer)
TestOrchestrator = property(lambda self: _loader.TestOrchestrator)


def check_c_extensions():
    """
    Check if C extensions are available and working.

    Returns:
        Tuple of (available: bool, details: dict)
    """
    details = get_implementation_info()
    
    # First check if we're in a fallback mode
    if details.get("type") in ["pure_python_fallback", "pure_python_forced"]:
        details["functional"] = False
        details["error"] = f"Running in {details['type']} mode"
        return False, details
    
    available = details["c_extensions_available"]

    # Try to test the extensions
    if available:
        try:
            # Try to import the actual C modules
            import django_mercury._c_metrics
            import django_mercury._c_analyzer
            import django_mercury._c_orchestrator
            
            # Create instances to verify they work
            monitor = get_performance_monitor()()
            engine = get_metrics_engine()()
            analyzer = get_query_analyzer()()
            orchestrator = get_test_orchestrator()()

            # Basic functionality test
            monitor.start_monitoring()
            monitor.stop_monitoring()

            details["functional"] = True
        except ImportError as e:
            details["functional"] = False
            details["error"] = f"C extension import failed: {str(e)}"
            available = False
        except Exception as e:
            details["functional"] = False
            details["error"] = str(e)
            available = False
    else:
        details["functional"] = False
        if "error" not in details:
            details["error"] = "C extensions not available"

    return available, details


# Auto-load on import if in eager mode
if os.environ.get("DJANGO_MERCURY_EAGER_LOAD", "").lower() in ("1", "true", "yes"):
    _loader.load()
