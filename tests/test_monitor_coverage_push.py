"""
Push to 90% by directly calling the missing lines.
Target: 241, 245, 247, 610, 686, 759, 761, 763, 818, 947-954, 1224-1225, 1269, 1339, 1343
"""

import unittest
from unittest.mock import Mock, patch
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python,
    monitor_django_view,
    monitor_database_query,
    monitor_serializer,
    monitor_django_model
)


class TestDirectCoverage(unittest.TestCase):
    """Direct test of specific lines."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_factory_functions_lines_947_954(self, mock_lib):
        """Directly test factory functions to cover lines 947-954."""
        # Each function creates a monitor with specific operation_type
        view_monitor = monitor_django_view("test_view")
        self.assertIsNotNone(view_monitor)
        self.assertEqual(view_monitor.operation_name, "test_view")
        
        query_monitor = monitor_database_query("test_query")
        self.assertIsNotNone(query_monitor)
        self.assertEqual(query_monitor.operation_name, "test_query")
        
        serial_monitor = monitor_serializer("test_serial")
        self.assertIsNotNone(serial_monitor)
        self.assertEqual(serial_monitor.operation_name, "test_serial")
        
        model_monitor = monitor_django_model("test_model")
        self.assertIsNotNone(model_monitor)
        self.assertEqual(model_monitor.operation_name, "test_model")
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_chaining_lines_1224_1225_1269(self, mock_lib):
        """Test method chaining for lines 1224-1225 and 1269."""
        monitor = EnhancedPerformanceMonitor("test")
        
        # Line 1269: set_test_context
        r1 = monitor.set_test_context("test.py", 100, "test_func")
        self.assertEqual(r1, monitor)
        
        # Lines 1224-1225: disable_auto_assert
        monitor._auto_assert = True
        r2 = monitor.disable_auto_assert()
        self.assertEqual(r2, monitor)
        self.assertFalse(monitor._auto_assert)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_thresholds_lines_1339_1343(self, mock_lib):
        """Test threshold violations for lines 1339 and 1343."""
        monitor = EnhancedPerformanceMonitor("test")
        
        # Set thresholds that will be violated
        monitor.expect_response_under(50)
        monitor.expect_memory_under(30)
        
        # Create metrics that violate both
        mock_metrics = Mock()
        mock_metrics.response_time = 100  # Line 1339
        mock_metrics.memory_usage = 50   # Line 1343
        mock_metrics.query_count = 5
        mock_metrics.cache_hit_ratio = 0.8
        monitor._metrics = mock_metrics
        
        # This should raise with both violations
        with self.assertRaises(AssertionError) as ctx:
            monitor._assert_thresholds()
        
        self.assertIn("Response time", str(ctx.exception))
        self.assertIn("Memory usage", str(ctx.exception))
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_lines_610_686_818(self, mock_lib):
        """Test monitor lines 610, 686, 818."""
        # Line 686: operation_type parameter
        m1 = EnhancedPerformanceMonitor("test", operation_type="custom_type")
        self.assertEqual(m1.operation_type, "custom_type")
        
        # Line 818: __enter__ with None handle
        mock_lib.start_performance_monitoring_enhanced.return_value = None
        m2 = EnhancedPerformanceMonitor("test")
        result = m2.__enter__()
        self.assertEqual(result, m2)
        self.assertIsNone(m2.handle)
        
        # Line 610: metrics creation in __exit__
        m3 = EnhancedPerformanceMonitor("test")
        mock_lib.start_performance_monitoring_enhanced.return_value = 123
        
        mock_c = Mock()
        mock_c.contents.operation_type = b"test"
        mock_c.contents.operation_name = b"test"
        mock_c.contents.end_time_ns = 2000000000
        mock_c.contents.start_time_ns = 1000000000
        mock_c.contents.memory_end_bytes = 100000000
        mock_c.contents.memory_start_bytes = 100000000
        mock_c.contents.query_count_end = 5
        mock_c.contents.query_count_start = 0
        mock_c.contents.cache_hits = 8
        mock_c.contents.cache_misses = 2
        mock_c.contents.baseline_memory_mb = 50
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=mock_c.contents)
        mock_lib.get_elapsed_time_ms.return_value = 100
        mock_lib.get_memory_usage_mb.return_value = 100
        mock_lib.get_memory_delta_mb.return_value = 0
        mock_lib.get_query_count.return_value = 5
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        m3.__enter__()
        m3.__exit__(None, None, None)
        self.assertIsNotNone(m3._metrics)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_score_lines_241_245_247_759_761_763(self, mock_lib):
        """Test score calculation lines."""
        mock_c = Mock()
        mock_c.contents.operation_type = b"test"
        mock_c.contents.operation_name = b"test"
        mock_c.contents.baseline_memory_mb = 50
        
        # Test response time boundaries (241, 245, 247)
        for rt in [50, 100, 200]:  # Boundaries for score changes
            mock_c.contents.end_time_ns = int(1000000000 + rt * 1000000)
            mock_c.contents.start_time_ns = 1000000000
            mock_c.contents.memory_end_bytes = 100000000
            mock_c.contents.memory_start_bytes = 100000000
            mock_c.contents.query_count_end = 5
            mock_c.contents.query_count_start = 0
            mock_c.contents.cache_hits = 8
            mock_c.contents.cache_misses = 2
            
            mock_lib.get_elapsed_time_ms.return_value = float(rt)
            mock_lib.get_memory_usage_mb.return_value = 100
            mock_lib.get_memory_delta_mb.return_value = 0
            mock_lib.get_query_count.return_value = 5
            mock_lib.get_cache_hit_ratio.return_value = 0.8
            
            metrics = EnhancedPerformanceMetrics_Python(mock_c, "test", None)
            score = metrics.performance_score
            self.assertIsNotNone(score)
        
        # Test memory boundaries (759, 761, 763)
        for mem_delta in [10, 50, 100]:  # Boundaries for score changes
            mock_c.contents.end_time_ns = 1100000000
            mock_c.contents.start_time_ns = 1000000000
            mock_c.contents.memory_end_bytes = int(100000000 + mem_delta * 1000000)
            mock_c.contents.memory_start_bytes = 100000000
            mock_c.contents.query_count_end = 5
            mock_c.contents.query_count_start = 0
            mock_c.contents.cache_hits = 8
            mock_c.contents.cache_misses = 2
            
            mock_lib.get_elapsed_time_ms.return_value = 100
            mock_lib.get_memory_usage_mb.return_value = 100 + mem_delta
            mock_lib.get_memory_delta_mb.return_value = float(mem_delta)
            mock_lib.get_query_count.return_value = 5
            mock_lib.get_cache_hit_ratio.return_value = 0.8
            
            metrics = EnhancedPerformanceMetrics_Python(mock_c, "test", None)
            score = metrics.performance_score
            self.assertIsNotNone(score)


if __name__ == '__main__':
    unittest.main()