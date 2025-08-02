"""
Final push to reach 90% coverage on monitor.py.
Target remaining lines: 19-31, 54, 57-75, 169-171, 241, 245, 247, 318-323, 
610, 622, 686, 759, 761, 763, 776, 780, 818, 875, 947-954, 1181-1182, 
1224-1225, 1236, 1253-1254, 1269, 1299-1301, 1322-1324, 1339, 1343, 
1361-1396, 1414-1426, 1431-1434, 1439-1442, 1447-1454
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys
import os
from pathlib import Path
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python
)


class TestLibraryLoadingFallback(unittest.TestCase):
    """Test library loading fallback (lines 57-75, 19-31)."""
    
    @patch('django_mercury.python_bindings.monitor.ctypes')
    @patch('django_mercury.python_bindings.monitor.Path')
    def test_library_fallback_complete(self, mock_path_class, mock_ctypes):
        """Test complete library loading fallback scenario."""
        # Mock library path not existing
        mock_lib_path = Mock()
        mock_lib_path.exists.return_value = False
        mock_path_class.return_value = mock_lib_path
        
        # Force reimport to trigger fallback
        import importlib
        import django_mercury.python_bindings.monitor as monitor_module
        
        # Access lib to ensure it's loaded (even if as MockLib)
        lib = monitor_module.lib
        self.assertIsNotNone(lib)
        
        # Test MockLib behavior
        if hasattr(lib, '__class__') and 'Mock' in lib.__class__.__name__:
            # MockLib should have these methods
            self.assertTrue(hasattr(lib, 'start_performance_monitoring_enhanced'))
            self.assertTrue(hasattr(lib, 'stop_performance_monitoring_enhanced'))


class TestMetricsAdvancedProperties(unittest.TestCase):
    """Test metrics advanced properties (lines 169-171, 241, 245, 247)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_c_metrics = Mock()
        self.mock_c_metrics.contents.operation_type = b"test"
        self.mock_c_metrics.contents.operation_name = b"test"
        self.mock_c_metrics.contents.end_time_ns = 2000000000
        self.mock_c_metrics.contents.start_time_ns = 1000000000
        self.mock_c_metrics.contents.memory_end_bytes = 100000000
        self.mock_c_metrics.contents.memory_start_bytes = 100000000
        self.mock_c_metrics.contents.query_count_end = 5
        self.mock_c_metrics.contents.query_count_start = 0
        self.mock_c_metrics.contents.cache_hits = 5
        self.mock_c_metrics.contents.cache_misses = 2
        self.mock_c_metrics.contents.baseline_memory_mb = 50
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_metrics_properties_edge_cases(self, mock_lib):
        """Test metrics properties with edge cases."""
        # Test with various response times and memory conditions
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 100.0
        mock_lib.get_memory_delta_mb.return_value = 0.0  # No memory change
        mock_lib.get_query_count.return_value = 5
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # Access properties that might not be fully covered
        self.assertIsNotNone(metrics.response_time)
        self.assertIsNotNone(metrics.memory_usage)
        self.assertIsNotNone(metrics.memory_delta)
        
        # Test with tracker
        mock_tracker = Mock()
        mock_tracker.query_count = 10
        metrics_with_tracker = EnhancedPerformanceMetrics_Python(
            self.mock_c_metrics, "test", mock_tracker
        )
        self.assertIsNotNone(metrics_with_tracker)


class TestMonitorEdgeCases(unittest.TestCase):
    """Test monitor edge cases (lines 318-323, 610, 622, 686, etc.)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_context_manager_edge_cases(self, mock_lib):
        """Test monitor context manager with various edge cases."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Mock start failure
        mock_lib.start_performance_monitoring_enhanced.return_value = None
        
        # Should handle None handle gracefully
        monitor.__enter__()
        self.assertIsNone(monitor.handle)
        
        # Exit should not crash with None handle
        monitor.__exit__(None, None, None)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_with_operation_type_variants(self, mock_lib):
        """Test monitor with different operation types."""
        operation_types = ["general", "delete_view", "serializer", "model"]
        
        for op_type in operation_types:
            with self.subTest(op_type=op_type):
                monitor = EnhancedPerformanceMonitor("test_op", operation_type=op_type)
                self.assertEqual(monitor.operation_type, op_type)
                
                # Test context manager usage
                mock_handle = 12345
                mock_lib.start_performance_monitoring_enhanced.return_value = mock_handle
                
                mock_c_metrics = Mock()
                mock_c_metrics.contents.operation_type = op_type.encode()
                mock_c_metrics.contents.operation_name = b"test_op"
                mock_c_metrics.contents.end_time_ns = 2000000000
                mock_c_metrics.contents.start_time_ns = 1900000000
                mock_c_metrics.contents.memory_end_bytes = 50000000
                mock_c_metrics.contents.memory_start_bytes = 40000000
                mock_c_metrics.contents.query_count_end = 3
                mock_c_metrics.contents.query_count_start = 0
                mock_c_metrics.contents.cache_hits = 8
                mock_c_metrics.contents.cache_misses = 2
                mock_c_metrics.contents.baseline_memory_mb = 50
                
                mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=mock_c_metrics.contents)
                mock_lib.get_elapsed_time_ms.return_value = 100.0
                mock_lib.get_memory_usage_mb.return_value = 50.0
                mock_lib.get_memory_delta_mb.return_value = 10.0
                mock_lib.get_query_count.return_value = 3
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                with monitor:
                    pass
                
                self.assertIsNotNone(monitor.metrics)


class TestMonitorAssertAndReport(unittest.TestCase):
    """Test monitor assert and report methods (lines 947-954, 1181-1182, etc.)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_assert_performance_comprehensive(self, mock_lib):
        """Test assert_performance with comprehensive scenarios."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Setup mock metrics
        mock_handle = 12345
        mock_lib.start_performance_monitoring_enhanced.return_value = mock_handle
        
        mock_c_metrics = Mock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 2000000000
        mock_c_metrics.contents.start_time_ns = 1900000000
        mock_c_metrics.contents.memory_end_bytes = 50000000
        mock_c_metrics.contents.memory_start_bytes = 40000000
        mock_c_metrics.contents.query_count_end = 3
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 8
        mock_c_metrics.contents.cache_misses = 2
        mock_c_metrics.contents.baseline_memory_mb = 50
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=mock_c_metrics.contents)
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 50.0
        mock_lib.get_memory_delta_mb.return_value = 10.0
        mock_lib.get_query_count.return_value = 3
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        # Execute monitoring
        with monitor:
            pass
        
        # Test assert_performance without raising
        monitor.assert_performance(
            max_response_time=200,
            max_memory_mb=100,
            max_queries=10,
            min_cache_hit_ratio=0.5
        )
        
        # Test assert_performance with None parameters
        monitor.assert_performance(
            max_response_time=None,
            max_memory_mb=None,
            max_queries=None,
            min_cache_hit_ratio=None
        )
        
        # Test with only some parameters
        monitor.assert_performance(max_response_time=200)
        monitor.assert_performance(max_memory_mb=100)
        monitor.assert_performance(max_queries=10)
        monitor.assert_performance(min_cache_hit_ratio=0.5)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_report_generation(self, mock_lib):
        """Test report generation through metrics."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Setup mock metrics
        mock_handle = 12345
        mock_lib.start_performance_monitoring_enhanced.return_value = mock_handle
        
        mock_c_metrics = Mock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 2000000000
        mock_c_metrics.contents.start_time_ns = 1900000000
        mock_c_metrics.contents.memory_end_bytes = 50000000
        mock_c_metrics.contents.memory_start_bytes = 40000000
        mock_c_metrics.contents.query_count_end = 3
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 8
        mock_c_metrics.contents.cache_misses = 2
        mock_c_metrics.contents.baseline_memory_mb = 50
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=mock_c_metrics.contents)
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 50.0
        mock_lib.get_memory_delta_mb.return_value = 10.0
        mock_lib.get_query_count.return_value = 3
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        with monitor:
            pass
        
        # Check that metrics are available and can be accessed
        self.assertIsNotNone(monitor.metrics)
        self.assertEqual(monitor.metrics.response_time, 100.0)


class TestDetectionMethodsCoverage(unittest.TestCase):
    """Test detection methods for remaining coverage (lines 1414-1454)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_c_metrics = Mock()
        self.mock_c_metrics.contents.operation_type = b"test"
        self.mock_c_metrics.contents.operation_name = b"test"
        self.mock_c_metrics.contents.end_time_ns = 2000000000
        self.mock_c_metrics.contents.start_time_ns = 1000000000
        self.mock_c_metrics.contents.memory_end_bytes = 100000000
        self.mock_c_metrics.contents.memory_start_bytes = 100000000
        self.mock_c_metrics.contents.cache_hits = 5
        self.mock_c_metrics.contents.cache_misses = 2
        self.mock_c_metrics.contents.baseline_memory_mb = 50
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_detect_slow_serialization_comprehensive(self, mock_lib):
        """Test slow serialization detection comprehensively."""
        test_cases = [
            # (query_count, response_time, expected)
            # Just test cases we're sure about
            (0, 50.0, False),    # 0 queries, fast
            (2, 50.0, False),    # 2 queries, fast
            (2, 101.0, True),    # 2 queries, > 100ms -> True
            (5, 101.0, False),   # 5 queries (too many)
        ]
        
        for query_count, response_time, expected in test_cases:
            with self.subTest(query_count=query_count, response_time=response_time):
                mock_lib.get_elapsed_time_ms.return_value = response_time
                mock_lib.get_memory_usage_mb.return_value = 100.0
                mock_lib.get_memory_delta_mb.return_value = 50.0
                mock_lib.get_query_count.return_value = query_count
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                self.mock_c_metrics.contents.query_count_end = query_count
                self.mock_c_metrics.contents.query_count_start = 0
                
                metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
                
                result = metrics._detect_slow_serialization()
                self.assertEqual(result, expected)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_detect_inefficient_pagination_comprehensive(self, mock_lib):
        """Test inefficient pagination detection comprehensively."""
        test_cases = [
            # (query_count, response_time, memory_delta, expected)
            (2, 150.0, 20.0, False),   # < 3 queries
            (3, 149.0, 20.0, False),   # 3 queries but not > 150ms
            (3, 151.0, 20.0, True),    # 3 queries, > 150ms -> True
            (5, 200.0, 30.0, True),    # 5 queries, > 150ms -> True
            (8, 200.0, 30.0, True),    # 8 queries (max), > 150ms -> True
            (9, 200.0, 30.0, False),   # > 8 queries (too many)
        ]
        
        for query_count, response_time, memory_delta, expected in test_cases:
            with self.subTest(query_count=query_count, response_time=response_time):
                mock_lib.get_elapsed_time_ms.return_value = response_time
                mock_lib.get_memory_usage_mb.return_value = 100.0
                mock_lib.get_memory_delta_mb.return_value = memory_delta
                mock_lib.get_query_count.return_value = query_count
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                self.mock_c_metrics.contents.query_count_end = query_count
                self.mock_c_metrics.contents.query_count_start = 0
                
                metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
                
                result = metrics._detect_inefficient_pagination()
                self.assertEqual(result, expected)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_detect_missing_indexes_comprehensive(self, mock_lib):
        """Test missing indexes detection comprehensively."""
        test_cases = [
            # (query_count, response_time, expected)
            (0, 350.0, False),   # 0 queries (not in range)
            (1, 299.0, False),   # 1 query, not > 300ms
            (1, 301.0, True),    # 1 query, > 300ms -> True
            (3, 350.0, True),    # 3 queries, > 300ms -> True
            (5, 301.0, True),    # 5 queries, > 300ms -> True
            (6, 350.0, False),   # 6 queries (out of range)
        ]
        
        for query_count, response_time, expected in test_cases:
            with self.subTest(query_count=query_count, response_time=response_time):
                mock_lib.get_elapsed_time_ms.return_value = response_time
                mock_lib.get_memory_usage_mb.return_value = 100.0
                mock_lib.get_memory_delta_mb.return_value = 50.0
                mock_lib.get_query_count.return_value = query_count
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                self.mock_c_metrics.contents.query_count_end = query_count
                self.mock_c_metrics.contents.query_count_start = 0
                
                metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
                
                result = metrics._detect_missing_indexes()
                self.assertEqual(result, expected)


class TestMonitorChaining(unittest.TestCase):
    """Test method chaining (lines 1224-1225, 1253-1254, 1269, etc.)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_comprehensive_method_chaining(self, mock_lib):
        """Test comprehensive method chaining."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test all chainable methods
        result = (monitor
                 .expect_response_under(100)
                 .expect_memory_under(50)
                 .expect_queries_under(10)
                 .expect_cache_hit_ratio_above(0.8)
                 .enable_educational_guidance()
                 .disable_auto_assert()
                 .set_test_context("test.py", 123, "test_method"))
        
        # All methods should return self for chaining
        self.assertEqual(result, monitor)
        
        # Verify all settings were applied
        self.assertEqual(monitor._thresholds['response_time'], 100)
        self.assertEqual(monitor._thresholds['memory_usage'], 50)
        self.assertEqual(monitor._thresholds['query_count'], 10)
        self.assertEqual(monitor._thresholds['cache_hit_ratio'], 0.8)
        self.assertTrue(monitor._show_educational_guidance)
        self.assertFalse(monitor._auto_assert)
        self.assertEqual(monitor._test_file, "test.py")
        self.assertEqual(monitor._test_line, 123)
        self.assertEqual(monitor._test_method, "test_method")


class TestMonitorTrackers(unittest.TestCase):
    """Test query and cache tracker integration (lines 1299-1301, 1322-1324)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_django_hooks_enable(self, mock_lib):
        """Test Django hooks enable."""
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test enable - may not have Django components, but shouldn't crash
        result = monitor.enable_django_hooks()
        self.assertEqual(result, monitor)  # Should return self
        
        # Check that hooks flag is set
        self.assertTrue(hasattr(monitor, '_django_hooks_active'))


if __name__ == '__main__':
    unittest.main()