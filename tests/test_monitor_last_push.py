"""
Last push to reach 90% - targeting the final 16 lines.
Focus on: 241, 245, 247, 610, 686, 759, 761, 763, 818, 1224-1225, 1269, 1339, 1343
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django_mercury.python_bindings.monitor import (
    EnhancedPerformanceMonitor,
    EnhancedPerformanceMetrics_Python,
    monitor_django_view,
    monitor_database_query,
    monitor_serializer,
    monitor_django_model
)


class TestFactoryFunctionsComplete(unittest.TestCase):
    """Test all factory functions (lines 947-954)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_factory_functions_complete(self, mock_lib):
        """Test all factory functions."""
        # These factory functions are the easiest to cover
        m1 = monitor_django_view("view1")
        self.assertEqual(m1.operation_name, "view1")
        self.assertEqual(m1.operation_type, "view")
        
        m2 = monitor_database_query("query1")
        self.assertEqual(m2.operation_name, "query1")
        self.assertEqual(m2.operation_type, "query")
        
        m3 = monitor_serializer("serial1")
        self.assertEqual(m3.operation_name, "serial1")
        self.assertEqual(m3.operation_type, "serializer")
        
        m4 = monitor_django_model("model1")
        self.assertEqual(m4.operation_name, "model1")
        self.assertEqual(m4.operation_type, "model")


class TestMetricsScoring(unittest.TestCase):
    """Test metrics scoring calculations (lines 241, 245, 247, 759, 761, 763)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_c_metrics = Mock()
        self.mock_c_metrics.contents.operation_type = b"test"
        self.mock_c_metrics.contents.operation_name = b"test"
        self.mock_c_metrics.contents.baseline_memory_mb = 50
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_response_time_scoring_boundaries(self, mock_lib):
        """Test response time scoring at boundaries (lines 241, 245, 247)."""
        # Test exact boundary values to hit specific lines
        test_cases = [
            # (response_time, expected_score_range)
            (0.0, (90, 100)),      # Excellent
            (49.9, (90, 100)),     # Still excellent
            (50.0, (75, 90)),      # Good (line 241)
            (99.9, (75, 90)),      # Still good
            (100.0, (60, 75)),     # Fair (line 245)
            (199.9, (60, 75)),     # Still fair
            (200.0, (40, 60)),     # Slow (line 247)
            (499.9, (40, 60)),     # Still slow
            (500.0, (20, 40)),     # Very slow
            (999.9, (20, 40)),     # Still very slow
            (1000.0, (0, 20)),     # Extremely slow
        ]
        
        for response_time, expected_range in test_cases:
            with self.subTest(response_time=response_time):
                self.mock_c_metrics.contents.end_time_ns = int(2000000000 + response_time * 1000000)
                self.mock_c_metrics.contents.start_time_ns = 2000000000
                self.mock_c_metrics.contents.memory_end_bytes = 100000000
                self.mock_c_metrics.contents.memory_start_bytes = 100000000
                self.mock_c_metrics.contents.query_count_end = 5
                self.mock_c_metrics.contents.query_count_start = 0
                self.mock_c_metrics.contents.cache_hits = 8
                self.mock_c_metrics.contents.cache_misses = 2
                
                mock_lib.get_elapsed_time_ms.return_value = response_time
                mock_lib.get_memory_usage_mb.return_value = 100.0
                mock_lib.get_memory_delta_mb.return_value = 0.0
                mock_lib.get_query_count.return_value = 5
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
                score = metrics.performance_score
                
                self.assertIsNotNone(score)
                self.assertIsNotNone(score.response_time_score)
                # Check score is in expected range
                self.assertGreaterEqual(score.response_time_score, expected_range[0])
                self.assertLessEqual(score.response_time_score, expected_range[1])
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_memory_scoring_boundaries(self, mock_lib):
        """Test memory scoring at boundaries (lines 759, 761, 763)."""
        # Test memory delta scoring boundaries
        test_cases = [
            # (memory_delta_mb, expected_score_range)
            (0.0, (90, 100)),      # No memory increase
            (9.9, (90, 100)),      # Still excellent
            (10.0, (75, 90)),      # Small increase (line 759)
            (49.9, (75, 90)),      # Still small
            (50.0, (50, 75)),      # Moderate (line 761)
            (99.9, (50, 75)),      # Still moderate
            (100.0, (25, 50)),     # High (line 763)
            (199.9, (25, 50)),     # Still high
            (200.0, (0, 25)),      # Very high
        ]
        
        for memory_delta, expected_range in test_cases:
            with self.subTest(memory_delta=memory_delta):
                self.mock_c_metrics.contents.end_time_ns = 2100000000
                self.mock_c_metrics.contents.start_time_ns = 2000000000
                self.mock_c_metrics.contents.memory_end_bytes = int(100000000 + memory_delta * 1000000)
                self.mock_c_metrics.contents.memory_start_bytes = 100000000
                self.mock_c_metrics.contents.query_count_end = 5
                self.mock_c_metrics.contents.query_count_start = 0
                self.mock_c_metrics.contents.cache_hits = 8
                self.mock_c_metrics.contents.cache_misses = 2
                
                mock_lib.get_elapsed_time_ms.return_value = 100.0
                mock_lib.get_memory_usage_mb.return_value = 100.0 + memory_delta
                mock_lib.get_memory_delta_mb.return_value = memory_delta
                mock_lib.get_query_count.return_value = 5
                mock_lib.get_cache_hit_ratio.return_value = 0.8
                
                metrics = EnhancedPerformanceMetrics_Python(self.mock_c_metrics, "test", None)
                score = metrics.performance_score
                
                self.assertIsNotNone(score)
                self.assertIsNotNone(score.memory_efficiency_score)
                # Check score is in expected range
                self.assertGreaterEqual(score.memory_efficiency_score, expected_range[0])
                self.assertLessEqual(score.memory_efficiency_score, expected_range[1])


class TestMonitorMethods(unittest.TestCase):
    """Test monitor methods (lines 610, 686, 818, 1224-1225, 1269, 1339, 1343)."""
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_operation_type_line_686(self, mock_lib):
        """Test monitor operation type setting (line 686)."""
        # Test various operation types
        types = ["view", "query", "serializer", "model", "custom"]
        for op_type in types:
            monitor = EnhancedPerformanceMonitor("test", operation_type=op_type)
            self.assertEqual(monitor.operation_type, op_type)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_enter_with_none_handle_line_818(self, mock_lib):
        """Test __enter__ when handle is None (line 818)."""
        monitor = EnhancedPerformanceMonitor("test")
        
        # Make start return None
        mock_lib.start_performance_monitoring_enhanced.return_value = None
        
        result = monitor.__enter__()
        self.assertEqual(result, monitor)
        self.assertIsNone(monitor.handle)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_monitor_metrics_line_610(self, mock_lib):
        """Test metrics creation (line 610)."""
        monitor = EnhancedPerformanceMonitor("test")
        
        mock_handle = 12345
        mock_lib.start_performance_monitoring_enhanced.return_value = mock_handle
        
        mock_c_metrics = Mock()
        mock_c_metrics.contents.operation_type = b"test"
        mock_c_metrics.contents.operation_name = b"test"
        mock_c_metrics.contents.end_time_ns = 2100000000
        mock_c_metrics.contents.start_time_ns = 2000000000
        mock_c_metrics.contents.memory_end_bytes = 110000000
        mock_c_metrics.contents.memory_start_bytes = 100000000
        mock_c_metrics.contents.query_count_end = 3
        mock_c_metrics.contents.query_count_start = 0
        mock_c_metrics.contents.cache_hits = 8
        mock_c_metrics.contents.cache_misses = 2
        mock_c_metrics.contents.baseline_memory_mb = 50
        
        mock_lib.stop_performance_monitoring_enhanced.return_value = Mock(contents=mock_c_metrics.contents)
        mock_lib.get_elapsed_time_ms.return_value = 100.0
        mock_lib.get_memory_usage_mb.return_value = 110.0
        mock_lib.get_memory_delta_mb.return_value = 10.0
        mock_lib.get_query_count.return_value = 3
        mock_lib.get_cache_hit_ratio.return_value = 0.8
        
        with monitor:
            pass
        
        # Metrics should be created (line 610)
        self.assertIsNotNone(monitor._metrics)
        self.assertEqual(monitor._metrics.response_time, 100.0)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_chaining_methods_lines_1224_1225_1269(self, mock_lib):
        """Test chaining methods (lines 1224-1225, 1269)."""
        monitor = EnhancedPerformanceMonitor("test")
        
        # Test disable_auto_assert (lines 1224-1225)
        monitor._auto_assert = True
        result1 = monitor.disable_auto_assert()
        self.assertEqual(result1, monitor)
        self.assertFalse(monitor._auto_assert)
        
        # Test set_test_context (line 1269)
        result2 = monitor.set_test_context("file.py", 123, "test_method")
        self.assertEqual(result2, monitor)
        self.assertEqual(monitor._test_file, "file.py")
        self.assertEqual(monitor._test_line, 123)
        self.assertEqual(monitor._test_method, "test_method")
        
        # Chain them all
        result3 = (monitor
                  .enable_educational_guidance()
                  .expect_response_under(100)
                  .expect_memory_under(50)
                  .disable_auto_assert())
        self.assertEqual(result3, monitor)
    
    @patch('django_mercury.python_bindings.monitor.lib')
    def test_assert_thresholds_violations_lines_1339_1343(self, mock_lib):
        """Test threshold violations (lines 1339, 1343)."""
        monitor = EnhancedPerformanceMonitor("test")
        
        # Set thresholds
        monitor.expect_response_under(100)
        monitor.expect_memory_under(50)
        
        # Create metrics that violate
        mock_metrics = Mock()
        mock_metrics.response_time = 150  # Violates (line 1339)
        mock_metrics.memory_usage = 75   # Violates (line 1343)
        mock_metrics.query_count = 5
        mock_metrics.cache_hit_ratio = 0.8
        monitor._metrics = mock_metrics
        
        with self.assertRaises(AssertionError) as context:
            monitor._assert_thresholds()
        
        error_msg = str(context.exception)
        self.assertIn("Response time", error_msg)
        self.assertIn("Memory usage", error_msg)


if __name__ == '__main__':
    unittest.main()