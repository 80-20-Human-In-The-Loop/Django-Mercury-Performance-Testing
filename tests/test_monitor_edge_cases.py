"""
Edge case tests for monitor.py to improve coverage.
Tests error handling, fallback scenarios, and boundary conditions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import ctypes
from pathlib import Path

from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python,
    monitor_django_view,
    monitor_django_model,
    monitor_serializer
)


class TestMonitorEdgeCases(unittest.TestCase):
    """Test edge cases and error paths in monitor.py"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
        self.patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_with_c_library_failure(self, mock_lib):
        """Test monitor behavior when C library operations fail."""
        # Make C library calls fail
        mock_lib.start_performance_monitoring_enhanced.return_value = -1
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Should raise RuntimeError when starting fails
        with self.assertRaises(RuntimeError) as context:
            with monitor:
                pass
        
        self.assertIn("Failed to start performance monitoring", str(context.exception))
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_with_null_metrics_returned(self, mock_lib):
        """Test handling when C library returns NULL metrics."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        mock_lib.stop_performance_monitoring_enhanced.return_value = None
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        with self.assertRaises(RuntimeError) as context:
            with monitor:
                pass
        
        self.assertIn("Failed to get performance metrics", str(context.exception))
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_metrics_with_invalid_operation_type(self, mock_lib):
        """Test metrics creation with invalid operation type bytes."""
        # Create mock C metrics with invalid bytes
        mock_c_metrics = MagicMock()
        mock_c_metrics.contents.operation_type = b'\xff\xfe\xfd'  # Invalid UTF-8
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 2000000000
        mock_c_metrics.contents.start_time_ns = 1000000000
        mock_c_metrics.contents.memory_end_bytes = 200000000
        mock_c_metrics.contents.memory_start_bytes = 100000000
        mock_c_metrics.contents.query_count_end = 10
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 5
        mock_c_metrics.contents.cache_misses = 2
        
        # Test that it handles decode errors gracefully
        metrics = EnhancedPerformanceMetrics_Python(mock_c_metrics, "test_op", None)
        self.assertEqual(metrics.operation_type, "unknown")  # Should fall back to "unknown"
    
    def test_monitor_educational_guidance_edge_cases(self):
        """Test educational guidance with various edge cases."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test with None context
        monitor.enable_educational_guidance(None)
        self.assertTrue(monitor._educational_guidance)
        
        # Test with empty dict context
        monitor.enable_educational_guidance({})
        self.assertTrue(monitor._educational_guidance)
        
        # Test with partial context
        monitor.enable_educational_guidance({"view_type": "list"})
        self.assertEqual(monitor._operation_context["view_type"], "list")
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_memory_calculations_edge_cases(self, mock_lib):
        """Test edge cases in memory calculations."""
        # Set up mock C metrics with edge case values
        mock_c_metrics = MagicMock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 1000000000
        mock_c_metrics.contents.start_time_ns = 1000000000  # Same as end (0 duration)
        mock_c_metrics.contents.memory_end_bytes = 100000000
        mock_c_metrics.contents.memory_start_bytes = 200000000  # End < Start (negative)
        mock_c_metrics.contents.query_count_end = 0
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 0
        mock_c_metrics.contents.cache_misses = 0  # No cache operations
        
        metrics = EnhancedPerformanceMetrics_Python(mock_c_metrics, "test_op", None)
        
        # Should handle edge cases gracefully
        self.assertEqual(metrics.response_time, 0.0)  # 0 duration
        self.assertEqual(metrics.memory_overhead, 0)  # Negative clamped to 0
        self.assertEqual(metrics.cache_hit_ratio, 0.0)  # No cache operations
    
    @patch('django_mercury.python_bindings.monitor.DjangoQueryTracker', None)
    @patch('django_mercury.python_bindings.monitor.DjangoCacheTracker', None)
    def test_monitor_without_django_components(self):
        """Test monitor when Django components are not available."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Should not crash when enabling Django hooks
        monitor.enable_django_hooks()
        self.assertFalse(monitor._django_hooks_active)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_exception_during_exit(self, mock_lib):
        """Test exception handling during context manager exit."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        
        # Make stop monitoring raise an exception
        mock_lib.stop_performance_monitoring_enhanced.side_effect = Exception("C library error")
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Should handle the exception and re-raise as RuntimeError
        with self.assertRaises(RuntimeError):
            with monitor:
                pass
    
    def test_monitor_factory_functions(self):
        """Test the factory functions for creating monitors."""
        # Test monitor_django_view
        with monitor_django_view("test_view") as monitor:
            self.assertEqual(monitor.operation_name, "test_view")
            self.assertEqual(monitor.operation_type, "view")
        
        # Test monitor_django_model
        with monitor_django_model("test_model") as monitor:
            self.assertEqual(monitor.operation_name, "test_model")
            self.assertEqual(monitor.operation_type, "model")
        
        # Test monitor_serializer
        with monitor_serializer("test_serializer") as monitor:
            self.assertEqual(monitor.operation_name, "test_serializer")
            self.assertEqual(monitor.operation_type, "serializer")
        
        # Test monitor_django_view with query operation type
        with monitor_django_view("test_query", operation_type="query") as monitor:
            self.assertEqual(monitor.operation_name, "test_query")
            self.assertEqual(monitor.operation_type, "query")
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_auto_assert_with_failures(self, mock_lib):
        """Test auto-assert functionality when thresholds are exceeded."""
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        
        # Create mock metrics that exceed thresholds
        mock_c_metrics = MagicMock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 2000000000
        mock_c_metrics.contents.start_time_ns = 1000000000
        mock_c_metrics.contents.memory_end_bytes = 500000000  # 500MB
        mock_c_metrics.contents.memory_start_bytes = 100000000
        mock_c_metrics.contents.query_count_end = 100
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 1
        mock_c_metrics.contents.cache_misses = 9
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = mock_c_metrics
        mock_lib.free_metrics.return_value = None
        
        monitor = EnhancedPerformanceMonitor("test_op")
        monitor.expect_response_under(10)  # Set very low threshold
        monitor.enable_auto_assert()
        
        # Should raise AssertionError due to auto-assert
        with self.assertRaises(AssertionError) as context:
            with monitor:
                pass
        
        self.assertIn("Performance thresholds exceeded", str(context.exception))
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_metrics_performance_status_boundaries(self, mock_lib):
        """Test performance status classification at boundaries."""
        test_cases = [
            (49, "excellent"),   # Just under 50ms
            (50, "excellent"),   # Exactly 50ms
            (51, "good"),        # Just over 50ms
            (99, "good"),        # Just under 100ms
            (100, "good"),       # Exactly 100ms
            (101, "acceptable"), # Just over 100ms
            (299, "acceptable"), # Just under 300ms
            (300, "acceptable"), # Exactly 300ms
            (301, "slow"),       # Just over 300ms
            (499, "slow"),       # Just under 500ms
            (500, "slow"),       # Exactly 500ms
            (501, "critical"),   # Just over 500ms
        ]
        
        for response_time, expected_status in test_cases:
            mock_c_metrics = MagicMock()
            mock_c_metrics.contents.operation_type = b"test"
            mock_c_metrics.contents.operation_name = b"test"
            mock_c_metrics.contents.end_time_ns = response_time * 1000000
            mock_c_metrics.contents.start_time_ns = 0
            mock_c_metrics.contents.memory_end_bytes = 100000000
            mock_c_metrics.contents.memory_start_bytes = 100000000
            mock_c_metrics.contents.query_count_end = 1
            mock_c_metrics.contents.query_count_start = 0
            mock_c_metrics.contents.cache_hits = 0
            mock_c_metrics.contents.cache_misses = 0
            
            metrics = EnhancedPerformanceMetrics_Python(mock_c_metrics, "test_op", None)
            self.assertEqual(metrics.performance_status, expected_status,
                           f"Failed for response_time={response_time}ms")


class TestMonitorThreadSafety(unittest.TestCase):
    """Test thread safety aspects of monitor."""
    
    @patch('django_mercury.python_bindings.monitor.C_EXTENSIONS_AVAILABLE', False)
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_concurrent_usage(self, mock_lib):
        """Test that multiple monitors can be used concurrently."""
        import threading
        import time
        
        mock_lib.start_performance_monitoring_enhanced.return_value = 12345
        
        # Create mock metrics
        mock_c_metrics = MagicMock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 1000000000
        mock_c_metrics.contents.start_time_ns = 0
        mock_c_metrics.contents.memory_end_bytes = 100000000
        mock_c_metrics.contents.memory_start_bytes = 100000000
        mock_c_metrics.contents.query_count_end = 1
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 0
        mock_c_metrics.contents.cache_misses = 0
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = mock_c_metrics
        
        results = []
        errors = []
        
        def monitor_task(name):
            try:
                with monitor_django_view(name) as mon:
                    time.sleep(0.01)  # Simulate some work
                    results.append(mon.operation_name)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=monitor_task, args=(f"view_{i}",))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        for i in range(5):
            self.assertIn(f"view_{i}", results)


if __name__ == '__main__':
    unittest.main()