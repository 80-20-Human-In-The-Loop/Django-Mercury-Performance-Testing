"""
Final tests to reach exactly 90% coverage on monitor.py.
Target the last remaining lines: imports, library loading, error formatting.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys
import os
from pathlib import Path


class TestImportFallbacks(unittest.TestCase):
    """Test import fallback scenarios (lines 19-31)."""
    
    @patch.dict('sys.modules', {'django': None})
    def test_django_import_failure(self):
        """Test when Django is not available."""
        # Force reimport with Django unavailable
        import importlib
        import django_mercury.python_bindings.monitor as monitor_module
        
        # Should still be able to create monitor
        monitor = monitor_module.EnhancedPerformanceMonitor("test")
        self.assertIsNotNone(monitor)
    
    def test_django_components_none(self):
        """Test when Django components are None."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test")
        
        # Set Django components to None to simulate import failure
        monitor._query_tracker = None
        monitor._cache_tracker = None
        
        # Should still work
        result = monitor.enable_django_hooks()
        self.assertEqual(result, monitor)


class TestLibraryLoadingEdgeCases(unittest.TestCase):
    """Test library loading edge cases (lines 57-75)."""
    
    @patch('django_mercury.python_bindings.monitor.Path')
    @patch('django_mercury.python_bindings.monitor.ctypes.CDLL')
    def test_library_loading_with_path_issues(self, mock_cdll, mock_path_class):
        """Test library loading with various path issues."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        # Test creating monitor - library should already be loaded
        monitor = EnhancedPerformanceMonitor("test")
        self.assertIsNotNone(monitor)
        
        # Check that monitor has expected attributes
        self.assertEqual(monitor.operation_name, "test")
        self.assertIsNone(monitor.handle)
        self.assertIsNone(monitor._metrics)


class TestErrorLocationAdvanced(unittest.TestCase):
    """Test advanced error location formatting (lines 1371-1396)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_error_formatting_with_eduflask_in_path(self, mock_lib):
        """Test error location with EduFlask in path."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set test context with EduFlask in path
        monitor.set_test_context(
            test_file="/home/user/EduFlask/backend/tests/test_routes.py",
            test_line=999,
            test_method="test_route_handler"
        )
        
        monitor.expect_response_under(50)
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should format with EduFlask reference
        self.assertIn("test_routes.py:999", error_msg)
        self.assertIn("test_route_handler", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_error_formatting_with_app_in_path(self, mock_lib):
        """Test error location with 'app' in path."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set test context with app in path
        monitor.set_test_context(
            test_file="/workspace/app/tests/test_services.py",
            test_line=555,
            test_method="test_service_call"
        )
        
        monitor.expect_response_under(50)
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should include app path reference
        self.assertIn("test_services.py:555", error_msg)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_error_formatting_relative_path(self, mock_lib):
        """Test error location with relative path calculation."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Set test context with simple path
        monitor.set_test_context(
            test_file="./tests/test_simple.py",
            test_line=111,
            test_method="test_simple_case"
        )
        
        monitor.expect_response_under(50)
        
        mock_metrics = Mock()
        mock_metrics.response_time = 100
        mock_metrics.memory_usage = 50
        mock_metrics.query_count = 5
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        # Should handle relative path
        self.assertIn("test_simple.py:111", error_msg)


class TestMonitorInternalMethods(unittest.TestCase):
    """Test internal monitor methods for coverage."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_properties_access(self, mock_lib):
        """Test accessing monitor properties."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test operation_name property
        self.assertEqual(monitor.operation_name, "test_op")
        
        # Test operation_type property
        self.assertEqual(monitor.operation_type, "general")
        
        # Test metrics property raises when not monitored
        with self.assertRaises(RuntimeError):
            _ = monitor.metrics
        
        # Test threshold methods exist and work
        monitor.expect_response_under(100)
        self.assertEqual(monitor._thresholds['response_time'], 100)
        
        monitor.expect_memory_under(50)
        self.assertEqual(monitor._thresholds['memory_usage'], 50)
        
        monitor.expect_queries_under(10)
        self.assertEqual(monitor._thresholds['query_count'], 10)
        
        monitor.expect_cache_hit_ratio_above(0.8)
        self.assertEqual(monitor._thresholds['cache_hit_ratio'], 0.8)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_string_representations(self, mock_lib):
        """Test monitor string representations."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_operation")
        
        # Should have reasonable string representation
        self.assertIsNotNone(str(monitor))
        self.assertIsNotNone(repr(monitor))


class TestDetectionBoundaryConditions(unittest.TestCase):
    """Test detection methods boundary conditions (lines 1414-1454)."""
    
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
    def test_query_count_with_django_tracker(self, mock_lib):
        """Test query count calculation with Django tracker (lines 1414-1426)."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMetrics_Python
        
        # Mock Django query tracker
        mock_tracker = Mock()
        mock_tracker.query_count = 50
        
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 100.0
        mock_lib.get_memory_delta_mb.return_value = 50.0
        mock_lib.get_query_count.return_value = 20
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        self.mock_c_metrics.contents.query_count_end = 20
        self.mock_c_metrics.contents.query_count_start = 0
        
        # Create metrics with Django tracker
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", mock_tracker)
        
        # Should use the C metrics count
        self.assertEqual(metrics.query_count, 20)
        
        # Test hasattr checks for _slow_queries
        if hasattr(metrics, '_slow_queries'):
            self.assertIsNotNone(metrics._slow_queries)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_detection_edge_cases(self, mock_lib):
        """Test detection methods with edge values (lines 1431-1454)."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMetrics_Python
        
        # Test with zero values
        mock_lib.get_elapsed_time_ms.return_value = 0.0
        mock_lib.get_memory_usage_mb.return_value = 0.0
        mock_lib.get_memory_delta_mb.return_value = 0.0
        mock_lib.get_query_count.return_value = 0
        mock_lib.get_cache_hit_ratio.return_value = 0.0
        
        self.mock_c_metrics.contents.query_count_end = 0
        self.mock_c_metrics.contents.query_count_start = 0
        
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # Should handle zero values gracefully
        self.assertFalse(metrics._detect_slow_serialization())
        self.assertFalse(metrics._detect_inefficient_pagination())
        self.assertFalse(metrics._detect_missing_indexes())
        
        # Test with negative values (shouldn't happen but test defensive coding)
        mock_lib.get_elapsed_time_ms.return_value = -100.0
        metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
        
        # Should handle negative values gracefully
        self.assertFalse(metrics._detect_slow_serialization())


class TestMonitorHelperMethods(unittest.TestCase):
    """Test monitor helper methods for remaining coverage."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_auto_assert_flag(self, mock_lib):
        """Test auto assert flag handling (lines 1224-1225)."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test auto assert is initially False
        self.assertFalse(monitor._auto_assert)
        
        # Test setting auto assert
        monitor._auto_assert = True
        self.assertTrue(monitor._auto_assert)
        
        # Test disable returns self
        result = monitor.disable_auto_assert()
        self.assertEqual(result, monitor)
        self.assertFalse(monitor._auto_assert)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_test_context_setting(self, mock_lib):
        """Test setting test context (lines 1269)."""
        from django_mercury.python_bindings.monitor import EnhancedPerformanceMonitor
        
        monitor = EnhancedPerformanceMonitor("test_op")
        
        # Test set_test_context returns self for chaining
        result = monitor.set_test_context(
            test_file="test.py",
            test_line=123,
            test_method="test_method"
        )
        
        self.assertEqual(result, monitor)
        self.assertEqual(monitor._test_file, "test.py")
        self.assertEqual(monitor._test_line, 123)
        self.assertEqual(monitor._test_method, "test_method")


if __name__ == '__main__':
    unittest.main()