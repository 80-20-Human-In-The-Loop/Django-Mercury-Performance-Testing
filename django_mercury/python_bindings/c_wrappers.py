"""
Wrapper classes for C extensions to provide Python-compatible interface.

Since the C extensions are raw C libraries, we need to wrap them
to provide the same interface as the pure Python implementations.
"""

import ctypes
import os
from typing import Dict, Any, List


def load_c_library(name: str):
    """
    Load a C extension library.

    Args:
        name: Name of the C extension (e.g., '_c_performance')

    Returns:
        Loaded ctypes library or None if not found
    """
    # Get the directory where this module is located
    module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Try different library naming conventions
    lib_patterns = [
        f"{name}.cpython-*.so",  # Linux/Unix
        f"{name}.*.pyd",  # Windows
        f"{name}.*.dylib",  # macOS
        f"{name}.so",  # Generic
    ]

    import glob

    for pattern in lib_patterns:
        libs = glob.glob(os.path.join(module_dir, pattern))
        if libs:
            try:
                return ctypes.CDLL(libs[0])
            except Exception:
                pass

    return None


class CPerformanceMonitor:
    """
    Wrapper for C performance monitor extension.

    Uses the actual C implementation when available, falls back to Python otherwise.
    """

    def __init__(self):
        try:
            # Try to use the actual C implementation
            import django_mercury._c_performance as c_performance
            self._monitor = c_performance.PerformanceMonitor()
            self._using_fallback = False
        except (ImportError, AttributeError) as e:
            # Fall back to pure Python implementation
            from .pure_python import PythonPerformanceMonitor
            self._monitor = PythonPerformanceMonitor()
            self._using_fallback = True

    def start_monitoring(self):
        return self._monitor.start_monitoring()

    def stop_monitoring(self):
        return self._monitor.stop_monitoring()

    def track_query(self, sql: str, duration: float = 0.0):
        return self._monitor.track_query(sql, duration)

    def track_cache(self, hit: bool):
        return self._monitor.track_cache(hit)

    def get_metrics(self) -> Dict[str, Any]:
        return self._monitor.get_metrics()

    def reset(self):
        return self._monitor.reset()
    
    @property
    def metrics(self):
        """Access to underlying metrics for compatibility."""
        return self._monitor.metrics


class CMetricsEngine:
    """
    Wrapper for C metrics engine extension.

    Provides the same interface as PythonMetricsEngine.
    """

    def __init__(self):
        # Import the actual C extension
        import django_mercury._c_metrics as c_metrics

        self._engine = c_metrics.MetricsEngine()

    def add_metrics(self, metrics: Dict[str, Any]):
        return self._engine.add_metrics(metrics)

    def calculate_statistics(self) -> Dict[str, Any]:
        return self._engine.calculate_statistics()

    def detect_n_plus_one(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._engine.detect_n_plus_one(queries)


class CQueryAnalyzer:
    """
    Wrapper for C query analyzer extension.

    Provides the same interface as PythonQueryAnalyzer.
    """

    def __init__(self):
        # Import the actual C extension
        import django_mercury._c_analyzer as c_analyzer

        self._analyzer = c_analyzer.QueryAnalyzer()

    def analyze_query(self, sql: str) -> Dict[str, Any]:
        return self._analyzer.analyze_query(sql)


class CTestOrchestrator:
    """
    Wrapper for C test orchestrator extension.

    Provides the same interface as PythonTestOrchestrator.
    """

    def __init__(self):
        # Import the actual C extension
        import django_mercury._c_orchestrator as c_orchestrator

        self._orchestrator = c_orchestrator.TestOrchestrator()

    def start_test(self, test_name: str):
        return self._orchestrator.start_test(test_name)

    def end_test(self, test_name: str, status: str = "passed") -> Dict[str, Any]:
        return self._orchestrator.end_test(test_name, status)

    def get_summary(self) -> Dict[str, Any]:
        return self._orchestrator.get_summary()


# Aliases for compatibility
PerformanceMonitor = CPerformanceMonitor
MetricsEngine = CMetricsEngine
QueryAnalyzer = CQueryAnalyzer
TestOrchestrator = CTestOrchestrator
