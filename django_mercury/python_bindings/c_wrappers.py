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
    
    Provides the same interface as PythonPerformanceMonitor.
    """
    
    def __init__(self):
        # For now, we'll use the pure Python implementation
        # until we have proper Python C API bindings
        from .pure_python import PythonPerformanceMonitor
        self._impl = PythonPerformanceMonitor()
    
    def start_monitoring(self):
        return self._impl.start_monitoring()
    
    def stop_monitoring(self):
        return self._impl.stop_monitoring()
    
    def track_query(self, sql: str, duration: float = 0.0):
        return self._impl.track_query(sql, duration)
    
    def track_cache(self, hit: bool):
        return self._impl.track_cache(hit)
    
    def get_metrics(self) -> Dict[str, Any]:
        metrics = self._impl.get_metrics()
        metrics['implementation'] = 'c_extension_wrapper'
        return metrics
    
    def reset(self):
        return self._impl.reset()


class CMetricsEngine:
    """
    Wrapper for C metrics engine extension.
    
    Provides the same interface as PythonMetricsEngine.
    """
    
    def __init__(self):
        # For now, we'll use the pure Python implementation
        from .pure_python import PythonMetricsEngine
        self._impl = PythonMetricsEngine()
    
    def add_metrics(self, metrics: Dict[str, Any]):
        return self._impl.add_metrics(metrics)
    
    def calculate_statistics(self) -> Dict[str, Any]:
        stats = self._impl.calculate_statistics()
        stats['implementation'] = 'c_extension_wrapper'
        return stats
    
    def detect_n_plus_one(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = self._impl.detect_n_plus_one(queries)
        result['implementation'] = 'c_extension_wrapper'
        return result


class CQueryAnalyzer:
    """
    Wrapper for C query analyzer extension.
    
    Provides the same interface as PythonQueryAnalyzer.
    """
    
    def __init__(self):
        # For now, we'll use the pure Python implementation
        from .pure_python import PythonQueryAnalyzer
        self._impl = PythonQueryAnalyzer()
    
    def analyze_query(self, sql: str) -> Dict[str, Any]:
        analysis = self._impl.analyze_query(sql)
        analysis['implementation'] = 'c_extension_wrapper'
        return analysis


class CTestOrchestrator:
    """
    Wrapper for C test orchestrator extension.
    
    Provides the same interface as PythonTestOrchestrator.
    """
    
    def __init__(self):
        # For now, we'll use the pure Python implementation
        from .pure_python import PythonTestOrchestrator
        self._impl = PythonTestOrchestrator()
    
    def start_test(self, test_name: str):
        return self._impl.start_test(test_name)
    
    def end_test(self, test_name: str, status: str = 'passed') -> Dict[str, Any]:
        result = self._impl.end_test(test_name, status)
        if result:
            result['implementation'] = 'c_extension_wrapper'
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        summary = self._impl.get_summary()
        summary['implementation'] = 'c_extension_wrapper'
        return summary


# Aliases for compatibility
PerformanceMonitor = CPerformanceMonitor
MetricsEngine = CMetricsEngine
QueryAnalyzer = CQueryAnalyzer
TestOrchestrator = CTestOrchestrator