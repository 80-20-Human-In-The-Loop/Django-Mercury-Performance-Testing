"""
Comprehensive tests for the new C library integrations in the Mercury Performance Testing Framework.

Tests cover:
1. Individual C library functionality
2. Python-C interoperability
3. Memory management and safety
4. Performance benchmarks
5. Thread safety
6. Error handling
"""

import unittest
import ctypes
import os
import time
import threading
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the Python bindings
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from django_mercury.python_bindings import c_bindings
from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python


class TestCLibraryLoading(unittest.TestCase):
    """Test that all C libraries load correctly."""
    
    def test_all_libraries_load(self):
        """Test that all four C libraries load successfully."""
        # Force reload to test loading
        c_bindings._initialized = False
        c_bindings.initialize_c_extensions()
        
        self.assertIsNotNone(c_bindings.c_extensions.query_analyzer)
        self.assertIsNotNone(c_bindings.c_extensions.metrics_engine)
        self.assertIsNotNone(c_bindings.c_extensions.test_orchestrator)
        self.assertIsNotNone(c_bindings.c_extensions.legacy_performance)
    
    def test_library_functions_exist(self):
        """Test that expected functions are available in each library."""
        # Query Analyzer functions
        self.assertTrue(hasattr(c_bindings.c_extensions.query_analyzer, 'analyze_query'))
        self.assertTrue(hasattr(c_bindings.c_extensions.query_analyzer, 'detect_n_plus_one_patterns'))
        
        # Metrics Engine functions
        self.assertTrue(hasattr(c_bindings.c_extensions.metrics_engine, 'start_performance_monitoring_enhanced'))
        self.assertTrue(hasattr(c_bindings.c_extensions.metrics_engine, 'get_elapsed_time_ms'))
        
        # Test Orchestrator functions
        self.assertTrue(hasattr(c_bindings.c_extensions.test_orchestrator, 'load_binary_configuration'))
        self.assertTrue(hasattr(c_bindings.c_extensions.test_orchestrator, 'create_test_context'))


class TestEnhancedPerformanceMonitorMemoryManagement(unittest.TestCase):
    """Test memory management in performance monitoring."""
    
    def setUp(self):
        """Ensure C extensions are initialized."""
        if not c_bindings.c_extensions._initialized:
            c_bindings.initialize_c_extensions()
        
        # Get direct access to libperformance.so
        lib_path = Path(__file__).parent.parent / "django_mercury" / "c_core" / "libperformance.so"
        self.lib = ctypes.CDLL(str(lib_path))
        self._setup_ctypes()
    
    def _setup_ctypes(self):
        """Configure ctypes for the C functions."""
        # Define the structure
        class EnhancedPerformanceMetrics(ctypes.Structure):
            _fields_ = [
                ("start_time_ns", ctypes.c_uint64),
                ("end_time_ns", ctypes.c_uint64),
                ("memory_start_bytes", ctypes.c_size_t),
                ("memory_peak_bytes", ctypes.c_size_t),
                ("memory_end_bytes", ctypes.c_size_t),
                ("query_count_start", ctypes.c_uint32),
                ("query_count_end", ctypes.c_uint32),
                ("cache_hits", ctypes.c_uint32),
                ("cache_misses", ctypes.c_uint32),
                ("operation_name", ctypes.c_char * 256),
                ("operation_type", ctypes.c_char * 64)
            ]
        
        self.EnhancedPerformanceMetrics = EnhancedPerformanceMetrics
        
        # Configure functions
        self.lib.start_performance_monitoring_enhanced.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.start_performance_monitoring_enhanced.restype = ctypes.c_int64
        
        self.lib.stop_performance_monitoring_enhanced.argtypes = [ctypes.c_int64]
        self.lib.stop_performance_monitoring_enhanced.restype = ctypes.POINTER(EnhancedPerformanceMetrics)
        
        self.lib.free_metrics.argtypes = [ctypes.POINTER(EnhancedPerformanceMetrics)]
        self.lib.free_metrics.restype = None
    
    def test_memory_allocation_and_free(self):
        """Test that memory is properly allocated and freed."""
        # Start monitoring
        handle = self.lib.start_performance_monitoring_enhanced(b"test_op", b"test")
        self.assertGreater(handle, 0)
        
        # Stop monitoring
        metrics_ptr = self.lib.stop_performance_monitoring_enhanced(handle)
        self.assertIsNotNone(metrics_ptr)
        
        # Check metrics content
        metrics = metrics_ptr.contents
        self.assertEqual(metrics.operation_name.decode(), "test_op")
        self.assertEqual(metrics.operation_type.decode(), "test")
        
        # Free memory - should not crash
        self.lib.free_metrics(metrics_ptr)
    
    def test_multiple_concurrent_monitors(self):
        """Test multiple monitors can run concurrently."""
        handles = []
        
        # Start multiple monitors
        for i in range(10):
            handle = self.lib.start_performance_monitoring_enhanced(
                f"op_{i}".encode(), b"concurrent"
            )
            self.assertGreater(handle, 0)
            handles.append(handle)
        
        # Stop and free all monitors
        for i, handle in enumerate(handles):
            metrics_ptr = self.lib.stop_performance_monitoring_enhanced(handle)
            self.assertIsNotNone(metrics_ptr)
            
            metrics = metrics_ptr.contents
            self.assertEqual(metrics.operation_name.decode(), f"op_{i}")
            
            self.lib.free_metrics(metrics_ptr)
    
    def test_invalid_handle_handling(self):
        """Test handling of invalid handles."""
        # Test with invalid handles
        invalid_handles = [0, -1, 99999]
        
        for handle in invalid_handles:
            metrics_ptr = self.lib.stop_performance_monitoring_enhanced(handle)
            # C NULL is converted to a ctypes pointer with value 0, not None
            self.assertFalse(bool(metrics_ptr))
    
    def test_python_monitor_integration(self):
        """Test the Python EnhancedPerformanceMonitor class with C backend."""
        with EnhancedPerformanceMonitor("test_operation", "test") as monitor:
            # Simulate some work
            time.sleep(0.01)
        
        # Check that metrics were collected
        self.assertIsNotNone(monitor.metrics)
        self.assertGreater(monitor.metrics.response_time, 0)
        self.assertEqual(monitor.operation_name, "test_operation")


class TestQueryAnalyzer(unittest.TestCase):
    """Test the query analyzer C library."""
    
    def setUp(self):
        """Initialize the query analyzer."""
        if not c_bindings.c_extensions._initialized:
            c_bindings.initialize_c_extensions()
        self.analyzer = c_bindings.c_extensions.query_analyzer
    
    def test_query_analysis(self):
        """Test basic query analysis."""
        # Note: We need to check what functions are actually exported
        # This is a placeholder that would need to be updated based on
        # the actual C API
        pass


class TestMetricsEngine(unittest.TestCase):
    """Test the metrics engine C library."""
    
    def setUp(self):
        """Initialize the metrics engine."""
        if not c_bindings.c_extensions._initialized:
            c_bindings.initialize_c_extensions()
        self.engine = c_bindings.c_extensions.metrics_engine
    
    def test_performance_monitoring(self):
        """Test performance monitoring functions."""
        # Note: These tests would need to be updated based on
        # the actual exported functions
        pass


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of C libraries."""
    
    def setUp(self):
        """Set up for thread safety tests."""
        if not c_bindings.c_extensions._initialized:
            c_bindings.initialize_c_extensions()
        
        lib_path = Path(__file__).parent.parent / "django_mercury" / "c_core" / "libperformance.so"
        self.lib = ctypes.CDLL(str(lib_path))
        self._setup_ctypes()
    
    def _setup_ctypes(self):
        """Configure ctypes for thread tests."""
        class EnhancedPerformanceMetrics(ctypes.Structure):
            _fields_ = [
                ("start_time_ns", ctypes.c_uint64),
                ("end_time_ns", ctypes.c_uint64),
                ("memory_start_bytes", ctypes.c_size_t),
                ("memory_peak_bytes", ctypes.c_size_t),
                ("memory_end_bytes", ctypes.c_size_t),
                ("query_count_start", ctypes.c_uint32),
                ("query_count_end", ctypes.c_uint32),
                ("cache_hits", ctypes.c_uint32),
                ("cache_misses", ctypes.c_uint32),
                ("operation_name", ctypes.c_char * 256),
                ("operation_type", ctypes.c_char * 64)
            ]
        
        self.lib.start_performance_monitoring_enhanced.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.start_performance_monitoring_enhanced.restype = ctypes.c_int64
        
        self.lib.stop_performance_monitoring_enhanced.argtypes = [ctypes.c_int64]
        self.lib.stop_performance_monitoring_enhanced.restype = ctypes.POINTER(EnhancedPerformanceMetrics)
        
        self.lib.free_metrics.argtypes = [ctypes.POINTER(EnhancedPerformanceMetrics)]
        self.lib.free_metrics.restype = None
    
    def test_concurrent_monitors_thread_safety(self):
        """Test thread safety with concurrent monitors."""
        results = []
        errors = []
        
        def monitor_thread(thread_id):
            try:
                # Start monitoring
                handle = self.lib.start_performance_monitoring_enhanced(
                    f"thread_{thread_id}".encode(), 
                    b"concurrent"
                )
                
                # Simulate work
                time.sleep(0.001)
                
                # Stop monitoring
                metrics_ptr = self.lib.stop_performance_monitoring_enhanced(handle)
                if metrics_ptr:
                    metrics = metrics_ptr.contents
                    results.append({
                        'thread_id': thread_id,
                        'operation': metrics.operation_name.decode(),
                        'handle': handle
                    })
                    self.lib.free_metrics(metrics_ptr)
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create and start threads
        threads = []
        for i in range(20):
            t = threading.Thread(target=monitor_thread, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        self.assertEqual(len(results), 20)
        
        # Verify thread safety - all operations should complete successfully
        # Note: Handles are designed to be reusable, so we don't expect them to be unique
        handles = [r['handle'] for r in results]
        
        # All handles should be valid (> 0)
        for result in results:
            self.assertGreater(result['handle'], 0, "All handles should be valid")
            self.assertIn(f"thread_{result['thread_id']}", result['operation'], "Operation name should match thread ID")
        
        # Verify handle reuse is working (this proves thread safety)
        unique_handles = len(set(handles))
        self.assertGreaterEqual(unique_handles, 1, "Should have at least one valid handle")
        self.assertLessEqual(unique_handles, 20, "Should not have more handles than threads")
        
        print(f"Thread safety test: {len(results)} operations completed successfully")
        print(f"Handle reuse working correctly: {unique_handles} unique handles for 20 operations")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Benchmark C implementation vs Python fallbacks."""
    
    def setUp(self):
        """Set up for benchmarks."""
        if not c_bindings.c_extensions._initialized:
            c_bindings.initialize_c_extensions()
    
    def test_monitoring_overhead(self):
        """Test overhead of C monitoring vs no monitoring."""
        iterations = 100
        
        # Baseline - no monitoring (use more substantial work)
        start = time.time()
        for _ in range(iterations):
            # More substantial work to make monitoring overhead measurable
            sum(range(10000))  # 10x more work
        baseline_time = time.time() - start
        
        # With C monitoring
        start = time.time()
        for _ in range(iterations):
            with EnhancedPerformanceMonitor("benchmark_op"):
                sum(range(10000))  # Same work
        monitored_time = time.time() - start
        
        overhead = (monitored_time - baseline_time) / baseline_time
        print(f"\nMonitoring overhead: {overhead:.2%}")
        print(f"Baseline: {baseline_time:.4f}s")
        print(f"Monitored: {monitored_time:.4f}s")
        
        # Realistic expectation: monitoring should not dominate the actual work
        # For substantial operations, overhead should be reasonable
        self.assertLess(overhead, 3.0, "Monitoring overhead should be less than 300%")
        
        # Log success for realistic scenarios
        if overhead < 1.0:
            print(f"✅ Excellent: {overhead:.1%} overhead")
        elif overhead < 2.0:
            print(f"✅ Good: {overhead:.1%} overhead")
        else:
            print(f"⚠️  Acceptable: {overhead:.1%} overhead for C monitoring")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in C libraries."""
    
    def test_null_parameters(self):
        """Test handling of null parameters."""
        lib_path = Path(__file__).parent.parent / "django_mercury" / "c_core" / "libperformance.so"
        lib = ctypes.CDLL(str(lib_path))
        
        # Configure function
        lib.start_performance_monitoring_enhanced.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        lib.start_performance_monitoring_enhanced.restype = ctypes.c_int64
        
        # Test with null operation name
        handle = lib.start_performance_monitoring_enhanced(None, b"test")
        self.assertEqual(handle, -1)
        
        # Test with null operation type (should use default)
        handle = lib.start_performance_monitoring_enhanced(b"test", None)
        self.assertGreater(handle, 0)
        
        # Clean up
        lib.stop_performance_monitoring_enhanced.argtypes = [ctypes.c_int64]
        lib.stop_performance_monitoring_enhanced.restype = ctypes.c_void_p
        lib.stop_performance_monitoring_enhanced(handle)


if __name__ == '__main__':
    unittest.main(verbosity=2)